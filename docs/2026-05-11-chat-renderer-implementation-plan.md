# Chat Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing `examples/ag-ui-assistant` chat UI so AI responses can render a richer component-based structured JSON format, including Mermaid-enabled Markdown.

**Architecture:** Keep the current `components[]` response contract and expand it with a few focused component types. Update the frontend renderer first, using local sample messages for validation, then align the backend schema and prompting so the agent can emit the new response shape consistently.

**Tech Stack:** React 19, TypeScript, Vite, `react-markdown`, FastAPI, Pydantic, OpenAI-compatible local API, Mermaid

---

## File Structure

### Existing files to modify

- `examples/ag-ui-assistant/types.ts`
  - Owns the frontend response contract and discriminated union types for chat-rendered components.
- `examples/ag-ui-assistant/components/AGUIRenderer.tsx`
  - Owns component dispatch and rendering behavior for structured model output.
- `examples/ag-ui-assistant/App.tsx`
  - Owns chat message state and is the best place to add local sample responses for manual verification.
- `examples/ag-ui-assistant/services/agent_server.py`
  - Owns the backend response schema and system prompt used to shape agent output.
- `examples/ag-ui-assistant/package.json`
  - Owns frontend dependencies and scripts.

### New files to create

- `examples/ag-ui-assistant/components/MermaidBlock.tsx`
  - Owns Mermaid diagram rendering and safe fallback behavior.

### Test approach

This example app does not currently include a dedicated automated frontend test harness. The plan still follows TDD intent by adding focused verification steps in small increments:

- Start with type and render contract changes
- Verify failure points quickly with TypeScript or runtime checks
- Add sample payloads in `App.tsx` for manual regression coverage

If a lightweight frontend test setup is added during implementation, keep it scoped to renderer behavior only.

## Task 1: Add schema types for new chat components

**Files:**
- Modify: `examples/ag-ui-assistant/types.ts`

- [ ] **Step 1: Add the new component enum values**

Update `ComponentType` in `examples/ag-ui-assistant/types.ts` to include the new chat-renderable types:

```ts
export enum ComponentType {
  MARKDOWN = 'markdown',
  INFO_CARD = 'info_card',
  DATA_LIST = 'data_list',
  STEP_PROCESS = 'step_process',
  TABLE = 'table',
  STAT_GRID = 'stat_grid',
  CODE_BLOCK = 'code_block',
  ACTION_GROUP = 'action_group'
}
```

- [ ] **Step 2: Define the new payload interfaces**

Append these interfaces below the existing `TableComponent` definition in `examples/ag-ui-assistant/types.ts`:

```ts
export interface StatItem {
  label: string;
  value: string;
  description?: string;
}

export interface StatGridComponent extends BaseComponent {
  type: ComponentType.STAT_GRID;
  title?: string;
  items: StatItem[];
}

export interface CodeBlockComponent extends BaseComponent {
  type: ComponentType.CODE_BLOCK;
  title?: string;
  language?: string;
  content: string;
}

export interface ActionItem {
  label: string;
  action: string;
  description?: string;
}

export interface ActionGroupComponent extends BaseComponent {
  type: ComponentType.ACTION_GROUP;
  title?: string;
  items: ActionItem[];
}
```

- [ ] **Step 3: Expand the AGUI union**

Update the `AGUIComponent` union in `examples/ag-ui-assistant/types.ts`:

```ts
export type AGUIComponent =
  | MarkdownComponent
  | InfoCardComponent
  | DataListComponent
  | StepProcessComponent
  | TableComponent
  | StatGridComponent
  | CodeBlockComponent
  | ActionGroupComponent;
```

- [ ] **Step 4: Run TypeScript compile to verify the contract is still valid**

Run:

```powershell
./node_modules/.bin/tsc.cmd --noEmit
```

Workdir:

```text
C:\Users\qpdbc\iloveit\Kanzen-kankaku-Dreamer\examples\ag-ui-assistant
```

Expected:

- TypeScript reports no syntax errors in `types.ts`
- Existing imports may fail later until renderer updates are completed, which is acceptable at this stage

- [ ] **Step 5: Commit**

```bash
git add examples/ag-ui-assistant/types.ts
git commit -m "feat: add chat renderer component schema types"
```

## Task 2: Add Mermaid renderer with safe fallback

**Files:**
- Create: `examples/ag-ui-assistant/components/MermaidBlock.tsx`
- Modify: `examples/ag-ui-assistant/package.json`

- [ ] **Step 1: Add the Mermaid dependency**

Add this dependency to `examples/ag-ui-assistant/package.json`:

