"""Aralia OpenRAG - A framework for building RAG applications with LLMs and data planets."""

# Main classes
from core.graph import AraliaAssistantGraph
from core.config import AraliaConfig
from core.state import GraphState, SearchResult, create_initial_state

# Tools
from tools.aralia import AraliaClient

# Nodes
from nodes import (
    SearchNode, PlanningNode, ExecutionNode, InterpretationNode,
    aralia_search_agent, analytics_planning_agent, analytics_execution_agent,
    filter_decision_agent, interpretation_agent
)

# Schemas
from schemas.models import (
    DatasetExtractOutput, XAxis, YAxis, FilterConfig, QueryConfig, QueryList
)

# Legacy imports for backward compatibility
from . import node
from . import aralia_tools
from . import schema
from . import prompts

__version__ = "0.3.0"

__all__ = [
    # Main classes
    "AraliaAssistantGraph",
  # Legacy
    "AraliaConfig",
    "GraphState",
    "SearchResult",
    "create_initial_state",
    
    # Tools
    "AraliaClient",
    
    # Nodes
    "SearchNode",
    "PlanningNode", 
    "ExecutionNode",
    "InterpretationNode",
    
    # Legacy node functions
    "aralia_search_agent",
    "analytics_planning_agent",
    "analytics_execution_agent", 
    "filter_decision_agent",
    "interpretation_agent",
    
    # Schemas
    "DatasetExtractOutput",
    "XAxis",
    "YAxis", 
    "FilterConfig",
    "QueryConfig",
    "QueryList",
    
    # Legacy modules
    "node",
    "aralia_tools",
    "schema",
    "prompts"
]
