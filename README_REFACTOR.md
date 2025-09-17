# Aralia OpenRAG - 重構版本

這是 Aralia OpenRAG 的重構版本，遵循 LangGraph 官方最佳實踐和現代 Python 開發標準。

## 🚀 主要改進

### ✨ 新特性

1. **模組化架構**: 清晰的模組分離和職責劃分
2. **配置管理**: 統一的配置管理系統
3. **錯誤處理**: 完善的錯誤處理和重試機制
4. **型別安全**: 完整的型別註解和 Pydantic 模型
5. **可觀測性**: 內建日誌記錄和 LangSmith 追蹤
6. **向後相容**: 保持與舊版本的完全相容性

### 🏗️ 架構改進

```
aralia_openrag/
├── core/                 # 核心模組
│   ├── config.py        # 配置管理
│   ├── state.py         # 狀態管理
│   └── graph.py         # 主要圖形定義
├── nodes/               # 節點實現
│   ├── base.py         # 基礎節點類
│   ├── search.py       # 搜索節點
│   └── ...
├── tools/               # 工具類
│   ├── aralia.py       # Aralia API 客戶端
│   └── data_processing.py
├── schemas/             # 資料模型
│   ├── models.py       # Pydantic 模型
│   └── prompts.py      # 提示模板
└── utils/               # 工具函數
    ├── decorators.py   # 裝飾器
    └── logging.py      # 日誌配置
```

## 📦 安裝和設置

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 環境變數設置

創建 `.env` 檔案：

```env
# Aralia API 配置
ARALIA_CLIENT_ID=your_client_id
ARALIA_CLIENT_SECRET=your_client_secret

# LLM API 金鑰
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## 🎯 使用方法

### 新介面 (推薦)

```python
from aralia_openrag import AraliaAssistantGraph, AraliaConfig

# 創建配置
config = AraliaConfig(
    aralia_client_id="your_client_id",
    aralia_client_secret="your_client_secret",
    verbose=True
)

# 創建助手
assistant = AraliaAssistantGraph(config)

# 執行查詢
result = assistant.invoke({
    "question": "你的問題",
    "ai": "your_api_key"
})

print(result["final_response"])
```

### 舊介面 (向後相容)

```python
from aralia_openrag import AssistantGraph

assistant = AssistantGraph()

response = assistant({
    "question": "你的問題",
    "ai": "your_api_key",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "verbose": True
})
```

## 🔧 配置選項

### AraliaConfig 參數

- `aralia_client_id`: Aralia 客戶端 ID
- `aralia_client_secret`: Aralia 客戶端密鑰
- `aralia_sso_url`: SSO 服務 URL (預設: https://sso.araliadata.io)
- `aralia_stellar_url`: Stellar API URL (預設: https://tw-air.araliadata.io)
- `verbose`: 詳細輸出模式 (預設: False)
- `log_level`: 日誌級別 (預設: INFO)
- `max_retries`: 最大重試次數 (預設: 3)
- `timeout_seconds`: 請求超時時間 (預設: 30)

## 🛠️ 開發者指南

### 自定義節點

```python
from aralia_openrag.nodes.base import BaseNode
from aralia_openrag.utils.decorators import node_with_error_handling

class CustomNode(BaseNode):
    def __init__(self):
        super().__init__("custom")
    
    def execute(self, state):
        # 實現自定義邏輯
        return {"response": "custom_result"}

# 創建節點函數
@node_with_error_handling("custom_node")
def custom_node(state):
    return CustomNode()(state)
```

### 自定義工具

```python
from aralia_openrag.tools.aralia import AraliaClient

class CustomTool:
    def __init__(self, client: AraliaClient):
        self.client = client
    
    def process_data(self, data):
        # 實現自定義處理邏輯
        return processed_data
```

## 📊 監控和日誌

### 日誌配置

```python
from aralia_openrag.utils.logging import setup_logging

setup_logging(
    level="DEBUG",
    include_timestamp=True
)
```

### LangSmith 追蹤

重構版本自動支援 LangSmith 追蹤（如果已安裝）：

```bash
pip install langsmith
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_langsmith_key
```

## 🧪 測試

```bash
# 運行基本測試
python main.py

# 運行範例
python examples/basic_usage.py
```

## 🔄 遷移指南

### 從舊版本遷移

1. **簡單遷移**: 舊代碼無需修改，直接使用
2. **推薦遷移**: 使用新的 `AraliaAssistantGraph` 和 `AraliaConfig`
3. **完整遷移**: 使用新的節點類和工具類

### 遷移檢查清單

- [ ] 更新 import 語句
- [ ] 使用 `AraliaConfig` 管理配置
- [ ] 採用新的錯誤處理模式
- [ ] 啟用日誌記錄
- [ ] 設置 LangSmith 追蹤（可選）

## 🤝 貢獻

1. Fork 專案
2. 創建功能分支
3. 提交更改
4. 推送到分支
5. 創建 Pull Request

## 📄 授權

MIT License

## 📚 更多資源

- [LangGraph 官方文檔](https://langchain-ai.github.io/langgraph/)
- [LangChain 最佳實踐](https://python.langchain.com/docs/guides/)
- [Pydantic 文檔](https://docs.pydantic.dev/)

---

**注意**: 這個重構版本完全向後相容，現有的代碼可以無縫運行。建議逐步遷移到新介面以獲得更好的功能和性能。
