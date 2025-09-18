"""Token counting utilities for tracking LLM usage."""

import tiktoken
from typing import Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult


def count_tokens_for_text(text: str, model: str = "gpt-4") -> int:
    """Count tokens for a text string.
    
    Args:
        text: Text to count tokens for
        model: Model name for tokenizer (default: gpt-4)
        
    Returns:
        Number of tokens
    """
    try:
        # Try to get encoding for the specific model
        if "gpt-4" in model.lower():
            encoding = tiktoken.encoding_for_model("gpt-4")
        elif "gpt-3.5" in model.lower():
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        elif "gemini" in model.lower() or "google" in model.lower():
            # Gemini uses similar tokenization to GPT-4
            encoding = tiktoken.encoding_for_model("gpt-4")
        elif "claude" in model.lower() or "anthropic" in model.lower():
            # Claude uses similar tokenization to GPT-4
            encoding = tiktoken.encoding_for_model("gpt-4")
        else:
            # Default to GPT-4 encoding
            encoding = tiktoken.encoding_for_model("gpt-4")
            
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimation (1 token ≈ 4 characters)
        return len(text) // 4


def extract_token_usage(llm_result: Any) -> Dict[str, int]:
    """Extract token usage from LLM result.
    
    Args:
        llm_result: Result from LLM call
        
    Returns:
        Dictionary with prompt_tokens, completion_tokens, total_tokens
    """
    token_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }
    
    try:
        # Try to extract from LLMResult
        if hasattr(llm_result, 'llm_output') and llm_result.llm_output:
            usage = llm_result.llm_output.get('token_usage', {})
            if usage:
                token_usage["prompt_tokens"] = usage.get('prompt_tokens', 0)
                token_usage["completion_tokens"] = usage.get('completion_tokens', 0)
                token_usage["total_tokens"] = usage.get('total_tokens', 0)
                return token_usage
        
        # Try to extract from response metadata
        if hasattr(llm_result, 'response_metadata'):
            usage = llm_result.response_metadata.get('token_usage', {})
            if usage:
                token_usage["prompt_tokens"] = usage.get('prompt_tokens', 0)
                token_usage["completion_tokens"] = usage.get('completion_tokens', 0)
                token_usage["total_tokens"] = usage.get('total_tokens', 0)
                return token_usage
                
        # Try to extract from usage_metadata (newer LangChain versions)
        if hasattr(llm_result, 'usage_metadata'):
            usage = llm_result.usage_metadata
            if usage:
                token_usage["prompt_tokens"] = getattr(usage, 'input_tokens', 0)
                token_usage["completion_tokens"] = getattr(usage, 'output_tokens', 0)
                token_usage["total_tokens"] = getattr(usage, 'total_tokens', 0)
                return token_usage
                
    except Exception as e:
        print(f"Warning: Could not extract token usage: {e}")
    
    return token_usage


def estimate_token_usage(prompt: str, response: str, model: str = "gpt-4") -> Dict[str, int]:
    """Estimate token usage when exact counts are not available.
    
    Args:
        prompt: Input prompt text
        response: Response text
        model: Model name for tokenizer
        
    Returns:
        Dictionary with estimated token counts
    """
    prompt_tokens = count_tokens_for_text(prompt, model)
    completion_tokens = count_tokens_for_text(response, model)
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens
    }


def format_token_usage(token_usage: Dict[str, int]) -> str:
    """Format token usage for display.
    
    Args:
        token_usage: Token usage dictionary
        
    Returns:
        Formatted string
    """
    return (
        f"Tokens - Prompt: {token_usage['prompt_tokens']:,}, "
        f"Completion: {token_usage['completion_tokens']:,}, "
        f"Total: {token_usage['total_tokens']:,}"
    )
