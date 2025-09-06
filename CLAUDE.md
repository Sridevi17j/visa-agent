# CLAUDE.md - Visa Agent Project Knowledge

## Project Flow & Architecture

### Complete Application Flow
1. **User Input** → Intent Analyzer
2. **Intent Analyzer** → Routes to: greetings, general_enquiry, or visa_application
3. **Visa Application** → Always routes to visa_application_collector
4. **Visa Application Collector** → Iteratively collects basic info (country, travelers, visa_type)
5. **Complete Collection** → Routes to detailed_collector (test node)

### State Management Rules
- **User messages**: Access via `state["messages"][0].content` for original request
- **Latest user message**: Filter out assistant responses to get actual user input
- **State persistence**: main.py maintains state between interactions via `state = agent_answer`
- **Message routing**: `awaiting_user_response: True` routes back to collector via intent_analyzer

### LangGraph Best Practices
- **Node functions**: Return clean state dictionaries for merging
- **LLM calls**: Use structured output with Pydantic models, not manual JSON parsing
- **State updates**: Simple key-value updates, let graph handle merging
- **Error handling**: Graceful failures with user-friendly messages

## Critical Implementation Details

### LLM Extraction Pattern
```python
# ✅ USE: Pydantic structured output
class VisaInfo(BaseModel):
    country: Optional[str] = Field(None, description="Country name")
    travelers: Optional[int] = Field(None, description="Number of travelers")
    visa_type: Optional[str] = Field(None, description="Visa type")

parser = PydanticOutputParser(pydantic_object=VisaInfo)
result = llm.invoke([HumanMessage(content=prompt)])
extracted_data = parser.parse(result.content)  # No JSON parsing needed

# ❌ AVOID: Manual JSON parsing (causes markdown formatting errors)
```

### Error Handling with Retry Logic
- **Max 1 retry** using `extraction_retry_count` state field
- **First failure**: "Sorry, I had an issue. Which country do you want to visit, how many travelers, and what type of visa do you need?"
- **Second failure**: "I'm having difficulty processing your request. Please try again later."
- **Reset state**: `initial_info: {}` on retry for fresh start
- **Never hardcode**: No fallback country lists (Thailand, Vietnam, etc.)

### Minimizing User Interactions
- **Batch questions**: Ask for all missing info in one message
- **Smart extraction**: "I want to apply" = 1 traveler automatically
- **Iterative flow**: Keep asking until all 3 fields complete
- **No step-by-step**: Avoid "First tell me country, then travelers..."

## Code Style Guidelines

### Icons & Formatting
- **Never use icons/emojis** in code (indicates AI-generated)
- **Clean debug output**: No 🔍, 📊, ⚡ symbols
- **Professional messages**: Plain text only

### Smart Minimal Coding
- **Think smart, code minimal**: Avoid complex logic when simple solutions exist
- **Always get latest user message**: Don't use state checks to decide message selection
- **Remove unnecessary conditions**: If logic can be simplified, do it
- **One purpose per function**: Clear, focused functionality over complex branching

### State Access Patterns
```python
# ✅ Correct - LangGraph official pattern for latest message
user_message = state["messages"][-1].content  # What triggered current node

# ✅ Also correct - Access specific message positions
first_message = state["messages"][0].content
second_to_last = state["messages"][-2].content

# ❌ Wrong - Complex filtering logic  
for msg in reversed(state["messages"]):
    if hasattr(msg, 'content') and not any(phrase in msg.content.lower()...):
        # Complex filtering not needed

# ❌ Wrong - Using state to decide message selection
if not current_initial_info:
    user_message = state["messages"][0].content  # Complex + incorrect

# ❌ Wrong patterns  
user_message = state.latest_message().content  # No such method
```

### Graph Routing Logic
- **awaiting_user_response**: Routes from intent_analyzer → visa_application_collector
- **next field**: Controls conditional edges (detailed_collector, continue_collection, etc.)
- **State updates**: Always return dictionary updates, never modify state directly

## Common Issues & Solutions

### JSON Parsing Errors
- **Problem**: LLM returns ```json {...} ``` (markdown format)
- **Solution**: Use PydanticOutputParser instead of manual json.loads()

### Infinite Loops  
- **Problem**: Node keeps routing to itself
- **Solution**: Proper state management with awaiting_user_response and counters

### Message Access Errors
- **Problem**: Analyzing assistant messages instead of user input
- **Solution**: Filter messages or use state["messages"][0] for original request

### Missing Information
- **Problem**: "I want Thailand visa" doesn't extract travelers=1
- **Solution**: Better LLM prompting with examples: "I want to apply" = 1 traveler

## State Schema Reference
```python
initial_info: {"country": str, "travelers": int, "visa_type": str}
awaiting_user_response: bool  # Routes back to collector
extraction_retry_count: int  # Prevents infinite retries
```

## LangGraph Documentation
- Always verify node patterns and state management with official docs
- Use StateGraph conditional edges properly
- Follow message handling best practices for conversation flows
- Structured output preferred over manual parsing for reliability