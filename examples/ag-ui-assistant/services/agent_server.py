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
    SURFACE = 'surface'

class SurfaceKind(str, Enum):
    HTML = 'html'
    SVG = 'svg'
    MARKDOWN = 'markdown'
    IFRAME = 'iframe'

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

class SurfaceComponent(BaseComponent):
    type: Literal[ComponentType.SURFACE] = ComponentType.SURFACE
    kind: SurfaceKind
    html: Optional[str] = None
    css: Optional[str] = None
    svg: Optional[str] = None
    markdown: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

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
        ActionGroupComponent,
        SurfaceComponent
    ],
    Field(discriminator='type')
]

class TextContent(BaseModel):
    answer: str = Field(description="The main response text in Traditional Chinese.")
    suggestions: List[str] = Field(description="Suggest exactly 0, 1, or 2 follow-up questions.")

class ComponentPlan(BaseModel):
    components_to_use: List[ComponentType] = Field(description="List of component types that fit the content.")
    component_descriptions: dict = Field(description="Brief description of what content goes in each component.")

class AGUIResponse(BaseModel):
    components: List[ComponentUnion] = Field(description="A list of UI components to render the answer.")
    suggestions: List[str] = Field(description="Suggest exactly 0, 1, or 2 follow-up questions.")

# --- 2. Google ADK Agent Logic ---

def generate_ag_ui_text_content(prompt: str) -> TextContent:
    client = OpenAI(
        base_url="http://localhost:9006/v1",
        api_key="***"
    )

    system_instruction = """
    You are a helpful assistant that provides clear, concise answers in TRADITIONAL CHINESE (繁體中文).

    Your task:
    1. Answer the user's question thoroughly and clearly
    2. Suggest 0-2 concise follow-up questions based on the answer

    Output a JSON with two fields:
    - "answer": The main response text
    - "suggestions": Array of 0-2 follow-up questions
    """

    tool_schema = {
        "type": "function",
        "function": {
            "name": "emit_text_response",
            "description": "Return text content with suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The main response text"
                    },
                    "suggestions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Follow-up suggestions"
                    }
                },
                "required": ["answer", "suggestions"],
                "additionalProperties": False
            }
        }
    }

    completion = client.chat.completions.create(
        model="qwen",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
        temperature=0.7,
        tools=[tool_schema],
        tool_choice={
            "type": "function",
            "function": {"name": "emit_text_response"}
        },
    )

    tool_calls = completion.choices[0].message.tool_calls or []
    if not tool_calls:
        raise ValueError("Model did not return a tool call for emit_text_response")

    arguments = tool_calls[0].function.arguments or "{}"
    parsed = TextContent.model_validate(json.loads(arguments))
    logger.info(f"Stage 1 (Text Content): {parsed}")
    return parsed


def suggest_components(text_content: TextContent) -> ComponentPlan:
    client = OpenAI(
        base_url="http://localhost:9006/v1",
        api_key="***"
    )

    component_options = ", ".join([c.value for c in ComponentType])

    system_instruction = f"""
    You are an expert at selecting appropriate UI components to display content.

    Your task:
    1. Analyze the provided text content
    2. Select which component types would best display this content
    3. Decide what content goes in each component

    Available component types: {component_options}

    Component guidance:
    - markdown: For general text, explanations, summaries
    - info_card: For important callouts, warnings, successes
    - data_list: For key-value pairs or structured data
    - step_process: For guides or multi-step instructions
    - table: For tabular/comparison data
    - stat_grid: For KPIs, metrics, statistics
    - code_block: For code snippets or technical content
    - action_group: For suggested actions or next steps

    Output JSON with:
    - "components_to_use": Array of component type strings to use
    - "component_descriptions": Object mapping component types to descriptions of their content
    """

    tool_schema = {
        "type": "function",
        "function": {
            "name": "suggest_ui_components",
            "description": "Suggest which UI components fit the content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "components_to_use": {
                        "type": "array",
                        "items": {"type": "string", "enum": [c.value for c in ComponentType]},
                        "description": "Component types to use"
                    },
                    "component_descriptions": {
                        "type": "object",
                        "description": "Map of component type to description",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["components_to_use", "component_descriptions"],
                "additionalProperties": False
            }
        }
    }

    completion = client.chat.completions.create(
        model="qwen",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Answer text:\n{text_content.answer}"},
        ],
        max_tokens=2048,
        temperature=0.5,
        tools=[tool_schema],
        tool_choice={
            "type": "function",
            "function": {"name": "suggest_ui_components"}
        },
    )

    tool_calls = completion.choices[0].message.tool_calls or []
    if not tool_calls:
        raise ValueError("Model did not return a tool call for suggest_ui_components")

    arguments = tool_calls[0].function.arguments or "{}"
    parsed = ComponentPlan.model_validate(json.loads(arguments))
    logger.info(f"Stage 2 (Component Plan): {parsed}")
    return parsed


