"""Basic usage example for Aralia OpenRAG."""

import os
from dotenv import load_dotenv
from core.graph import AraliaAssistantGraph
from core.config import AraliaConfig

# Load environment variables
load_dotenv()

def main():
    """Demonstrate basic usage of the refactored Aralia OpenRAG."""
    
    # Method 1: Using configuration class (recommended)
    config = AraliaConfig(
        aralia_client_id=os.getenv("ARALIA_CLIENT_ID"),
        aralia_client_secret=os.getenv("ARALIA_CLIENT_SECRET"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
        verbose=True,
        log_level="INFO"
    )
    
    # Create assistant graph
    assistant = AraliaAssistantGraph(config)
    
    # Example questions
    questions = [
        '哪個縣市經呼氣檢測 0.16~0.25 mg/L或血液檢0.031%~0.05%酒駕死亡人數最多?請依照各縣市進行排序。',
        '酒駕致死道路類別以哪種類型居多?',
        '各縣市死亡車禍的熱點地圖',
        'What is the average GDP growth rate of each state in Malaysia in 2019?',
    ]
    
    for question in questions[:1]:  # Process first question only for demo
        print(f"\n{'='*80}")
        print(f"Question: {question}")
        print(f"{'='*80}")
        
        try:
            # Execute the graph
            result = assistant.invoke({
                "question": question,
                "ai": os.getenv("GEMINI_API_KEY")
            })
            
            print(f"\nResult: {result.get('final_response', 'No final response generated')}")
            
        except Exception as e:
            print(f"Error processing question: {str(e)}")




if __name__ == "__main__":
    print("=== Aralia OpenRAG Example ===")
    main()
