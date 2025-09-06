from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model("anthropic:claude-sonnet-4-20250514", max_tokens=8192, temperature=0)
