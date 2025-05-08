import json
import sys
from . import prompts
from .state import BasicState
from . import schema
from bs4 import BeautifulSoup
import requests
import re
import base64
import textwrap

def aralia_search_agent(state: BasicState):
    # search multi dataset
    datasets = state["at"].search_tool(state["question"])

    if state['verbose']:
        print(
            textwrap.dedent(
                f'''
                    I received your question: "{state['question']}"

                    To answer your question, I performed the following steps:
                    1. Searched for available datasets, initially finding {len(datasets)} datasets.
                '''
            ), 
            end=""
        )

    extract_prompt = prompts.simple_datasets_extract_template.invoke(
        {
            "question": state["question"],
            "datasets": datasets
        }
    )

    structured_llm = state["ai"].with_structured_output(
        schema.datasets_extract_output
    )

    for _ in range(5):
        try:
            # extract datasets
            response = structured_llm.invoke(extract_prompt).dict()

            filtered_datasets = [
                datasets[item] for item in response['dataset_key']
            ]
            break
        except:
            continue
    else:
        raise RuntimeError("Unable to find datasets that could answer the question, program terminated")

    if state['verbose']:
        print(
            textwrap.dedent(
                f'''
                    2. Filtered out the following datasets most relevant to the question {[item["name"] for item in filtered_datasets]}。
                '''
            )
        )

    return {
        "response": filtered_datasets
    }


def analytics_planning_agent(state: BasicState):
    datasets = state["at"].column_metadata_tool(state['response'])

    if not datasets:
        raise RuntimeError("Unable to retrieve data from the searched planet, program terminated")
    

    if state['verbose']:
        print("3. I am carefully analyzing which data to obtain for chart plotting, please wait a moment.\n")

    plot_chart_prompt = prompts.chart_ploting_template.invoke(  # extract column
        {
            "question": state["question"], 
            "datasets": datasets,
            "admin_level": prompts.admin_level
        }
    )

    for _ in range(5):
        try:
            response = state["ai"].invoke(plot_chart_prompt)

            response_json = json.loads(list(re.finditer(
                r'```json(.*?)```', response.content, re.DOTALL))[-1].group(1))
            
            filtered_datasets = [
                {
                    **{k: v for k, v in datasets[chart['id']].items() if k != 'columns'},
                    "x": [
                        {
                            **datasets[chart['id']]['columns'][x['columnID']],
                            "format": x["format"]
                            if x["type"] not in ["date", "datetime", "space"]
                            else x["format"] if (
                                (x["type"] in ["date", "datetime"] and (x["format"] in prompts.format["date"] or (_ := None))) or
                                (x["type"] == "space" and (x["format"] in prompts.format["space"] or (_ := None)))
                            )
                            else x["format"]
                        }
                        for x in chart["x"]
                    ],
                    "y": [
                        {
                            **datasets[chart['id']]['columns'][y['columnID']],
                            'calculation': y['calculation']
                        }
                        for y in chart['y'] 
                        if y['type'] in ["integer", "float"] and (
                            y['calculation'] in prompts.format['calculation'] or (_ := None)  # Check calculation method
                        )
                    ],
                    "filter": [
                        {
                            **datasets[chart['id']]['columns'][f['columnID']],
                            "format": f["format"]
                            if f["type"] not in ["date", "datetime", "space"]
                            else f["format"] if (
                                (f["type"] in ["date", "datetime"] and (f["format"] in prompts.format["date"] or (_ := None))) or
                                (f["type"] == "space" and (f["format"] in prompts.format["space"] or (_ := None)))
                            )
                            else f["format"]
                        }
                        for f in chart["filter"]
                    ]
                }
                for chart in response_json["charts"]
            ]
            break
        except Exception as e:
            if state['verbose']:
                print(f"Error occurred: {e}")
            continue
    else:
        raise RuntimeError("AI model failed to generate accurate API calls")
    
    return {
        "response": filtered_datasets
    }


def filter_decision_agent(state: BasicState):
    state["at"].filter_option_tool(state['response'])

    prompt = prompts.query_generate_template.invoke(
        {
            "question": state['question'],
            "response": state['response'],
        }
    )

    structured_llm = state["ai"].with_structured_output(
        schema.query_list
    )

    for _ in range(5):
        try:
            response = structured_llm.invoke(prompt).dict()['querys']
            for chart in response:
                for x in chart["x"]:
                    if x["type"] not in {"date", "datetime", "space"}:
                        x.pop("format")
                for filter in chart["filter"]:
                    if filter["type"] not in {"date", "datetime", "space"}:
                        filter.pop("format")
                chart["filter"] = [chart["filter"]]
            break
        except:
            continue
    else:
        raise RuntimeError("AI model cannot select accurate filter value")

    return {
        "response": response
    }


def analytics_execution_agent(state: BasicState):
    if state['verbose']:
        print("4. I have selected the appropriate data and obtained suitable charts, now proceeding with detailed analysis.\n")

    state["at"].explore_tool(state['response'])

    return {
        "search_results": [state['response']],

    }

def interpretation_agent(state: BasicState):
    if state.get("interpretation_prompt"):
        interpretation_prompt = state["interpretation_prompt"]
    else:
        interpretation_prompt ='''
            I have already gathered relevant information based on the user's question.
            Please analyze the information above in detail, then provide a detailed answer to the question, and give a conclusion within 300 words.
            Please help me analyze this data carefully.
            Please provide with English.
        '''


    messages = f"""
        Question: ***{state['question']}***
        Information: {state['search_results']}

        Please pay special attention that "json_data" is the actual retrieved data.

        {interpretation_prompt}
    """

    response = state["ai"].invoke(messages)

    if state['verbose']:
        print("5. ", end="")
        
    print(response.content)

    return {
        "final_response": response.content
    }
