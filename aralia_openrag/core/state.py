"""State management for LangGraph execution."""

from typing import TypedDict, Annotated, Optional, List, Dict, Any
from operator import add
from pydantic import BaseModel, Field
from datetime import datetime


class SearchResult(BaseModel):
    """Structured representation of a dataset search result.
    
    Attributes:
        dataset_id: Unique identifier for the dataset
        name: Human-readable name of the dataset
        description: Description of the dataset content
        site_name: Name of the data source site
        source_url: URL of the data source
        relevance_score: Calculated relevance to the query (0.0-1.0)
    """
    dataset_id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Dataset name")
    description: str = Field(..., description="Dataset description")
    site_name: str = Field(..., description="Data source site name")
    source_url: str = Field(..., description="Data source URL")
    relevance_score: Optional[float] = Field(None, description="Relevance score")


class ExecutionMetadata(BaseModel):
    """Metadata about the execution process.
    
    Attributes:
        start_time: When execution started
        current_node: Currently executing node
        completed_nodes: List of completed node names
        total_datasets_found: Number of datasets found in search
        selected_dataset_count: Number of datasets selected for analysis
    """
    start_time: datetime = Field(default_factory=datetime.now)
    current_node: Optional[str] = None
    completed_nodes: List[str] = Field(default_factory=list)
    total_datasets_found: int = 0
    selected_dataset_count: int = 0


class GraphState(TypedDict):
    """LangGraph state definition following official best practices.
    
    This state object maintains all information needed throughout the
    graph execution, including inputs, intermediate results, and outputs.
    """
    
    # Input parameters
    question: str  # User's question
    ai: Any  # LLM instance (will be set by graph)
    config: Dict[str, Any]  # Configuration dictionary
    
    # Aralia-specific inputs
    aralia_sso_url: Optional[str]
    aralia_stellar_url: Optional[str] 
    aralia_client_id: Optional[str]
    aralia_client_secret: Optional[str]
    
    # Processing state
    search_results: Annotated[List[SearchResult], add]
    selected_datasets: Optional[List[Dict[str, Any]]]
    query_plan: Optional[Dict[str, Any]]
    filter_options: Optional[List[Dict[str, Any]]]
    
    # Output
    response: Optional[Any]  # Intermediate response
    final_response: Optional[str]  # Final formatted response
    
    # System state
    errors: Annotated[List[str], add]
    execution_metadata: Dict[str, Any]
    
    # Legacy fields for backward compatibility
    at: Optional[Any]  # AraliaTools instance
    verbose: Optional[bool]
    interpretation_prompt: Optional[str]
    language: Optional[str]
    url: Optional[Any]
    google: Optional[Any]
    condition: Optional[str]


def create_initial_state(
    question: str,
    api_key: str,
    aralia_sso_url: str = "https://sso.araliadata.io",
    aralia_stellar_url: str = "https://tw-air.araliadata.io",
    aralia_client_id: Optional[str] = None,
    aralia_client_secret: Optional[str] = None,
    verbose: bool = False,
    interpretation_prompt: Optional[str] = None,
    **kwargs
) -> GraphState:
    """Create initial state for graph execution.
    
    Args:
        question: User's question
        api_key: LLM API key
        aralia_sso_url: Aralia SSO URL
        aralia_stellar_url: Aralia Stellar URL
        aralia_client_id: Aralia client ID
        aralia_client_secret: Aralia client secret
        verbose: Enable verbose logging
        interpretation_prompt: Custom interpretation prompt
        **kwargs: Additional parameters
        
    Returns:
        Initial GraphState instance
    """
    return GraphState(
        question=question,
        ai=api_key,  # Will be converted to LLM instance by graph
        config={
            "aralia_sso_url": aralia_sso_url,
            "aralia_stellar_url": aralia_stellar_url,
            "aralia_client_id": aralia_client_id,
            "aralia_client_secret": aralia_client_secret,
            "verbose": verbose,
            **kwargs
        },
        aralia_sso_url=aralia_sso_url,
        aralia_stellar_url=aralia_stellar_url,
        aralia_client_id=aralia_client_id,
        aralia_client_secret=aralia_client_secret,
        search_results=[],
        selected_datasets=None,
        query_plan=None,
        filter_options=None,
        response=None,
        final_response=None,
        errors=[],
        execution_metadata={
            "start_time": datetime.now().isoformat(),
            "current_node": None,
            "completed_nodes": [],
            "total_datasets_found": 0,
            "selected_dataset_count": 0
        },
        # Legacy fields
        at=None,
        verbose=verbose,
        interpretation_prompt=interpretation_prompt,
        language=None,
        url=None,
        google=None,
        condition=None
    )
