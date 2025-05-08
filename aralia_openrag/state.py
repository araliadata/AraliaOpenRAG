from operator import add
from typing import Any, Dict, TypedDict, Annotated


class BasicState(TypedDict):
    condition: str
    response: Any
    question: str
    language: str
    search_results: Annotated[list, add]
    ai: Any
    at: Any  # aralia tools
    google: Any
    final_response: Any
    url: Any
    verbose: Any
    interpretation_prompt: str


# class AssistantState(BasicState):
#     dataset_metadata: Annotated[list, add]
#     graphs_metadata: Dict
