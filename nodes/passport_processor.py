from state import State
from config.settings import llm
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field
from typing import Optional
import os
from pathlib import Path

class PassportInfo(BaseModel):
    passport_number: Optional[str] = Field(None, description="Passport number")
    full_name: Optional[str] = Field(None, description="Full name as shown on passport")
    nationality: Optional[str] = Field(None, description="Nationality")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (DD/MM/YYYY)")
    place_of_birth: Optional[str] = Field(None, description="Place of birth")
    issue_date: Optional[str] = Field(None, description="Passport issue date (DD/MM/YYYY)")
    expiry_date: Optional[str] = Field(None, description="Passport expiry date (DD/MM/YYYY)")
    issuing_authority: Optional[str] = Field(None, description="Issuing authority")

def extract_passport_info(file_path: str, traveler_index: int) -> dict:
    """
    Extract passport information from image file using OCR.
    For now, returns simulated data structure until OCR library is added.
    """
    
    # TODO: Implement actual OCR processing
    # This would typically involve:
    # 1. Load image with PIL/OpenCV
    # 2. Preprocess image (enhance contrast, resize, etc.)
    # 3. Use OCR library (pytesseract, easyocr, etc.) to extract text
    # 4. Use LLM with structured output to parse extracted text
    
    # For now, return simulated structure
    return {
        "traveler_index": traveler_index,
        "file_path": file_path,
        "passport_number": f"PENDING_OCR_{traveler_index}",
        "full_name": f"PENDING_OCR_{traveler_index}",
        "nationality": "PENDING_OCR",
        "date_of_birth": "PENDING_OCR",
        "issue_date": "PENDING_OCR", 
        "expiry_date": "PENDING_OCR",
        "issuing_authority": "PENDING_OCR",
        "ocr_status": "pending_implementation"
    }

def passport_processor(state: State) -> dict:
    """
    Process passport files and extract information using OCR.
    Expects user to provide file paths to passport images.
    """
    
    # Get the latest user message for file paths
    user_message = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, 'type') and msg.type == 'human':
            user_message = msg.content
            break
    
    # Check if user provided file paths
    if not user_message or not any(keyword in user_message.lower() for keyword in ['file', 'path', 'upload', 'passport']):
        return {
            "messages": [AIMessage(content="Please provide the file path(s) to your passport images. Example: C:\\Documents\\passport1.jpg")]
        }
    
    # Extract file paths from user message
    # This is a simple implementation - could be enhanced with regex
    potential_paths = []
    words = user_message.split()
    for word in words:
        if ('.' in word and any(ext in word.lower() for ext in ['.jpg', '.jpeg', '.png', '.pdf'])) or ('\\' in word or '/' in word):
            potential_paths.append(word.strip('",\''))
    
    if not potential_paths:
        return {
            "messages": [AIMessage(content="I couldn't find any file paths in your message. Please provide the full path to your passport file(s).")]
        }
    
    processed_passports = []
    travelers_count = state.get("initial_info", {}).get("number_of_travelers", 1)
    
    for i, file_path in enumerate(potential_paths[:travelers_count]):  # Limit to expected number
        # Verify file exists
        if not os.path.exists(file_path):
            return {
                "messages": [AIMessage(content=f"File not found: {file_path}. Please check the path and try again.")]
            }
        
        # Process passport image with OCR
        try:
            extracted_info = extract_passport_info(file_path, i + 1)
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Failed to process passport file {file_path}: {str(e)}")]
            }
        
        processed_passports.append(extracted_info)
    
    # Prepare summary message
    if len(processed_passports) == travelers_count:
        summary = f"Successfully processed {len(processed_passports)} passport(s):\n\n"
        for passport in processed_passports:
            summary += f"**Traveler {passport['traveler_index']}:**\n"
            summary += f"- Name: {passport['full_name']}\n"
            summary += f"- Passport: {passport['passport_number']}\n"
            summary += f"- Nationality: {passport['nationality']}\n"
            summary += f"- Expiry: {passport['expiry_date']}\n\n"
        
        summary += "Now please provide your hotel booking details or accommodation information."
        
        return {
            "messages": [AIMessage(content=summary)],
            "passport_info": processed_passports,
            "next": "accommodation_processor"  # Next step
        }
    else:
        missing_count = travelers_count - len(processed_passports)
        return {
            "messages": [AIMessage(content=f"I've processed {len(processed_passports)} passport(s). Please provide {missing_count} more passport file path(s).")]
        }