```json
"mermaid": "^11.6.0"
```

Place it inside the existing `"dependencies"` object.

- [ ] **Step 2: Install dependencies and verify the lock file updates**

Run:

```powershell
npm install
```

Workdir:

```text
C:\Users\qpdbc\iloveit\Kanzen-kankaku-Dreamer\examples\ag-ui-assistant
```

Expected:

- `package-lock.json` updates
- `node_modules` contains Mermaid packages

- [ ] **Step 3: Create the Mermaid renderer component**

Create `examples/ag-ui-assistant/components/MermaidBlock.tsx` with this implementation:

```tsx
import React, { useEffect, useId, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  securityLevel: 'strict',
  theme: 'default',
});

interface MermaidBlockProps {
  chart: string;
  fallback?: React.ReactNode;
}

export const MermaidBlock: React.FC<MermaidBlockProps> = ({ chart, fallback }) => {
  const reactId = useId();
  const [svg, setSvg] = useState<string | null>(null);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const renderChart = async () => {
      try {
        setHasError(false);
        const renderId = `mermaid-${reactId.replace(/[:]/g, '-')}`;
        const result = await mermaid.render(renderId, chart);
        if (!cancelled) {
          setSvg(result.svg);
        }
      } catch (error) {
        console.error('Failed to render mermaid diagram', error);
        if (!cancelled) {
          setHasError(true);
          setSvg(null);
        }
      }
    };

    void renderChart();

    return () => {
      cancelled = true;
    };
  }, [chart, reactId]);

  if (hasError) {
    return <>{fallback ?? null}</>;
  }

  if (!svg) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-app-border bg-white dark:bg-app-card px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
        Rendering diagram...
      </div>
    );
  }

  return (
    <div
      className="rounded-xl border border-slate-200 dark:border-app-border bg-white dark:bg-app-card p-4 overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};
```

- [ ] **Step 4: Verify the new component compiles**

Run:

```powershell
./node_modules/.bin/tsc.cmd --noEmit
```

Workdir:

```text
C:\Users\qpdbc\iloveit\Kanzen-kankaku-Dreamer\examples\ag-ui-assistant
```

Expected:

- TypeScript recognizes the Mermaid component
- If renderer imports are not wired yet, only unrelated missing-use errors are acceptable

- [ ] **Step 5: Commit**

```bash
git add examples/ag-ui-assistant/package.json examples/ag-ui-assistant/package-lock.json examples/ag-ui-assistant/components/MermaidBlock.tsx
git commit -m "feat: add mermaid renderer for markdown blocks"
```

## Task 3: Upgrade markdown rendering to support Mermaid code fences

**Files:**
- Modify: `examples/ag-ui-assistant/components/AGUIRenderer.tsx`
- Modify: `examples/ag-ui-assistant/components/MermaidBlock.tsx`

- [ ] **Step 1: Update imports for the new renderer and component types**

Replace the top import block in `examples/ag-ui-assistant/components/AGUIRenderer.tsx` so it includes the new types and Mermaid component:

```tsx
import React from 'react';
import ReactMarkdown from 'react-markdown';
import {
  AGUIComponent,
  ComponentType,
  MarkdownComponent,
  InfoCardComponent,
  DataListComponent,
  StepProcessComponent,
  TableComponent,
  DataItem,
  StepItem,
  StatGridComponent,
  StatItem,
  CodeBlockComponent,
  ActionGroupComponent,
  ActionItem
} from '../types';
import { MermaidBlock } from './MermaidBlock';
import {
  Info,
  AlertTriangle,
  CheckCircle2,
  Ban,
  ListChecks,
  LayoutList,
  Sparkles,
  Code2,
  ArrowRight
} from 'lucide-react';
```

- [ ] **Step 2: Replace the Markdown block implementation**

Replace the existing `MarkdownBlock` component in `examples/ag-ui-assistant/components/AGUIRenderer.tsx` with:

