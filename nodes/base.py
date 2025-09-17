"""Base node class for LangGraph nodes."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from core.state import GraphState
from utils.logging import get_logger


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
