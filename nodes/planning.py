"""Planning node for analytics planning."""

from typing import Dict, Any
from .base import BaseNode
from core.state import GraphState
from utils.decorators import node_with_error_handling


class PlanningNode(BaseNode):
    """Node for analytics planning (future implementation)."""
    
    def __init__(self):
        """Initialize planning node."""
        super().__init__("planning")
    
    def execute(self, state: GraphState) -> Dict[str, Any]:
        """Execute analytics planning.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates
        """
        import json
        import re
        from schemas.prompts import PromptTemplates
        
        # Get metadata for each dataset
        datasets = {}
        for dataset in state['response']:
            metadata = state["at"].get_dataset_metadata(dataset['id'], dataset['sourceURL'])
            if metadata:
                datasets[dataset['id']] = {
                    **dataset,
                    **metadata
                }

        if not datasets:
            raise RuntimeError("Unable to retrieve data from the searched planet, program terminated")
        
        if state.get('verbose'):
            print("3. I am carefully analyzing which data to obtain for chart plotting, please wait a moment.\n")

        plot_chart_prompt = PromptTemplates.CHART_PLOTTING.invoke({
            "question": state["question"], 
            "datasets": datasets,
            "admin_level": PromptTemplates.get_admin_levels()
        })

        for _ in range(5):
            try:
                response = state["ai"].invoke(plot_chart_prompt)

                response_json = json.loads(list(re.finditer(
                    r'```json(.*?)```', response.content, re.DOTALL))[-1].group(1))
                
                # Process the response to match expected format
                filtered_datasets = []
                for chart in response_json["charts"]:
                    chart_data = {
                        **{k: v for k, v in datasets[chart['id']].items() if k != 'columns'},
                        "x": [
                            {
                                **datasets[chart['id']]['columns'][x['columnID']],
                                "format": x["format"]
                            }
                            for x in chart["x"]
                        ],
                        "y": [
                            {
                                **datasets[chart['id']]['columns'][y['columnID']],
                                'calculation': y['calculation']
                            }
                            for y in chart['y'] 
                        ],
                        "filter": [
                            {
                                **datasets[chart['id']]['columns'][f['columnID']],
                                "format": f["format"]
                            }
                            for f in chart["filter"]
                        ]
                    }
                    filtered_datasets.append(chart_data)
                break
            except Exception as e:
                if state.get('verbose'):
                    print(f"Error occurred: {e}")
                continue
        else:
            raise RuntimeError("AI model failed to generate accurate API calls")
        
        return {"response": filtered_datasets}


# Create node instance and legacy function
planning_node = PlanningNode()

@node_with_error_handling("analytics_planning_agent")
def analytics_planning_agent(state: GraphState) -> Dict[str, Any]:
    """Legacy function wrapper for planning node.
    
    Args:
        state: Current graph state
        
    Returns:
        State updates
    """
    return planning_node(state)
