# Aralia OpenRAG

一個基於 LangGraph 的智能數據分析助手，可以自動搜尋和分析 Aralia Data Planet 上的資料集。

## 功能特色

- 🔍 **自動搜尋資料集**：根據問題自動找到相關的資料集
- 📊 **智能圖表規劃**：AI 自動設計最適合的圖表類型
- 🤖 **多步驟分析**：搜尋 → 規劃 → 篩選 → 執行 → 解讀
- 🌐 **多 LLM 支援**：支援 OpenAI、Google Gemini、Anthropic Claude

## 安裝

1. 安裝套件：
```bash
pip install -r requirements.txt
```

2. 設定環境變數（建立 `.env` 檔案）：
```env
# 選擇一個 LLM API Key
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Aralia Data Planet 認證
ARALIA_CLIENT_ID=your_client_id
ARALIA_CLIENT_SECRET=your_client_secret
```

## 使用方法

### 簡單使用

```python
from core.graph import AraliaAssistantGraph

# 建立助手
assistant = AraliaAssistantGraph()

# 問問題
result = assistant.invoke({
    "question": "哪個縣市的交通事故最多？",
    "ai": "your_api_key_here"
})

print(result["final_response"])
```

### 命令列執行

```bash
python main.py
```

## 工作流程

```
使用者問題
    ↓
1. 搜尋相關資料集
    ↓
2. 規劃分析策略
    ↓
3. 設計資料篩選
    ↓
4. 執行資料探索
    ↓
5. 生成分析結果
```

## 專案結構

```
AraliaOpenRAG/
├── core/           # 核心功能
├── nodes/          # 分析步驟
├── tools/          # 外部工具
├── schemas/        # 資料模型
├── utils/          # 工具函式
└── main.py         # 主程式
```

## 設定選項

主要設定都在 `core/config.py`：

- `temperature`: 控制 AI 創意程度（預設 0.0）
- `verbose`: 是否顯示詳細訊息（預設 False）
- `log_level`: 日誌等級（預設 "INFO"）

## 範例問題

- "哪個縣市的交通事故死亡率最高？"
- "台灣各縣市的空氣品質如何？"
- "最近一年的經濟成長趨勢？"

## 常見問題

**Q: 沒有回應或出錯？**  
A: 檢查 API Key 是否正確設定在 `.env` 檔案中

**Q: 找不到相關資料？**  
A: 試著調整問題的描述方式，使用更具體的關鍵字

**Q: 想要更詳細的分析過程？**  
A: 在設定中將 `verbose` 設為 `True`

## 技術架構

- **LangGraph**: 工作流程管理
- **Pydantic**: 資料驗證
- **Aralia Data Planet**: 資料來源
- **多種 LLM**: 智能分析引擎

---

簡單易用的數據分析助手，讓 AI 幫你找答案！