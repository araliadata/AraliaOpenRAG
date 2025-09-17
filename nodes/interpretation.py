"""Interpretation node for generating final responses."""

from typing import Dict, Any
from .base import BaseNode
from core.state import GraphState
from schemas.prompts import PromptTemplates
from utils.decorators import node_with_error_handling


class InterpretationNode(BaseNode):
    """Node for interpreting results and generating final responses."""
    
    def __init__(self):
        """Initialize interpretation node."""
        super().__init__("interpretation")
    
    def validate_input(self, state: GraphState) -> bool:
        """Validate input for interpretation node.
        
        Args:
            state: Current graph state
            
        Returns:
            True if valid, False otherwise
        """
        if not super().validate_input(state):
            return False
        
        if not state.get("search_results") and not state.get("response"):
            self.logger.error("No search results or response data available for interpretation")
            return False
            
        return True
    
    def execute(self, state: GraphState) -> Dict[str, Any]:
        """Execute interpretation and response generation.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates with final response
        """
        question = state["question"]
        search_results = state.get("search_results", state.get("response", []))
        
        # Use custom interpretation prompt if provided
        interpretation_prompt = state.get("interpretation_prompt")
        if interpretation_prompt:
            prompt_text = f"""
                Question: ***{question}***
                Information: {search_results}
                
                Please pay special attention that "json_data" is the actual retrieved data.
                
                {interpretation_prompt}
            """
        else:
            # Use default interpretation prompt
            prompt_text = f"""
                Question: ***{question}***
                Information: {search_results}

                Please pay special attention that "json_data" is the actual retrieved data.

                You are an expert data analyst. Your task is to answer the user's question based on the provided information.

                Your most important rule is this:
                **The language of your response MUST EXACTLY MATCH the language used in the 'Question'. There are NO exceptions to this rule.**

                Additionally, follow these content rules:
                1.  Your response must contain a detailed analysis of the charts.
                2.  Provide a clear, direct answer to the question.
                3.  Include a final conclusion that is under 300 words.
            """
        
        # Get AI response
        ai_model = state["ai"]
        response = ai_model.invoke(prompt_text)
        
        # Log and print response if verbose
        if state.get("verbose", False):
            print("5. ", end="")
        
        print(response.content)
        
        return {
            "final_response": response.content
        }


