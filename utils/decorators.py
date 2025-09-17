"""Custom decorators for LangGraph nodes and tools."""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type
from core.state import GraphState

try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    # Fallback decorator if langsmith is not available
    def traceable(name: str = None, **kwargs):
        def decorator(func):
            return func
        return decorator


def node_with_error_handling(node_name: str, max_retries: int = 3):
    """Standard decorator for LangGraph nodes with error handling and tracing.
    
    This decorator provides:
    - Error handling with graceful fallbacks
    - Execution timing and logging
    - LangSmith tracing (if available)
    - State validation
    
    Args:
        node_name: Name of the node for logging and tracing
        max_retries: Maximum number of retry attempts
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[[GraphState], Dict[str, Any]]):
        @wraps(func)
        @traceable(name=f"aralia_node_{node_name}")
        def wrapper(state: GraphState) -> Dict[str, Any]:
            logger = logging.getLogger(f"aralia_openrag.nodes.{node_name}")
            start_time = time.time()
            
            # Update execution metadata
            if "execution_metadata" not in state:
                state["execution_metadata"] = {}
            
            state["execution_metadata"]["current_node"] = node_name
            logger.info(f"Starting node: {node_name}")
            
            # Validate state
            if not _validate_state(state, logger):
                return {
                    "errors": [f"{node_name}: Invalid state provided"]
                }
            
            # Execute with retries
            last_exception = None
            for attempt in range(max_retries):
                try:
                    result = func(state)
                    execution_time = time.time() - start_time
                    
                    # Update metadata
                    completed_nodes = state["execution_metadata"].get("completed_nodes", [])
                    completed_nodes.append(node_name)
                    
                    result.setdefault("execution_metadata", {}).update({
                        "completed_nodes": completed_nodes,
                        "current_node": None,
                        f"{node_name}_execution_time": execution_time
                    })
                    
                    logger.info(f"Completed node: {node_name} in {execution_time:.2f}s")
                    return result
                    
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed for {node_name}: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    
            # All retries failed
            execution_time = time.time() - start_time
            logger.error(f"Node {node_name} failed after {max_retries} attempts: {str(last_exception)}")
            
            return {
                "errors": [f"{node_name}: {str(last_exception)}"],
                "execution_metadata": {
                    "completed_nodes": state["execution_metadata"].get("completed_nodes", []),
                    "current_node": None,
                    f"{node_name}_execution_time": execution_time,
                    f"{node_name}_failed": True
                }
            }
            
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator for functions that may fail transiently.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(f"aralia_openrag.retry.{func.__name__}")
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {str(e)}")
                        raise
                    
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {wait_time:.1f}s")
                    time.sleep(wait_time)
                    
        return wrapper
    return decorator


def validate_node_input(required_fields: list):
    """Decorator to validate required fields in node input state.
    
    Args:
        required_fields: List of required field names in state
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[[GraphState], Dict[str, Any]]):
        @wraps(func)
        def wrapper(state: GraphState) -> Dict[str, Any]:
            logger = logging.getLogger(f"aralia_openrag.validation.{func.__name__}")
            
            missing_fields = [field for field in required_fields if field not in state or state[field] is None]
            
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.error(error_msg)
                return {"errors": [error_msg]}
                
            return func(state)
            
        return wrapper
    return decorator


def _validate_state(state: GraphState, logger: logging.Logger) -> bool:
    """Validate basic state structure.
    
    Args:
        state: The graph state to validate
        logger: Logger instance
        
    Returns:
        True if state is valid, False otherwise
    """
    required_fields = ["question", "execution_metadata"]
    
    for field in required_fields:
        if field not in state:
            logger.error(f"Missing required state field: {field}")
            return False
            
    if not isinstance(state.get("question", ""), str) or not state["question"].strip():
        logger.error("Question field must be a non-empty string")
        return False
        
    return True