```tsx
const MarkdownBlock: React.FC<RendererProps<MarkdownComponent>> = ({ data, themeColor }) => {
  const content = data.content || resolveText(data);
  if (!content) return null;

  return (
    <div className={`prose prose-slate dark:prose-invert max-w-none text-slate-700 dark:text-slate-300 leading-relaxed
      prose-headings:font-bold prose-headings:text-slate-800 dark:prose-headings:text-slate-100
      prose-p:my-3 prose-strong:text-slate-900 dark:prose-strong:text-slate-100 prose-strong:font-semibold
      prose-ul:list-disc prose-ul:pl-5
      prose-code:text-${themeColor}-600 dark:prose-code:text-${themeColor}-400
      prose-code:bg-${themeColor}-50 dark:prose-code:bg-${themeColor}-900/30
      prose-code:px-1 prose-code:py-0.5 prose-code:rounded-md prose-code:font-mono prose-code:text-sm`}>
      <ReactMarkdown
        components={{
          code({ className, children }) {
            const rawValue = String(children).replace(/\n$/, '');
            const match = /language-(\w+)/.exec(className || '');
            const language = match?.[1]?.toLowerCase();

            if (language === 'mermaid') {
              return (
                <MermaidBlock
                  chart={rawValue}
                  fallback={
                    <pre className="rounded-xl border border-slate-200 dark:border-app-border bg-slate-950 text-slate-100 p-4 overflow-x-auto text-sm">
                      <code>{rawValue}</code>
                    </pre>
                  }
                />
              );
            }

            return (
              <pre className="rounded-xl border border-slate-200 dark:border-app-border bg-slate-950 text-slate-100 p-4 overflow-x-auto text-sm">
                <code>{rawValue}</code>
              </pre>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
```

- [ ] **Step 3: Run a focused manual failure check**

In `examples/ag-ui-assistant/App.tsx`, temporarily inject a message using malformed Mermaid:

```ts
const malformedMermaidMessage = {
  id: 'debug-mermaid-fail',
  role: 'model' as const,
  data: {
    components: [
      {
        type: 'markdown',
        content: '```mermaid\nflowchart LR\nA-->\n```'
      }
    ],
    suggestions: []
  },
  timestamp: Date.now()
};
```

Use it as the initial model message and start the app.

Run:

```powershell
npm run dev
```

Expected:

- The app stays usable
- The malformed Mermaid block falls back to a code block instead of crashing the message

- [ ] **Step 4: Remove the temporary malformed-only fixture and keep the renderer logic**

Delete the temporary malformed-only fixture from `App.tsx` after verifying fallback behavior.

- [ ] **Step 5: Commit**

```bash
git add examples/ag-ui-assistant/components/AGUIRenderer.tsx examples/ag-ui-assistant/components/MermaidBlock.tsx
git commit -m "feat: render mermaid diagrams inside markdown responses"
```

## Task 4: Add renderers for stat grids, code blocks, and action groups

**Files:**
- Modify: `examples/ag-ui-assistant/components/AGUIRenderer.tsx`

- [ ] **Step 1: Add the stat grid renderer**

Insert this component below `Table` in `examples/ag-ui-assistant/components/AGUIRenderer.tsx`:

```tsx
const StatGrid: React.FC<RendererProps<StatGridComponent>> = ({ data, themeColor }) => {
  if (!data.items || data.items.length === 0) return null;

  return (
    <div className="my-5">
      {data.title && (
        <h4 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
          {data.title}
        </h4>
      )}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {data.items.map((item: StatItem, index: number) => (
          <div
            key={`${item.label}-${index}`}
            className={`rounded-2xl border border-slate-200 dark:border-app-border bg-white dark:bg-app-card p-4 shadow-sm`}
          >
            <div className={`text-xs uppercase tracking-wide text-${themeColor}-600 dark:text-${themeColor}-400`}>
              {item.label}
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
              {item.value}
            </div>
            {item.description && (
              <div className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                {item.description}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Add the code block renderer**

Insert this component below `StatGrid` in `examples/ag-ui-assistant/components/AGUIRenderer.tsx`:

```tsx
const CodeBlockCard: React.FC<RendererProps<CodeBlockComponent>> = ({ data }) => {
  if (!data.content) return null;

  return (
    <div className="my-5 overflow-hidden rounded-2xl border border-slate-200 dark:border-app-border bg-slate-950 text-slate-100 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
        <div className="flex items-center gap-2">
          <Code2 className="h-4 w-4" />
          <span>{data.title || 'Code Block'}</span>
        </div>
        <span>{data.language || 'text'}</span>
      </div>
      <pre className="overflow-x-auto p-4 text-sm">
        <code>{data.content}</code>
      </pre>
    </div>
  );
};
```

- [ ] **Step 3: Add the action group renderer**

Insert this component below `CodeBlockCard` in `examples/ag-ui-assistant/components/AGUIRenderer.tsx`:

```tsx
const ActionGroup: React.FC<RendererProps<ActionGroupComponent>> = ({ data, themeColor }) => {
  if (!data.items || data.items.length === 0) return null;

  return (
    <div className="my-5 rounded-2xl border border-slate-200 dark:border-app-border bg-white dark:bg-app-card p-4 shadow-sm">
      {data.title && (
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
          <Sparkles className={`h-4 w-4 text-${themeColor}-600 dark:text-${themeColor}-400`} />
          <span>{data.title}</span>
        </div>
      )}
      <div className="flex flex-col gap-2">
        {data.items.map((item: ActionItem, index: number) => (
          <button
            key={`${item.action}-${index}`}
            type="button"
            className={`flex items-center justify-between rounded-xl border border-slate-200 dark:border-app-border bg-slate-50 dark:bg-zinc-800/50 px-4 py-3 text-left transition-colors hover:border-${themeColor}-300 hover:bg-${themeColor}-50 dark:hover:border-${themeColor}-700 dark:hover:bg-${themeColor}-900/20`}
          >
            <div>
              <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                {item.label}
              </div>
              {item.description && (
                <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {item.description}
                </div>
              )}
            </div>
            <ArrowRight className={`h-4 w-4 text-${themeColor}-500 dark:text-${themeColor}-400`} />
          </button>
        ))}
      </div>
    </div>
  );
};
```

- [ ] **Step 4: Add the new switch cases**

Update the `switch (component.type)` block in `examples/ag-ui-assistant/components/AGUIRenderer.tsx`:

```tsx
                  case ComponentType.STAT_GRID:
                    return <StatGrid data={component} themeColor={themeColor} />;
                  case ComponentType.CODE_BLOCK:
                    return <CodeBlockCard data={component} themeColor={themeColor} />;
                  case ComponentType.ACTION_GROUP:
                    return <ActionGroup data={component} themeColor={themeColor} />;
