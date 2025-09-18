"""
Aralia OpenRAG - Main execution script

This script demonstrates both the new refactored interface and maintains
backward compatibility with the legacy interface.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main execution function using the new interface."""
    from core.graph import AraliaAssistantGraph
    from core.config import AraliaConfig
    
    # Create configuration
    config = AraliaConfig(
        aralia_client_id=os.getenv("ARALIA_CLIENT_ID"),
        aralia_client_secret=os.getenv("ARALIA_CLIENT_SECRET"),
        verbose=True,
        log_level="WARNING"  # 減少日誌噪音
    )
    
    # Create assistant graph
    assistant_graph = AraliaAssistantGraph(config)
    
    # Example questions
    questions = [
        '哪個縣市經呼氣檢測 0.16~0.25 mg/L或血液檢0.031%~0.05%酒駕死亡人數最多?請依照各縣市進行排序。',
        '酒駕致死道路類別以哪種類型居多?',
        '經呼氣檢測超過 0.80 mg/L或血液檢測超過 0.16%酒駕事故者平均年齡?',
        '請提供4月份台北區監理所「酒駕新制再犯」課程日期。',
        '請列出六都中經呼氣檢測 0.56~0.80 mg/L或血液檢測 0.111%~0.16%酒駕死亡及受傷人數。',
        'What is the average GDP growth rate of each state in Malaysia in 2019?',
        'What is the average GDP growth rate of each state in Malaysia in 2019 compared to their Gini coefficient?',
        '請提供4月份新北市監理所「酒駕新制再犯」課程日期。',
        '如果酒駕車禍撞死人，會面臨哪些酒駕致死刑責?'
    ]
    
    # Process the first question
    question = questions[0]
    
    try:
        print("=== Using New Aralia OpenRAG Interface ===\n")
        
        response = assistant_graph.invoke({
            "question": question,
            "ai": os.getenv("GEMINI_API_KEY"),  # API key for LLM
            # Optional: override config settings
            # "sso_url": "https://sso.araliadata.io",
            # "stellar_url": "https://tw-air.araliadata.io",
            # "interpretation_prompt": "Custom prompt for interpretation"
        })
        
        # Display token usage
        metadata = response.get('execution_metadata', {})
        total_usage = metadata.get('token_usage', {})
        
        if total_usage.get('total_tokens', 0) > 0:
            print("=== Token Usage Summary ===")
            print(f"Total Tokens: {total_usage['total_tokens']:,}")
            print(f"Prompt Tokens: {total_usage['prompt_tokens']:,}")
            print(f"Completion Tokens: {total_usage['completion_tokens']:,}")
            
            # Show per-node breakdown
            node_usage = metadata.get('node_token_usage', {})
            if node_usage:
                print("\n=== Per-Node Token Usage ===")
                for node_name, usage in node_usage.items():
                    print(f"{node_name}: {usage['total_tokens']:,} tokens "
                          f"(prompt: {usage['prompt_tokens']:,}, "
                          f"completion: {usage['completion_tokens']:,})")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()