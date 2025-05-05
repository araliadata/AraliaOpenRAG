from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from . import aralia_tools
from . import node
from operator import add
from typing import Any, Dict, TypedDict, Annotated
from .state import BasicState
# import google_custom_search


class AssistantGraph:
    def __init__(self):
        builder = StateGraph(BasicState)

        builder.add_node("begin_node", node.begin_node)
        # builder.add_node("google_search_agent", node.google_search_agent)
        builder.add_node("aralia_search_agent", node.aralia_search_agent)
        builder.add_node("analytics_planning_agent",
                         node.analytics_planning_agent)
        builder.add_node("filter_decision_agent",
                         node.filter_decision_agent)
        builder.add_node("analytics_execution_agent",
                         node.analytics_execution_agent)
        builder.add_node("interpretation_agent", node.interpretation_agent)

        builder.set_entry_point("begin_node")

        builder.add_edge("begin_node", "aralia_search_agent")
        # builder.add_edge("begin_node", "google_search_agent")
        builder.add_edge("aralia_search_agent", "analytics_planning_agent")
        builder.add_edge("analytics_planning_agent", "filter_decision_agent")
        builder.add_edge("filter_decision_agent",
                         "analytics_execution_agent")
        builder.add_edge("analytics_execution_agent","interpretation_agent")
        builder.add_edge("interpretation_agent", END)

        #   builder.add_edge("init", "explain_check")
        #   builder.add_conditional_edges(
        #       "explain_check",
        #       lambda state: state['condition'],
        #       {
        #           "Yes": "explain",
        #           "No": "advise_single_graph",
        #           "NoQuestion": "no_question"
        #       }
        #   )
        #   builder.add_edge("no_question", END)
        #   builder.add_edge("explain", END)
        #   builder.add_edge("advise_single_graph", "advise_adjust")

        self.graph = builder.compile()

        # print(graph.get_graph().draw_mermaid()) #set['debug']

    def __call__(self, request):
        # 根據API key的前綴來判定使用哪家LLM
        api_key = request['ai']
        if api_key.startswith('sk-ant-'):
            # Anthropic Claude
            request['ai'] = ChatAnthropic(
                api_key=api_key, model="claude-3-5-sonnet-20240620", temperature=0)
        elif api_key.startswith('AIza'):
            # Google Gemini
            request['ai'] = ChatGoogleGenerativeAI(
                api_key=api_key, model="gemini-2.0-flash", temperature=0)
        else:
            # 預設使用OpenAI
            request['ai'] = ChatOpenAI(
                api_key=api_key, model="gpt-4o", temperature=0)
            
        request['at'] = aralia_tools.AraliaTools(
            request['username'], request['password'], request['url'])

        return self.graph.invoke(request)