def construct_components(text_content: TextContent, component_plan: ComponentPlan) -> AGUIResponse:
    client = OpenAI(
        base_url="http://localhost:9006/v1",
        api_key="***"
    )

    components_str = "\n".join([f"- {c}" for c in component_plan.components_to_use])
    descriptions_str = "\n".join([f"- {k}: {v}" for k, v in component_plan.component_descriptions.items()])

    system_instruction = f"""
    You are an expert at transforming text content into structured AG-UI components.

    Your task:
    1. Transform the provided text content into the specified component types
    2. Fill each component with relevant data from the text
    3. Return a complete, valid AG-UI response

    Components to create:
    {components_str}

    Component content guidance:
    {descriptions_str}

    Component type definitions:
    1. [type="markdown"] - Use for general text content
       Fields: type, content (markdown format)

    2. [type="info_card"] - Use for important callouts/warnings/successes
       Fields: type, title, description, variant (info|warning|success|danger)

    3. [type="data_list"] - Use for key-value data
       Fields: type, title (optional), items (list of label/value objects)

    4. [type="step_process"] - Use for step-by-step guides
       Fields: type, title (optional), steps (list of title/description objects)

    5. [type="table"] - Use for tabular data
       Fields: type, title (optional), headers, rows

    6. [type="stat_grid"] - Use for metrics/KPIs
       Fields: type, title (optional), items (list of label/value/description objects)

    7. [type="code_block"] - Use for code snippets
       Fields: type, title (optional), language, content

    8. [type="action_group"] - Use for suggested actions
       Fields: type, title (optional), items (list of label/action/description objects)

    IMPORTANT:
    - Return a valid JSON with "components" array and "suggestions" array at root level
    - suggestions come from the original text_content, not generated here
    - Use Traditional Chinese (繁體中文) for all content
    - Do not mix component types - use exactly what was planned
    """

    tool_schema = {
        "type": "function",
        "function": {
            "name": "emit_agui_response",
            "description": "Return a structured AG-UI response with components.",
            "parameters": {
                "type": "object",
                "properties": {
                    "components": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Structured AG-UI components"
                    },
                    "suggestions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Follow-up suggestions"
                    }
                },
                "required": ["components", "suggestions"],
                "additionalProperties": False
            }
        }
    }

    completion = client.chat.completions.create(
        model="qwen",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Text content:\n{text_content.answer}\n\nSuggestions:\n{json.dumps(text_content.suggestions)}"},
        ],
        max_tokens=8192,
        temperature=0.5,
        tools=[tool_schema],
        tool_choice={
            "type": "function",
            "function": {"name": "emit_agui_response"}
        },
    )

    tool_calls = completion.choices[0].message.tool_calls or []
    if not tool_calls:
        raise ValueError("Model did not return a tool call for emit_agui_response")

    arguments = tool_calls[0].function.arguments or "{}"
    parsed = AGUIResponse.model_validate(json.loads(arguments))
    logger.info(f"Stage 3 (Final Response): {parsed}")
    return parsed


def generate_ag_ui_response(prompt: str) -> AGUIResponse:
    logger.info(f"=== Starting three-stage response generation ===")
    logger.info(f"User prompt: {prompt}")

    # Stage 1: Generate text content and suggestions
    logger.info("Stage 1: Generating text content...")
    text_content = generate_ag_ui_text_content(prompt)

    # Stage 2: Suggest appropriate components
    logger.info("Stage 2: Suggesting component types...")
    component_plan = suggest_components(text_content)

    # Stage 3: Construct final components
    logger.info("Stage 3: Constructing final response...")
    response = construct_components(text_content, component_plan)

    logger.info(f"=== Response generation complete ===")
    return response


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
