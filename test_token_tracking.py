#!/usr/bin/env python3
"""
簡單的 token 追蹤測試腳本
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_token_tracking():
    """測試 token 追蹤功能"""
    from core.graph import AraliaAssistantGraph
    from core.config import AraliaConfig
    
    # 創建配置
    config = AraliaConfig(
        aralia_client_id=os.getenv("ARALIA_CLIENT_ID"),
        aralia_client_secret=os.getenv("ARALIA_CLIENT_SECRET"),
        verbose=False,  # 減少輸出噪音
        log_level="ERROR"  # 只顯示錯誤
    )
    
    # 創建助手圖形
    assistant_graph = AraliaAssistantGraph(config)
    
    # 簡單的測試問題
    test_question = "台北市的空氣品質如何？"
    
    try:
        print("=== Token 追蹤測試 ===")
        print(f"測試問題: {test_question}")
        print("正在處理...")
        
        # 執行查詢
        response = assistant_graph.invoke({
            "question": test_question,
            "ai": os.getenv("GEMINI_API_KEY"),
        })
        
        # 顯示 token 使用情況
        metadata = response.get('execution_metadata', {})
        total_usage = metadata.get('token_usage', {})
        
        print("\n=== Token 使用統計 ===")
        if total_usage.get('total_tokens', 0) > 0:
            print(f"總 Token 數: {total_usage['total_tokens']:,}")
            print(f"輸入 Token: {total_usage['prompt_tokens']:,}")
            print(f"輸出 Token: {total_usage['completion_tokens']:,}")
            
            # 顯示各節點的 token 使用情況
            node_usage = metadata.get('node_token_usage', {})
            if node_usage:
                print("\n=== 各節點 Token 使用情況 ===")
                for node_name, usage in node_usage.items():
                    print(f"{node_name}: {usage['total_tokens']:,} tokens")
                    print(f"  - 輸入: {usage['prompt_tokens']:,}")
                    print(f"  - 輸出: {usage['completion_tokens']:,}")
        else:
            print("未能獲取 token 使用數據")
        
        print(f"\n答案: {response.get('final_response', '無回應')[:200]}...")
        print("\n✅ Token 追蹤測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")


if __name__ == "__main__":
    test_token_tracking()
