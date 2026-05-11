# Chat Renderer Design

Date: 2026-05-11

## Goal

Build a component-based conversation renderer on top of the existing `examples/ag-ui-assistant` UI package so an AI agent can return structured JSON and have the chat window render multiple output forms cleanly.

This design covers the first implementation phase only:

- Render structured components inside the chat window
- Support enhanced Markdown rendering, including Mermaid diagrams
- Extend the existing schema with a small, stable set of new component types

This phase does not include:

- Right-side HTML/CSS stage rendering
- A block-based content architecture
- Arbitrary HTML injection in chat messages
- Executable action wiring

## Existing Project Fit

The best foundation is `examples/ag-ui-assistant` because it already has:

- A typed AG-UI response model in `types.ts`
- A component-based renderer in `components/AGUIRenderer.tsx`
- A chat shell in `App.tsx`
- A backend schema and prompt flow in `services/agent_server.py`

The implementation should extend those pieces rather than introduce a parallel rendering stack.

## Recommended Approach

Use a component-based schema instead of a generic block-based schema for phase one.

Why:

- It aligns with the current repo structure
- It keeps the agent response contract simpler
- It lowers implementation risk
- It creates a stable base for a later right-side stage surface

The renderer should continue to process a `components[]` array, where each item has a `type` discriminator and a strongly typed payload.

## Response Contract

The model response remains:

```json
{
  "components": [],
  "suggestions": []
}
```

For this phase, `components` supports these types:

- `markdown`
- `info_card`
- `data_list`
- `step_process`
- `table`
- `stat_grid`
- `code_block`
- `action_group`

### Component Intent

#### `markdown`

Use for:

- Summaries
- Explanations
- Rich text answers
- Embedded Mermaid diagrams through fenced code blocks

Rules:

- Standard Markdown should render normally
- Fenced code blocks should render as code by default
- Fenced code blocks with language `mermaid` should render as Mermaid diagrams
- If Mermaid parsing fails, the renderer should fall back to a normal code block
- Raw HTML should not be rendered in the chat view

Example:

````json
{
  "type": "markdown",
  "content": "資料流如下：\n\n```mermaid\nflowchart LR\n  U[User] --> A[Agent]\n  A --> J[Structured JSON]\n  J --> C[Chat Renderer]\n```\n"
}
````

#### `info_card`

Use for:

- Warnings
- Success messages
- Danger states
- Important callouts

#### `data_list`

Use for:

- Key-value summaries
- Metadata
- Compact inspection output

#### `step_process`

Use for:

- Guided steps
- Procedures
- Multi-stage instructions

#### `table`

Use for:

- Comparisons
- Matrix-style summaries
- Small datasets

#### `stat_grid`

Use for:

- KPI summaries
- Counts
- Operational snapshots

Example:

```json
{
  "type": "stat_grid",
  "title": "今日營運摘要",
  "items": [
    { "label": "今日案件", "value": "184" },
    { "label": "平均首響時間", "value": "4m" },
    { "label": "自動解決率", "value": "62%" }
  ]
}
```

#### `code_block`

Use for:

- JSON
- HTML
- CSS
- TypeScript
- Python
- Other source snippets that should remain visibly source-oriented

Suggested shape:

```json
{
  "type": "code_block",
  "title": "HTML Preview Source",
  "language": "html",
  "content": "<section>...</section>"
}
```

#### `action_group`

Use for:

- Suggested next actions
- Structured follow-up choices
- Human-readable action affordances inside the chat response

This phase only renders these actions visually. It does not execute them.

Suggested shape:

```json
{
  "type": "action_group",
  "title": "你可以接著做",
  "items": [
    { "label": "改成管理員視角", "action": "switch-admin-view" },
    { "label": "加入案件趨勢圖", "action": "add-trend-chart" }
  ]
}
```

## Frontend Rendering Behavior

### Message Flow

- User messages remain plain text
- Model messages carry structured `components`
- The chat bubble renders all components in order
- `suggestions` remain lightweight quick prompts below the message
- Richer structured next steps belong in `action_group`, not in `suggestions`

### Renderer Behavior

`AGUIRenderer.tsx` remains the central dispatch point.

It should:

- Switch on `component.type`
- Render each component independently
- Prevent one component failure from breaking the rest of the message

### Error Handling

The renderer should degrade safely:

- Missing fields should fail softly at the component level
- Unknown component types should render a compact unsupported-state box
- Markdown rendering failures should degrade to plain text when possible
- Mermaid rendering failures should degrade to a normal code block

## Testing Strategy

Implementation should follow a TDD-style path for this feature.

Minimum test targets:

- New schema types are typed correctly
- `AGUIRenderer` renders new component types
- Mermaid blocks inside Markdown are detected and routed correctly
- Mermaid failure falls back safely
- Unknown component types do not break the message tree

For fast manual validation during development, `App.tsx` can host one or more sample model messages that exercise:

- Standard Markdown
- Mermaid Markdown
- `stat_grid`
- `code_block`
- `action_group`

## Implementation Boundaries

Phase one stops after the chat renderer becomes a stable structured-output surface.

The following are intentionally deferred to a later design:

- Right-side stage surface for HTML/CSS application previews
- Shared response contracts spanning chat and stage rendering
- Action click execution
- Agent-authored arbitrary UI injection in chat
- Migration toward a generic block-based schema

## Proposed File Scope

Primary files expected to change during implementation:

- `examples/ag-ui-assistant/types.ts`
- `examples/ag-ui-assistant/components/AGUIRenderer.tsx`
- `examples/ag-ui-assistant/App.tsx`
- `examples/ag-ui-assistant/services/agent_server.py`

Potential additions:

- Mermaid rendering dependency and related setup
- Focused tests for renderer behavior if the current example app has a test setup added during implementation

## Example Target Response

```json
{
  "components": [
    {
      "type": "markdown",
      "content": "已建立客服儀表板首頁草稿。\n\n```mermaid\nflowchart LR\n  U[User] --> A[Agent]\n  A --> J[Structured JSON]\n  J --> C[Chat Components]\n```\n"
    },
    {
      "type": "stat_grid",
      "title": "今日營運摘要",
      "items": [
        { "label": "今日案件", "value": "184" },
        { "label": "平均首響時間", "value": "4m" },
        { "label": "自動解決率", "value": "62%" }
      ]
    },
    {
      "type": "info_card",
      "title": "顯示方式說明",
      "description": "大型 dashboard 建議在右側舞台顯示。",
      "variant": "warning"
    },
    {
      "type": "table",
      "title": "輸出通道",
      "headers": ["通道", "用途"],
      "rows": [
        ["Chat components", "摘要、表格、步驟"],
        ["Stage surface", "完整 HTML/CSS 預覽"]
      ]
    },
    {
      "type": "action_group",
      "title": "你可以接著做",
      "items": [
        { "label": "改成管理員視角", "action": "switch-admin-view" },
        { "label": "加入案件趨勢圖", "action": "add-trend-chart" }
      ]
    }
  ],
  "suggestions": [
    "改成管理員視角",
    "加入案件趨勢圖"
  ]
}
```