```

Place them before `default:`.

- [ ] **Step 5: Run TypeScript compile to verify the renderer**

Run:

```powershell
./node_modules/.bin/tsc.cmd --noEmit
```

Workdir:

```text
C:\Users\qpdbc\iloveit\Kanzen-kankaku-Dreamer\examples\ag-ui-assistant
```

Expected:

- New component renderers compile cleanly
- No missing import/type errors remain in `AGUIRenderer.tsx`

- [ ] **Step 6: Commit**

```bash
git add examples/ag-ui-assistant/components/AGUIRenderer.tsx
git commit -m "feat: add stat code and action chat renderers"
```

## Task 5: Add sample structured responses to the chat shell for manual verification

**Files:**
- Modify: `examples/ag-ui-assistant/App.tsx`

- [ ] **Step 1: Add a reusable sample model response**

Add a constant near the top of `examples/ag-ui-assistant/App.tsx` after `DEFAULT_QUESTIONS`:

```tsx
const SAMPLE_MODEL_RESPONSE: ChatMessage = {
  id: 'sample-model-response',
  role: 'model',
  timestamp: Date.now(),
  data: {
    components: [
      {
        type: 'markdown',
        content: [
          '已建立客服儀表板首頁草稿。',
          '',
          '```mermaid',
          'flowchart LR',
          '  U[User] --> A[Agent]',
          '  A --> J[Structured JSON]',
          '  J --> C[Chat Components]',
          '```'
        ].join('\n')
      },
      {
        type: 'stat_grid',
        title: '今日營運摘要',
        items: [
          { label: '今日案件', value: '184', description: '較昨日增加 12%' },
          { label: '平均首響時間', value: '4m', description: '維持在 SLA 內' },
          { label: '自動解決率', value: '62%', description: '知識庫與自動回覆生效中' }
        ]
      },
      {
        type: 'code_block',
        title: 'Surface HTML 範例',
        language: 'html',
        content: '<section class="dashboard-shell">...</section>'
      },
      {
        type: 'action_group',
        title: '你可以接著做',
        items: [
          { label: '改成管理員視角', action: 'switch-admin-view', description: '調整資訊層級與指標內容' },
          { label: '加入案件趨勢圖', action: 'add-trend-chart', description: '補上 7 日流量與分類走勢' }
        ]
      }
    ],
    suggestions: ['改成管理員視角', '加入案件趨勢圖']
  }
};
```

- [ ] **Step 2: Seed the sample message into the chat state**

Replace the current messages state initializer in `examples/ag-ui-assistant/App.tsx`:

```tsx
const [messages, setMessages] = useState<ChatMessage[]>([]);
```

with:

```tsx
const [messages, setMessages] = useState<ChatMessage[]>([SAMPLE_MODEL_RESPONSE]);
```

- [ ] **Step 3: Run the app and verify the visual result**

Run:

```powershell
npm run dev
```

Workdir:

```text
C:\Users\qpdbc\iloveit\Kanzen-kankaku-Dreamer\examples\ag-ui-assistant
```

Expected:

- The sample response appears on first load
- Markdown text renders normally
- Mermaid renders as a diagram
- `stat_grid`, `code_block`, and `action_group` appear as distinct visual blocks
- Existing user message flow still works when sending another prompt

- [ ] **Step 4: Keep the sample response as a development fixture**

Leave `SAMPLE_MODEL_RESPONSE` in place for now so future prompt and renderer changes remain easy to validate locally.

- [ ] **Step 5: Commit**

```bash
git add examples/ag-ui-assistant/App.tsx
git commit -m "feat: add structured sample response for chat renderer validation"
```

## Task 6: Align backend schema and prompt output

**Files:**
- Modify: `examples/ag-ui-assistant/services/agent_server.py`

- [ ] **Step 1: Add backend models for the new component shapes**

In `examples/ag-ui-assistant/services/agent_server.py`, add these models after `TableComponent`:

```py
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
    type: Literal['stat_grid'] = 'stat_grid'
    title: Optional[str] = None
    items: List[StatItem]

