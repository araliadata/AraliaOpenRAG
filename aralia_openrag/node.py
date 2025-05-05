import json
import sys
from . import prompts
from .state import BasicState
from . import schema
from bs4 import BeautifulSoup
import requests
import re
import base64

def begin_node(state: BasicState):
    pass

def google_search_agent(state: BasicState):
    try:
        content = ""
        for i, result in enumerate(state['google'].search(state['question'], num=3), 1):
            result_data = result.data
            content += f"{i}. {result_data['title']}\n"
            content += f"   {result_data['snippet']}\n\n"
            response = requests.get(result_data['link'])

            if response.status_code == 200:
                if "application/pdf" in response.headers.get("Content-Type", ""):
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                if soup.find('article'):
                    context = soup.find('article')
                elif soup.find('main'):
                    context = soup.find('main')
                elif soup.find('div', class_='content'):
                    context = soup.find('div', class_='content')
                elif soup.find('div', class_='article'):
                    context = soup.find('div', class_='article')
                elif soup.find('div', id='content'):
                    context = soup.find('div', id='content')
                if context:
                    content += f"{context.get_text(strip=True)}\n"

    except Exception as e:
        print(e)
        return None

    if state['debug']:
        print("# google_search_agent:\n")
        print(content)

    return {
        "search_results": [content]
    }


def aralia_search_agent(state: BasicState):
    # search multi dataset
    datasets = state["at"].search_tool(state["question"])

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
        raise RuntimeError("Aralia Search Agent unable to find a dataset capable of answering the query; the program has terminated.")

    if state['debug']:
        print("# aralia_search_agent:\n")
        print([item["name"] for item in datasets.values()], end="\n\n")
        print([item["name"] for item in filtered_datasets], end="\n\n")

    return {
        "response": filtered_datasets
    }


def analytics_planning_agent(state: BasicState):
    datasets = state["at"].column_metadata_tool(state['response'])

    if not datasets:
        raise RuntimeError("Analytics Planning Agent unable to find data; the program has terminated.")
    
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

            if state['debug']:
                print(response.content, end="\n\n")

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
                            y['calculation'] in prompts.format['calculation'] or (_ := None)  # 檢查計算方法
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
            if state['debug']:
                print(f"發生錯誤: {e}")
            continue
    else:
        raise RuntimeError("AI unable to generate accurate API calls.")

    if state['debug']:
        print("# analytics_planning_agent:\n")
        print(json.dumps(filtered_datasets, ensure_ascii=False, indent=2), end="\n\n")

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
        raise RuntimeError("AI unable to select precise filter values.")

    if state['debug']:
        print("# filter_decision_agent\n")
        print(json.dumps(response, ensure_ascii=False, indent=2), end="\n\n")

    return {
        "response": response
    }


def analytics_execution_agent(state: BasicState):
    if state['debug']:
        print("# analytics_execution_agent:\n")

    state["at"].explore_tool(state['response'])

    return {
        "search_results": [state['response']],

    }

def interpretation_agent(state: BasicState):
    messages = [
        {
            "role": "system",
            "content": "You are a Senior Data Analyst with expertise in analyzing statistical data. You excel at uncovering insights from the data and identifying relationships between different datasets.",
        },
        {
            "role": "user",
            "content": f"""
                Question: ***{state['question']}***
                Information: {state['search_results']}

                I have already gathered relevant information based on the user's question.
                Please analyze the information above in detail, then provide a detailed answer to the question, and give a conclusion within 300 words.
                Please pay special attention that "json_data" is the actual retrieved data; please help me analyze this data carefully.
                Please provide with English.
            """,
        },
    ]

    response = state["ai"].invoke(messages)

    if state['debug']:
        print("# interpretation_agent:\n")
        
    print(response.content)

    return {
        "final_response": response.content
    }
