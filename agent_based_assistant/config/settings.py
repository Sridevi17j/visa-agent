# Configuration settings for agent-based visa assistant
# Purpose: LLM setup, environment variables, and other configurations

import os
import time
from typing import Any, Optional
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration with Error Handling and Streaming

class LLMConfig:
    """Enhanced LLM configuration with retry logic, error handling, and streaming support"""
    
    def __init__(self):
        self.model_name = os.getenv("LLM_MODEL", "anthropic:claude-sonnet-4-20250514")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "8192"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("LLM_RETRY_DELAY", "1.0"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        self.streaming_enabled = os.getenv("STREAMING_ENABLED", "true").lower() == "true"
        
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self) -> BaseChatModel:
        """Initialize LLM with error handling and validation"""
        try:
            required_env_vars = ["ANTHROPIC_API_KEY"]
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {missing_vars}")
            
            llm = init_chat_model(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            
            # Test the model
            test_response = llm.invoke([{"role": "user", "content": "Hello"}])
            if not test_response or not test_response.content:
                raise RuntimeError("LLM initialization test failed")
            
            # LLM initialized successfully - no print for clean terminal
            return llm
            
        except Exception as e:
            print(f"LLM initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize LLM: {e}")
    
    def invoke_with_retry(self, messages: list, **kwargs) -> Any:
        """Invoke LLM with retry logic and error handling"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.llm.invoke(messages, timeout=self.timeout, **kwargs)
                
                if not response or not response.content:
                    raise RuntimeError("Empty response from LLM")
                
                return response
                
            except Exception as e:
                last_error = e
                
                if self._is_non_retryable_error(e):
                    print(f"Non-retryable LLM error: {e}")
                    raise e
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"LLM attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"LLM failed after {self.max_retries + 1} attempts: {e}")
        
        raise RuntimeError(f"LLM invocation failed after all retries: {last_error}")
    
    def stream_with_retry(self, messages: list, **kwargs):
        """Stream LLM response with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                for chunk in self.llm.stream(messages, timeout=self.timeout, **kwargs):
                    yield chunk
                return
                
            except Exception as e:
                last_error = e
                
                if self._is_non_retryable_error(e):
                    print(f"Non-retryable streaming error: {e}")
                    raise e
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"Streaming attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Streaming failed after {self.max_retries + 1} attempts: {e}")
        
        raise RuntimeError(f"LLM streaming failed after all retries: {last_error}")
    
    def _is_non_retryable_error(self, error: Exception) -> bool:
        """Determine if error should not be retried"""
        error_str = str(error).lower()
        non_retryable_patterns = [
            "api key",
            "authentication",
            "authorization", 
            "invalid request",
            "malformed"
        ]
        return any(pattern in error_str for pattern in non_retryable_patterns)


# Application Settings

class AppConfig:
    """Application-wide configuration settings"""
    
    def __init__(self):
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Session management
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "3600"))
        self.max_sessions = int(os.getenv("MAX_SESSIONS", "1000"))
        
        # Tool settings
        self.max_tool_calls_per_turn = int(os.getenv("MAX_TOOL_CALLS", "10"))
        self.tool_timeout = int(os.getenv("TOOL_TIMEOUT", "30"))
        
        # Error handling
        self.max_error_history = int(os.getenv("MAX_ERROR_HISTORY", "50"))
        self.error_log_level = os.getenv("ERROR_LOG_LEVEL", "WARNING")
        
        # Performance
        self.enable_caching = os.getenv("ENABLE_CACHING", "true").lower() == "true"
        self.cache_ttl = int(os.getenv("CACHE_TTL", "300"))
        
        # Streaming settings
        self.streaming_chunk_size = int(os.getenv("STREAMING_CHUNK_SIZE", "1024"))
        self.streaming_timeout = int(os.getenv("STREAMING_TIMEOUT", "60"))


# Global Instances

llm_config = LLMConfig()
app_config = AppConfig()

# Export LLM instance for backward compatibility
llm = llm_config.llm

# Export enhanced LLM functions
def invoke_llm_safe(messages: list, **kwargs) -> Any:
    """Safe LLM invocation with retry logic"""
    return llm_config.invoke_with_retry(messages, **kwargs)

def stream_llm_safe(messages: list, **kwargs):
    """Safe LLM streaming with retry logic"""
    return llm_config.stream_with_retry(messages, **kwargs)


# Environment Validation

def validate_environment() -> tuple[bool, list[str]]:
    """Validate all required environment variables and configurations"""
    issues = []
    
    required_vars = ["ANTHROPIC_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Missing required environment variable: {var}")
    
    try:
        int(os.getenv("PORT", "8000"))
    except ValueError:
        issues.append("PORT must be a valid integer")
    
    try:
        float(os.getenv("LLM_TEMPERATURE", "0"))
    except ValueError:
        issues.append("LLM_TEMPERATURE must be a valid float")
    
    try:
        llm_config.llm.invoke([{"role": "user", "content": "test"}])
    except Exception as e:
        issues.append(f"LLM configuration test failed: {e}")
    
    return len(issues) == 0, issues