class CodeBlockComponent(BaseComponent):
    type: Literal['code_block'] = 'code_block'
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
    type: Literal['action_group'] = 'action_group'
    title: Optional[str] = None
    items: List[ActionItem]
```

- [ ] **Step 2: Expand the backend union**

Replace the current `ComponentUnion` in `examples/ag-ui-assistant/services/agent_server.py` with:

```py
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
```

- [ ] **Step 3: Update the system instruction to describe the new output types**

Replace the "Available Components" section inside `system_instruction` in `examples/ag-ui-assistant/services/agent_server.py` with this expanded version:

```py
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
```

- [ ] **Step 4: Start the backend and verify schema parsing still works**

Run:

```powershell
uv run python -m services.agent_server
```

Workdir:

```text
C:\Users\qpdbc\iloveit\Kanzen-kankaku-Dreamer\examples\ag-ui-assistant
```

Expected:

- FastAPI starts successfully on port 8000
- No Pydantic discriminator errors are raised on startup

- [ ] **Step 5: Commit**

```bash
git add examples/ag-ui-assistant/services/agent_server.py
git commit -m "feat: extend agent schema for richer chat renderer output"
```

## Task 7: Final verification pass

**Files:**
- Verify: `examples/ag-ui-assistant/types.ts`
- Verify: `examples/ag-ui-assistant/components/AGUIRenderer.tsx`
- Verify: `examples/ag-ui-assistant/components/MermaidBlock.tsx`
- Verify: `examples/ag-ui-assistant/App.tsx`
- Verify: `examples/ag-ui-assistant/services/agent_server.py`
- Verify: `examples/ag-ui-assistant/package.json`

- [ ] **Step 1: Run frontend compile verification**

Run:

```powershell
./node_modules/.bin/tsc.cmd --noEmit
```

Workdir:

```text
C:\Users\qpdbc\iloveit\Kanzen-kankaku-Dreamer\examples\ag-ui-assistant
```

Expected:

- TypeScript finishes without errors

- [ ] **Step 2: Run the frontend app for visual verification**

Run:

```powershell
npm run dev
```

Workdir:

```text
C:\Users\qpdbc\iloveit\Kanzen-kankaku-Dreamer\examples\ag-ui-assistant
```

Expected:

- The app loads successfully
- The seeded sample response displays all new component types correctly
- Mermaid diagrams render
- Mermaid parse failures still fall back safely if manually tested

- [ ] **Step 3: Run the backend app for schema verification**

Run:

```powershell
uv run python -m services.agent_server
```

Workdir:

```text
C:\Users\qpdbc\iloveit\Kanzen-kankaku-Dreamer\examples\ag-ui-assistant
```

Expected:

- The backend starts cleanly
- No response model or union discriminator startup errors occur

- [ ] **Step 4: Verify the end-to-end chat request manually**

With both frontend and backend running, send a prompt such as:

```text
請用 Mermaid 說明聊天室資料流，並附上三個 KPI 與兩個後續建議
```

Expected:

- The response includes Markdown
- Mermaid renders in the chat
- KPI data can appear as `stat_grid`
- Follow-up choices can appear as `action_group`
- The app remains interactive after the message renders

- [ ] **Step 5: Commit**

```bash
git add examples/ag-ui-assistant/types.ts examples/ag-ui-assistant/components/AGUIRenderer.tsx examples/ag-ui-assistant/components/MermaidBlock.tsx examples/ag-ui-assistant/App.tsx examples/ag-ui-assistant/services/agent_server.py examples/ag-ui-assistant/package.json examples/ag-ui-assistant/package-lock.json
git commit -m "feat: deliver structured chat renderer enhancements"
```
