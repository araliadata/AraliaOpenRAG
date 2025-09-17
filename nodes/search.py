"""Search node implementation for dataset discovery."""

import textwrap
from typing import Dict, Any
from .base import BaseNode
from core.state import GraphState
from tools.aralia import AraliaClient
from schemas.models import DatasetExtractOutput
from schemas.prompts import PromptTemplates
from utils.decorators import node_with_error_handling


class SearchNode(BaseNode):
    """Node for searching and filtering relevant datasets."""
    
    def __init__(self):
        """Initialize search node."""
        super().__init__("search")
    
    def validate_input(self, state: GraphState) -> bool:
        """Validate input for search node.
        
        Args:
            state: Current graph state
            
        Returns:
            True if valid, False otherwise
        """
        if not super().validate_input(state):
            return False
        
        # Check for Aralia tools or credentials
        if not state.get("at") and not (
            state.get("aralia_client_id") and 
            state.get("aralia_client_secret")
        ):
            self.logger.error("Missing Aralia credentials or tools")
            return False
            
        return True
    
    def execute(self, state: GraphState) -> Dict[str, Any]:
        """Execute dataset search and filtering.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates with filtered datasets
        """
        question = state["question"]
        
        # Get or create Aralia client
        aralia_client = state.get("at")
        if not aralia_client:
            aralia_client = AraliaClient(
                sso_url=state.get("aralia_sso_url"),
                stellar_url=state.get("aralia_stellar_url"),
                client_id=state.get("aralia_client_id"),
                client_secret=state.get("aralia_client_secret")
            )
        
        # Search for datasets
        self.logger.info(f"Searching datasets for question: {question}")
        raw_datasets = aralia_client.search_datasets(question)
        datasets = {item['id']: item for item in raw_datasets}
        
        if state.get("verbose", False):
            print(textwrap.dedent(f"""
                I received your question: "{question}"
                
                To answer your question, I performed the following steps:
                1. Searched for available datasets, initially finding {len(raw_datasets)} datasets.
            """), end="")
        
        # datasets is already indexed
        
        # Use LLM to filter relevant datasets
        extract_prompt = PromptTemplates.DATASET_EXTRACT.invoke({
            "question": question,
            "datasets": datasets
        })
        
        # Get structured LLM response
        ai_model = state["ai"]
        structured_llm = ai_model.with_structured_output(DatasetExtractOutput)
        
        # Retry logic for LLM extraction
        for attempt in range(5):
            try:
                response = structured_llm.invoke(extract_prompt).dict()
                filtered_datasets = [
                    datasets[item] for item in response['dataset_key']
                    if item in datasets
                ]
                break
            except Exception as e:
                self.logger.warning(f"LLM extraction attempt {attempt + 1} failed: {str(e)}")
                if attempt == 4:
                    raise RuntimeError("Unable to extract relevant datasets after 5 attempts")
                continue
        
        if state.get("verbose", False):
            dataset_names = [item["name"] for item in filtered_datasets]
            print(textwrap.dedent(f"""
                2. Filtered out the following datasets most relevant to the question: {dataset_names}.
            """))
        
        # Update execution metadata
        execution_metadata = state.get("execution_metadata", {})
        execution_metadata.update({
            "total_datasets_found": len(datasets),
            "selected_dataset_count": len(filtered_datasets)
        })
        
        return {
            "response": filtered_datasets,
            "search_results": filtered_datasets,
            "execution_metadata": execution_metadata,
            "at": aralia_client  # Preserve client for future use
        }


