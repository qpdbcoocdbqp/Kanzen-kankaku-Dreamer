import os
from enum import Enum
import json
from typing import List, Optional, Union, Annotated, Literal, Any
from pydantic import BaseModel, Field, field_validator
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. Define AG-UI Protocol (Pydantic Models) ---

class ComponentType(str, Enum):
    MARKDOWN = 'markdown'
    INFO_CARD = 'info_card'
    DATA_LIST = 'data_list'
    STEP_PROCESS = 'step_process'
    TABLE = 'table'
    STAT_GRID = 'stat_grid'
    CODE_BLOCK = 'code_block'
    ACTION_GROUP = 'action_group'

class BaseComponent(BaseModel):
    pass

class MarkdownComponent(BaseComponent):
    type: Literal[ComponentType.MARKDOWN] = ComponentType.MARKDOWN
    content: str

class InfoCardVariant(str, Enum):
    INFO = 'info'
    WARNING = 'warning'
    SUCCESS = 'success'
    DANGER = 'danger'

class InfoCardComponent(BaseComponent):
    type: Literal[ComponentType.INFO_CARD] = ComponentType.INFO_CARD
    title: str
    description: Union[str, List[Any]]
    variant: InfoCardVariant

    @field_validator('description')
    @classmethod
    def join_list(cls, v):
        if isinstance(v, list):
            return "\n".join(str(i) for i in v)
        return str(v)

class DataItem(BaseModel):
    label: str
    value: Union[str, List[Any]]

    @field_validator('value')
    @classmethod
    def join_list(cls, v):
        if isinstance(v, list):
            return "\n".join(str(i) for i in v)
        return str(v)

class DataListComponent(BaseComponent):
    type: Literal[ComponentType.DATA_LIST] = ComponentType.DATA_LIST
    title: Optional[str] = None
    items: List[DataItem]

class StepItem(BaseModel):
    title: str
    description: Union[str, List[Any]]

    @field_validator('description')
    @classmethod
    def join_list(cls, v):
        if isinstance(v, list):
            return "\n".join(str(i) for i in v)
        return str(v)

class StepProcessComponent(BaseComponent):
    type: Literal[ComponentType.STEP_PROCESS] = ComponentType.STEP_PROCESS
    title: Optional[str] = None
    steps: List[StepItem]

class TableComponent(BaseComponent):
    type: Literal[ComponentType.TABLE] = ComponentType.TABLE
    title: Optional[str] = None
    headers: List[str]
    rows: List[List[str]]

class StatItem(BaseModel):
    label: str
    value: Union[str, List[Any]]
    description: Optional[Union[str, List[Any]]] = None

    @field_validator('value', 'description')
    @classmethod
    def join_list(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            return "\n".join(str(i) for i in v)
        return str(v)

class StatGridComponent(BaseComponent):
    type: Literal[ComponentType.STAT_GRID] = ComponentType.STAT_GRID
    title: Optional[str] = None
    items: List[StatItem]

class CodeBlockComponent(BaseComponent):
    type: Literal[ComponentType.CODE_BLOCK] = ComponentType.CODE_BLOCK
    title: Optional[str] = None
    language: Optional[str] = None
    content: str

class ActionItem(BaseModel):
    label: str
    action: str
    description: Optional[Union[str, List[Any]]] = None

    @field_validator('description')
    @classmethod
    def join_list(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            return "\n".join(str(i) for i in v)
        return str(v)

class ActionGroupComponent(BaseComponent):
    type: Literal[ComponentType.ACTION_GROUP] = ComponentType.ACTION_GROUP
    title: Optional[str] = None
    items: List[ActionItem]

# Union type, using discriminator
ComponentUnion = Annotated[
    Union[
        MarkdownComponent,
        InfoCardComponent,
        DataListComponent,
        StepProcessComponent,
        TableComponent,
        StatGridComponent,
        CodeBlockComponent,
        ActionGroupComponent
    ],
    Field(discriminator='type')
]

class AGUIResponse(BaseModel):
    components: List[ComponentUnion] = Field(description="A list of UI components to render the answer.")
    suggestions: List[str] = Field(description="Suggest exactly 0, 1, or 2 follow-up questions.")

# --- 2. Google ADK Agent Logic ---

def generate_ag_ui_response(prompt: str):
    # Connect to local llama.cpp server
    client = OpenAI(
        base_url="http://localhost:9006/v1",
        api_key="***"
    )
    # listing models
    # models = client.models.list()
    # print(models)

    system_instruction = """
    You are an intelligent assistant communicating via the AG-UI protocol.

    Your Role:
    1. Analyze the user's question.
    2. Structure your answer using the strictly defined JSON schema.
    3. Language: ALWAYS reply in TRADITIONAL CHINESE (繁體中文).

    Output Schema Structure:
    The output MUST be a JSON object with two top-level fields:
    - "components": A list of UI components.
    - "suggestions": A list of strings (follow-up questions).

    Available Components (for the "components" list):

    1. [type="markdown"]
       - Use for: General text, paragraphs, summaries, and Mermaid diagrams in fenced code blocks.
       - Fields:
         - type: "markdown"
         - content: string (Markdown format)

    2. [type="info_card"]
       - Use for: Important notices, warnings, or summaries.
       - Fields:
         - type: "info_card"
         - title: string
         - description: string
         - variant: "info" | "warning" | "success" | "danger"

    3. [type="data_list"]
       - Use for: Key-value data.
       - Fields:
         - type: "data_list"
         - title: string (optional)
         - items: List of objects with "label" and "value" fields.

    4. [type="step_process"]
       - Use for: Step-by-step guides.
       - Fields:
         - type: "step_process"
         - title: string (optional)
         - steps: List of objects with "title" and "description" fields.

    5. [type="table"]
       - Use for: Tabular data representation.
       - Fields:
         - type: "table"
         - title: string (optional)
         - headers: List of strings
         - rows: List of List of strings

    6. [type="stat_grid"]
       - Use for: KPI summaries and metric snapshots.
       - Fields:
         - type: "stat_grid"
         - title: string (optional)
         - items: List of objects with "label", "value", and optional "description"

    7. [type="code_block"]
       - Use for: Raw code or source snippets such as JSON, HTML, CSS, TypeScript, or Python.
       - Fields:
         - type: "code_block"
         - title: string (optional)
         - language: string (optional)
         - content: string

    8. [type="action_group"]
       - Use for: Suggested next steps or structured follow-up options.
       - Fields:
         - type: "action_group"
         - title: string (optional)
         - items: List of objects with "label", "action", and optional "description"

    IMPORTANT RULES:
    - DO NOT use any component types other than the 8 listed above.
    - "suggestions" goes at the ROOT level, NOT inside "components".
    - Use Mermaid only inside markdown fenced code blocks with language "mermaid".
    - Do not output raw HTML as a markdown body unless it is intentionally being shown as source code.
    """

    completion = client.chat.completions.create(
        model="qwen",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        max_tokens=8192,
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    content = completion.choices[0].message.content or "{}"
    parsed = AGUIResponse.model_validate(json.loads(content))
    logger.info(parsed)
    return parsed


# --- 3. FastAPI Server Setup ---

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Allow CROSS-ORIGIN requests (Frontend usually runs on port 3000 or 5173)
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
        # Currently only message (prompt) is used, history handling can be added later
        response = generate_ag_ui_response(request.message)
        return response
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Start Server, Default port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
