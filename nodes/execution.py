"""Execution nodes for data processing."""

from typing import Dict, Any
from .base import BaseNode
from core.state import GraphState
from utils.decorators import node_with_error_handling


class ExecutionNode(BaseNode):
    """Node for executing data queries."""
    
    def __init__(self):
        """Initialize execution node."""
        super().__init__("execution")
    
    def execute(self, state: GraphState) -> Dict[str, Any]:
        """Execute data queries.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates
        """
        if state.get('verbose'):
            print("4. I have selected the appropriate data and obtained suitable charts, now proceeding with detailed analysis.\n")

        # Execute exploration for each chart
        from tools.data_processing import DataProcessor
        
        processor = DataProcessor()
        
        for chart in state['response']:
            try:
                # Execute exploration
                results = state["at"].execute_exploration(chart)
                
                # Process results
                x_cols = [x_axis.get('displayName', f"x{i}") for i, x_axis in enumerate(chart.get('x', []))]
                y_cols = [y_axis.get('displayName', f"y{i}") for i, y_axis in enumerate(chart.get('y', []))]
                
                chart_data = processor.prepare_chart_data(results, {
                    'name': chart.get('name', 'chart'),
                    'x': chart.get('x', []),
                    'y': chart.get('y', [])
                })
                
                # Add processed data to chart
                chart.update(chart_data)
                
            except Exception as e:
                self.logger.error(f"Failed to explore chart {chart.get('name', 'unknown')}: {str(e)}")
                chart['json_data'] = None

        return {
            "search_results": [state['response']],
        }


class FilterDecisionNode(BaseNode):
    """Node for filter decision making."""
    
    def __init__(self):
        """Initialize filter decision node."""
        super().__init__("filter_decision")
    
    def execute(self, state: GraphState) -> Dict[str, Any]:
        """Execute filter decision logic.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates
        """
        from schemas.prompts import PromptTemplates
        from schemas.models import QueryList
        
        # Get filter options for each dataset
        for dataset in state['response']:
            if 'filter' in dataset:
                state["at"].get_filter_options(dataset['id'], dataset['sourceURL'], dataset['filter'])

        prompt = PromptTemplates.QUERY_GENERATION.invoke({
            "question": state['question'],
            "response": state['response'],
        })

        structured_llm = state["ai"].with_structured_output(QueryList)

        for _ in range(5):
            try:
                response = structured_llm.invoke(prompt).dict()['querys']
                for chart in response:
                    for x in chart["x"]:
                        if x["type"] not in {"date", "datetime", "space"}:
                            x.pop("format", None)
                    for filter_item in chart["filter"]:
                        if filter_item["type"] not in {"date", "datetime", "space"}:
                            filter_item.pop("format", None)
                    chart["filter"] = [chart["filter"]]
                break
            except Exception as e:
                self.logger.warning(f"Filter decision attempt failed: {str(e)}")
                continue
        else:
            raise RuntimeError("AI model cannot select accurate filter value")

        return {"response": response}


# Create node instances and legacy functions
execution_node = ExecutionNode()
filter_decision_node = FilterDecisionNode()

@node_with_error_handling("analytics_execution_agent")
def analytics_execution_agent(state: GraphState) -> Dict[str, Any]:
    """Legacy function wrapper for execution node.
    
    Args:
        state: Current graph state
        
    Returns:
        State updates
    """
    return execution_node(state)

@node_with_error_handling("filter_decision_agent")
def filter_decision_agent(state: GraphState) -> Dict[str, Any]:
    """Legacy function wrapper for filter decision node.
    
    Args:
        state: Current graph state
        
    Returns:
        State updates
    """
    return filter_decision_node(state)
