import os
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from openai import OpenAI

# --- 1. 定義 AG-UI Protocol (Pydantic Models) ---

class ComponentType(str, Enum):
    MARKDOWN = 'markdown'
    INFO_CARD = 'info_card'
    DATA_LIST = 'data_list'
    STEP_PROCESS = 'step_process'

class BaseComponent(BaseModel):
    type: ComponentType

class MarkdownComponent(BaseComponent):
    type: ComponentType = ComponentType.MARKDOWN
    content: str

class InfoCardVariant(str, Enum):
    INFO = 'info'
    WARNING = 'warning'
    SUCCESS = 'success'
    DANGER = 'danger'

class InfoCardComponent(BaseComponent):
    type: ComponentType = ComponentType.INFO_CARD
    title: str
    description: str
    variant: InfoCardVariant

class DataItem(BaseModel):
    label: str
    value: str

class DataListComponent(BaseComponent):
    type: ComponentType = ComponentType.DATA_LIST
    title: Optional[str] = None
    items: List[DataItem]

class StepItem(BaseModel):
    title: str
    description: str

class StepProcessComponent(BaseComponent):
    type: ComponentType = ComponentType.STEP_PROCESS
    steps: List[StepItem]

# 聯合型別，讓 Gemini 知道可以選擇哪種組件
ComponentUnion = Union[MarkdownComponent, InfoCardComponent, DataListComponent, StepProcessComponent]

class AGUIResponse(BaseModel):
    components: List[ComponentUnion] = Field(description="A list of UI components to render the answer.")
    suggestions: List[str] = Field(description="Suggest exactly 0, 1, or 2 follow-up questions.", max_length=2)

# --- 2. Google ADK Agent 邏輯 ---

def generate_ag_ui_response(prompt: str):
    # 連接到本地 llama.cpp server
    client = OpenAI(
        base_url="http://localhost:9006/v1",
        api_key="***"
    )
    # listing models
    # models = client.models.list()
    # print(models)

    system_instruction = """
    You are an intelligent assistant powered by Google Gemini, communicating via the AG-UI protocol.
    
    Your Role:
    1. Analyze the user's question.
    2. Structure your answer using specific UI components defined in the output schema.
    3. Language: ALWAYS reply in TRADITIONAL CHINESE (繁體中文) unless requested otherwise.
    
    Component Usage & Field Requirements:
    
    1. [type="markdown"]
        - Use for: General text, paragraphs, and long explanations.
        - REQUIRED Field: 'content' (Markdown string).
    
    2. [type="info_card"]
        - Use for: Highlights, warnings, summaries, or key takeaways.
        - REQUIRED Fields: 
        - 'title' (Short header)
        - 'description' (The body text. MUST NOT be empty. Do not create cards just for titles.)
        - 'variant' ('info', 'warning', 'success', 'danger')
    
    3. [type="data_list"]
        - Use for: Key-value pairs for a SINGLE item (e.g., Specs of one device).
        - REQUIRED Field: 'items' (Array of label/value objects).
    
    4. [type="table"]
        - Use for: Comparing 2+ items (e.g., A vs B) or matrix data. Use this instead of multiple Data Lists for comparisons.
        - REQUIRED Fields: 'headers' (List of column names), 'rows' (List of row data).
    
    5. [type="step_process"]
        - Use for: Explaining a procedure or timeline.
        - REQUIRED Field: 'steps' (Array of title/description objects).
    
    Crucial Rules:
    - NO DUPLICATES: Do not generate two components with the same title consecutively. 
    - NO EMPTY CARDS: Do not create an Info Card with an empty or trivial description. Combine the title and content into a single valid card.
    - COMPARISONS: Always use 'table' when comparing features (e.g. ADK vs Bluetooth).
    - Break complex answers into multiple components for better readability.
    - Always provide 1 or 2 relevant follow-up questions in the 'suggestions' field.
    """

    completion = client.chat.completions.parse(
        model="lm",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
        temperature=1.1,
        response_format=AGUIResponse,
    )

    return completion.choices[0].message.parsed

# --- 3. FastAPI Server Setup ---

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# 允許跨域請求 (Frontend usually runs on port 3000 or 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: Optional[List] = []

@app.post("/chat", response_model=AGUIResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # 這裡目前只用了 message (prompt), 未來可以加入 history 的處理
        response = generate_ag_ui_response(request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 啟動 Server, Default port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)