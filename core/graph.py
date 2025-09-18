"""Main LangGraph implementation for Aralia OpenRAG."""

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from typing import Dict, Any, Optional

from .state import GraphState, create_initial_state
from .config import AraliaConfig
from utils.logging import setup_logging, get_logger



class AraliaAssistantGraph:
    """Main LangGraph implementation following official best practices.
    
    This class orchestrates the multi-node workflow for data analysis
    using Aralia Data Planet and LLMs.
    """
    
    def __init__(self, config: Optional[AraliaConfig] = None):
        """Initialize the assistant graph.
        
        Args:
            config: Configuration instance. If None, will create default config.
        """
        self.config = config or AraliaConfig()
        self.logger = get_logger("assistant_graph")
        
        # Setup logging
        setup_logging(
            level=self.config.log_level,
            include_timestamp=True
        )
        
        # Create node instances
        self._create_nodes()
        
        # Build the execution graph
        self.graph = self._build_graph()
        self.logger.info("Aralia Assistant Graph initialized")
    
    def _create_nodes(self):
        """Create and initialize node instances."""
        # Import node classes here to avoid circular imports
        from nodes.search import SearchNode
        from nodes.planning import PlanningNode  
        from nodes.execution import ExecutionNode, FilterDecisionNode
        from nodes.interpretation import InterpretationNode
        
        # Create node instances
        self.search_node = SearchNode()
        self.planning_node = PlanningNode()
        self.filter_decision_node = FilterDecisionNode()
        self.execution_node = ExecutionNode()
        self.interpretation_node = InterpretationNode()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph execution graph.
        
        Returns:
            Compiled StateGraph instance
        """
        builder = StateGraph(GraphState)
        
        # Add nodes using instance attributes
        builder.add_node("aralia_search", self.search_node)
        builder.add_node("analytics_planning", self.planning_node)
        builder.add_node("filter_decision", self.filter_decision_node)
        builder.add_node("analytics_execution", self.execution_node)
        builder.add_node("interpretation", self.interpretation_node)
        
        # Set entry point
        builder.set_entry_point("aralia_search")
        
        # Define edges
        builder.add_edge("aralia_search", "analytics_planning")
        builder.add_edge("analytics_planning", "filter_decision")
        builder.add_edge("filter_decision", "analytics_execution")
        builder.add_edge("analytics_execution", "interpretation")
        builder.add_edge("interpretation", END)
        
        # Compile graph
        return builder.compile()
    
    def _create_llm_instance(self, api_key: str) -> Any:
        """Create appropriate LLM instance based on API key.
        
        Args:
            api_key: API key for the LLM service
            
        Returns:
            LLM instance
        """
        llm_config = self.config.get_llm_config(api_key)
        
        if llm_config["provider"] == "anthropic":
            return ChatAnthropic(
                api_key=api_key,
                model=llm_config["model"],
                temperature=self.config.temperature
            )
        elif llm_config["provider"] == "google":
            return ChatGoogleGenerativeAI(
                api_key=api_key,
                model=llm_config["model"], 
                temperature=self.config.temperature
            )
        else:  # OpenAI
            return ChatOpenAI(
                api_key=api_key,
                model=llm_config["model"],
                temperature=self.config.temperature
            )
    
    def _prepare_state(self, request: Dict[str, Any]) -> GraphState:
        """Prepare initial state from request.
        
        Args:
            request: Input request dictionary
            
        Returns:
            Initial GraphState
        """
        # Extract API key and create LLM instance
        api_key = request.get("ai")
        if not api_key:
            raise ValueError("Missing 'ai' field with API key in request")
        
        # Create LLM instance
        llm_instance = self._create_llm_instance(api_key)
        
        # Import AraliaClient here to avoid circular imports
        from tools.aralia import AraliaClient
        
        # Create Aralia client
        aralia_client = AraliaClient(
            sso_url=request.get("sso_url", self.config.aralia_sso_url),
            stellar_url=request.get("stellar_url", self.config.aralia_stellar_url),
            client_id=request.get("client_id", self.config.aralia_client_id),
            client_secret=request.get("client_secret", self.config.aralia_client_secret)
        )
        
        # Create initial state
        state = create_initial_state(
            question=request["question"],
            api_key=api_key,
            aralia_sso_url=request.get("sso_url", self.config.aralia_sso_url),
            aralia_stellar_url=request.get("stellar_url", self.config.aralia_stellar_url),
            aralia_client_id=request.get("client_id", self.config.aralia_client_id),
            aralia_client_secret=request.get("client_secret", self.config.aralia_client_secret),
            verbose=request.get("verbose", self.config.verbose),
            interpretation_prompt=request.get("interpretation_prompt"),
            **{k: v for k, v in request.items() if k not in [
                "question", "ai", "sso_url", "stellar_url", 
                "client_id", "client_secret", "verbose", "interpretation_prompt"
            ]}
        )
        
        # Set LLM instance and Aralia client
        state["ai"] = llm_instance
        state["at"] = aralia_client
        
        return state
    
    def invoke(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the graph with the given request.
        
        Args:
            request: Input request containing question and configuration
            
        Returns:
            Graph execution result
        """
        try:
            # Validate required fields
            if "question" not in request:
                raise ValueError("Missing required field: 'question'")
            
            # Prepare initial state
            initial_state = self._prepare_state(request)
            
            self.logger.info(f"Starting graph execution for question: {request['question']}")
            
            # Execute graph
            result = self.graph.invoke(initial_state)
            
            self.logger.info("Graph execution completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Graph execution failed: {str(e)}", exc_info=True)
            raise
    
    def __call__(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Make the graph callable (legacy interface).
        
        Args:
            request: Input request
            
        Returns:
            Graph execution result
        """
        return self.invoke(request)


