from aralia_openrag.graph import AssistantGraph
import os
from dotenv import load_dotenv

load_dotenv()

assistant_graph = AssistantGraph()

question = [
    '哪個縣市經呼氣檢測 0.16~0.25 mg/L或血液檢0.031%~0.05%酒駕死亡人數最多?請依照各縣市進行排序。',
    # '酒駕致死道路類別以哪種類型居多?',
    # '經呼氣檢測超過 0.80 mg/L或血液檢測超過 0.16%酒駕事故者平均年齡?',
    # '請提供4月份台北區監理所「酒駕新制再犯」課程日期。',
    # '請列出六都中經呼氣檢測 0.56~0.80 mg/L或血液檢測 0.111%~0.16%酒駕死亡及受傷人數。',
    # '各縣市死亡車禍的熱點地圖',
    # 'What is the average GDP growth rate of each state in Malaysia in 2019?',
    # 'What is the average GDP growth rate of each state in Malaysia in 2019 compared to their Gini coefficient?',
    # '請提供4月份新北市監理所「酒駕新制再犯」課程日期。',
    # '如果酒駕車禍撞死人，會面臨哪些酒駕致死刑責?'
]

for item in question:
    response = assistant_graph(
        {
            "question": question[0],
            "ai": os.getenv("GEMINI_API_KEY"), ## Advanced option: select and set different LLMs here
            "sso_url": "https://sso.araliadata.io",
            "stellar_url":"https://tw-air.araliadata.io",
            "client_id": os.getenv("ARALIA_CLIENT_ID"),
            "client_secret": os.getenv("ARALIA_CLIENT_SECRET"),
            "verbose": True,
            # "interpretation_prompt":"replace this text with custom prompt" ## Advanced option: uncomment to set a custom prompt for the interpretation agent
        }
    )