from state import State
from config.settings import llm
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

class DocumentInfo(BaseModel):
    document_type: str = Field(description="Type of document: passport, hotel_booking, bank_statement, etc.")
    content: dict = Field(description="Extracted information from the document")
# Initialize OpenAI client  
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def encode_image(image_path: str) -> str:
    """Encode image file to base64 string for OpenAI API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def docs_parser(state: State) -> dict:
    """
    Generic document parser that can handle any document type.
    Extracts information and classifies document type automatically.
    """
    
    # Get the latest user message for file paths
    user_message = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, 'type') and msg.type == 'human':
            user_message = msg.content
            break
    
    # Extract file paths from user message
    potential_paths = []
    non_file_slashes = []  # Track slash-containing words that aren't files
    words = user_message.split()
    
    for word in words:
        # Only consider as file path if it has proper file extensions
        if '.' in word and any(ext in word.lower() for ext in ['.jpg', '.jpeg', '.png', '.pdf']):
            potential_paths.append(word.strip('",\''))
        # Track slash-containing words without file extensions (likely dates or other data)
        elif ('\\' in word or '/' in word) and word.strip('",\''):
            non_file_slashes.append(word.strip('",\''))
    
    # Handle case where user provided slashes but no actual file paths
    if not potential_paths and non_file_slashes:
        return {
            "messages": [AIMessage(content=f"I see you mentioned '{', '.join(non_file_slashes)}' but these don't appear to be file paths. Please provide the full file paths to your documents with extensions like .jpg, .png, or .pdf (e.g., 'C:\\Documents\\passport.jpg').")]
        }
    
    if not potential_paths:
        return {
            "messages": [AIMessage(content="Please provide your passport and hotel bookings if any.")]
        }
    
    processed_documents = []
    
    for file_path in potential_paths:
        # Verify file exists
        if not os.path.exists(file_path):
            return {
                "messages": [AIMessage(content=f"File not found: {file_path}. Please check the path and try again.")]
            }
        
        try:
            # Extract and classify document
            doc_info = extract_document_info(file_path)
            processed_documents.append(doc_info)
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Failed to process document {file_path}: {str(e)}")]
            }
    
    # Route extracted information to appropriate state fields
    state_updates = route_documents_to_state(processed_documents)
    
    # Create summary message
    summary = f"Successfully processed {len(processed_documents)} document(s):\n\n"
    for doc in processed_documents:
        summary += f"- {doc['document_type'].title()}: {doc.get('summary', 'Processed')}\n"
    
    # Add state updates to return data
    result = {
        "messages": [AIMessage(content=summary)]
    }
    result.update(state_updates)
    
    return result

def extract_document_info(file_path: str) -> dict:
    """
    Extract information from any document type using OpenAI's multimodal capabilities.
    """
    try:
        # Encode image for OpenAI API
        base64_image = encode_image(file_path)
        
        # System prompt for document analysis and classification
        system_prompt = """You are an expert OCR and document classification assistant. Analyze the provided document image and:

1. **CLASSIFY DOCUMENT TYPE**: Determine if this is a:
   - passport
   - hotel_booking 
   - bank_statement
   - invoice
   - receipt
   - id_card
   - other (specify type)

2. **EXTRACT KEY INFORMATION**: Based on document type:

For PASSPORT:
- full_name
- passport_number
- nationality
- date_of_birth (DD/MM/YYYY format)
- issue_date (DD/MM/YYYY format)
- expiry_date (DD/MM/YYYY format)
- place_of_birth
- issuing_authority

For HOTEL_BOOKING:
- hotel_name
- guest_names
- check_in_date (DD/MM/YYYY format)
- check_out_date (DD/MM/YYYY format)
- booking_reference
- total_cost
- room_type

For OTHER documents:
- Extract relevant key information based on document type

3. **RESPONSE FORMAT**: Return JSON with:
```json
{
  "document_type": "passport|hotel_booking|bank_statement|other",
  "confidence": "high|medium|low",
  "content": {
    "key_field_1": "extracted_value",
    "key_field_2": "extracted_value"
  },
  "summary": "Brief description of what was found"
}
```

Be accurate and only extract information that is clearly visible."""

        # Make API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this document and extract information according to the instructions."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        # Parse response with debug logging
        import json
        content = response.choices[0].message.content
        
        if content is None:
            raise Exception(f"OpenAI returned empty response. Full response: {response}")
            
        result = json.loads(content)
        
        # Add metadata
        result["file_path"] = file_path
        result["ocr_status"] = "success"
        
        return result
        
    except Exception as e:
        return {
            "document_type": "unknown",
            "file_path": file_path,
            "content": {},
            "summary": f"Failed to process document: {str(e)}",
            "ocr_status": "failed",
            "error": str(e)
        }

def route_documents_to_state(documents: List[dict]) -> dict:
    """
    Route extracted document information to appropriate state fields.
    """
    state_updates = {}
    
    for doc in documents:
        doc_type = doc["document_type"]
        
        if doc_type == "passport":
            if "passport_info" not in state_updates:
                state_updates["passport_info"] = []
            state_updates["passport_info"].append(doc["content"])
            
        elif doc_type == "hotel_booking":
            if "accommodation_info" not in state_updates:
                state_updates["accommodation_info"] = []
            state_updates["accommodation_info"].append(doc["content"])
            
        elif doc_type == "bank_statement":
            if "financial_info" not in state_updates:
                state_updates["financial_info"] = []
            state_updates["financial_info"].append(doc["content"])
            
        else:
            # Store unknown documents in a general field
            if "document_uploads" not in state_updates:
                state_updates["document_uploads"] = []
            state_updates["document_uploads"].append(doc)
    
    return state_updates