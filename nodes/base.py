"""Base node class for LangGraph nodes."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from core.state import GraphState, TokenUsage
from utils.logging import get_logger
from utils.token_counter import extract_token_usage, estimate_token_usage


class BaseNode(ABC):
    """Base class for all LangGraph nodes.
    
    This class provides common functionality and interface
    for all node implementations.
    """
    
    def __init__(self, name: str):
        """Initialize base node.
        
        Args:
            name: Name of the node for logging and identification
        """
        self.name = name
        self.logger = get_logger(f"nodes.{name}")
    
    @abstractmethod
    def execute(self, state: GraphState) -> Dict[str, Any]:
        """Execute the node logic.
        
        Args:
            state: Current graph state
            
        Returns:
            Dictionary with state updates
        """
        pass
    
    def validate_input(self, state: GraphState) -> bool:
        """Validate input state for the node.
        
        Args:
            state: Current graph state
            
        Returns:
            True if state is valid, False otherwise
        """
        # Basic validation - can be overridden by subclasses
        return "question" in state and state["question"] is not None
    
    def log_execution_start(self, state: GraphState) -> None:
        """Log the start of node execution.
        
        Args:
            state: Current graph state
        """
        self.logger.info(f"Starting {self.name} node execution")
        if state.get("verbose", False):
            self.logger.info(f"Processing question: {state['question']}")
    
    def log_execution_end(self, result: Dict[str, Any]) -> None:
        """Log the end of node execution.
        
        Args:
            result: Execution result
        """
        self.logger.info(f"Completed {self.name} node execution")
        if "errors" in result and result["errors"]:
            self.logger.warning(f"Node completed with errors: {result['errors']}")
        
        # Log token usage if available
        if "execution_metadata" in result:
            metadata = result["execution_metadata"]
            if "node_token_usage" in metadata and self.name in metadata["node_token_usage"]:
                token_usage = metadata["node_token_usage"][self.name]
                self.logger.info(
                    f"{self.name} token usage - "
                    f"Prompt: {token_usage.get('prompt_tokens', 0)}, "
                    f"Completion: {token_usage.get('completion_tokens', 0)}, "
                    f"Total: {token_usage.get('total_tokens', 0)}"
                )
    
    def track_token_usage(self, state: GraphState, llm_result: Any, prompt_text: str = "", response_text: str = "") -> Dict[str, Any]:
        """Track token usage for this node.
        
        Args:
            state: Current graph state
            llm_result: Result from LLM call
            prompt_text: Input prompt text (for estimation if needed)
            response_text: Response text (for estimation if needed)
            
        Returns:
            Updated execution metadata with token usage
        """
        # Extract or estimate token usage
        token_usage = extract_token_usage(llm_result)
        
        # If extraction failed, estimate from text
        if token_usage["total_tokens"] == 0 and prompt_text and response_text:
            token_usage = estimate_token_usage(prompt_text, response_text)
        
        # Get current metadata or create new
        metadata = state.get("execution_metadata", {})
        
        # Initialize node_token_usage if not exists
        if "node_token_usage" not in metadata:
            metadata["node_token_usage"] = {}
        
        # Store token usage for this node
        metadata["node_token_usage"][self.name] = token_usage
        
        # Update total token usage
        if "token_usage" not in metadata:
            metadata["token_usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        metadata["token_usage"]["prompt_tokens"] += token_usage["prompt_tokens"]
        metadata["token_usage"]["completion_tokens"] += token_usage["completion_tokens"]
        metadata["token_usage"]["total_tokens"] += token_usage["total_tokens"]
        
        return {"execution_metadata": metadata}

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors during node execution.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Error state update
        """
        error_msg = f"{self.name} node error: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
        
        return {
            "errors": [error_msg],
            "execution_metadata": {
                f"{self.name}_failed": True,
                f"{self.name}_error": str(error)
            }
        }
    
    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """Make the node callable for LangGraph.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates
        """
        try:
            self.log_execution_start(state)
            
            if not self.validate_input(state):
                return self.handle_error(ValueError("Invalid input state"))
            
            result = self.execute(state)
            self.log_execution_end(result)
            
            return result
            
        except Exception as e:
            return self.handle_error(e)
