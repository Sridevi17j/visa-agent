from typing import Annotated, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from operator import add

class State(TypedDict):
    messages: Annotated[list, add_messages]
    personal_info: Annotated[list[dict[str, Any]], add]        # Name, DOB, nationality, address, phone, email
    passport_info: Annotated[list[dict[str, Any]], add]        # Passport number, issue date, expiry, place of issue
    travel_details: Annotated[list[dict[str, Any]], add]       # Entry/exit dates, purpose, duration, previous visits, num_travelers, destination
    employment_info: Annotated[list[dict[str, Any]], add]      # Job title, employer, salary, work address
    financial_info: Annotated[list[dict[str, Any]], add]       # Bank statements, income proof, sponsor details
    accommodation_info: Annotated[list[dict[str, Any]], add]   # Hotel bookings, invitation letters, host details
    document_uploads: Annotated[list[dict[str, Any]], add]     # Photos, certificates, medical reports
    emergency_contacts: Annotated[list[dict[str, Any]], add]   # Next of kin details
    insurance_info: Annotated[list[dict[str, Any]], add]       # Travel insurance details
    visa_details: Annotated[list[dict[str, Any]], add]         # Previous visa applications, refusals, visa_type
    
    # Initial basic info collection
    initial_info: Optional[dict[str, Any]]                          # {"country": "thailand", "travelers": 2, "visa_type": "tourist_single_entry"}
    
    # Collection tracking fields
    collection_in_progress: Optional[bool]
    incomplete_session_id: Optional[str]
    missing_fields: Optional[list[str]]
    awaiting_user_response: Optional[bool]                     # True when waiting for user to provide missing info
    extraction_retry_count: Optional[int]                      # Counter to prevent infinite retry loops
