# Kanzen-kankaku-Dreamer
Test agent driven interface.  Playing with Kanzen kankaku Dreamer [完全感覚Dreamer](https://www.youtube.com/watch?v=NWDAjOsTYC8).

* **About 完全感覚Dreamer**

  > 完全感覚Dreamer · ONE OK ROCK
  >
  > Niche Syndrome

* Recommendation

  * [ONE OK ROCK - 完全在宅Dreamer](https://www.youtube.com/watch?v=qwj_TFDdUSI)

## Refernce

* [streamlit/streamlit](https://github.com/streamlit/streamlit)
  * [build conversational apps](https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps)

* [ag-ui-protocol/ag-ui](https://github.com/ag-ui-protocol/ag-ui)
* [CopilotKit/CopilotKit](https://github.com/CopilotKit/CopilotKit)


## Open design

```bash
git clone https://github.com/nexu-io/open-design.git
cd open-design/deploy
cp .env.example .env
echo "OD_API_TOKEN=$(openssl rand -hex 32)" >> .env
docker compose up -d
# open http://localhost:7456
```

## Agent UI

* **Setup**
```sh
uv venv --python 3.13
uv pip install streamlit
uv pip install ag-ui-protocol copilotkit
uv pip install gradio
source .venv/bin/activate
```

### Streamlit

* **Simple chat UI**

  ```sh
  streamlit run app/app.py \
    --server.address 127.0.0.1 \
    --server.port 9000 \
    --browser.gatherUsageStats false \
    --server.headless true
  ```

* **Style chat UI**
  * Download font file (`ttf`) 
    * `en`: [PressStart2P](https://fonts.google.com/specimen/Press+Start+2P)
    * `zh`: [Zpix](https://github.com/SolidZORO/zpix-pixel-font)

  * Set `ttf` to below path
    * `EN_FONT_PATH = "app/assets/PressStart2P-Regular.ttf"`
    * `ZH_FONT_PATH = "app/assets/zpix.ttf"`

  * Run APP

    ```sh
    streamlit run app/style_app.py \
      --server.address 127.0.0.1 \
      --server.port 9000 \
      --browser.gatherUsageStats false \
      --server.headless true
    ```

### AG-UI ADK

* **Copilotkit**

  ```sh
  # create
  npx copilotkit@latest create --name adk-ui --framework adk

  # install packages
  cd adk-ui
  pnpm install

  # windows use: source agent/.venv/Scripts/activate
  # linux use:   source agent/.venv/bin/activate

  # In new terminal, start ADK agent
  source examples/adk-ui/agent/.venv/Scripts/activate
  uv run examples/adk-ui/agent/main.py

  # In new terminal, start AG-UI
  cd examples/adk-ui
  pnpm run dev:ui
  ```
  
  * ADK agent host: `http://localhost:8080`
  * AG-UI host : `http://localhost:3000`

* **AG-UI**

  ```sh
  # create
  npx create-ag-ui-app@latest --adk

  # below command follows Copilotkit guide
  ```


### AG-UI-Assistant

* Google AI studio generate UI.

  * Current local implementation highlights
    * component-based chat renderer for structured JSON output
    * Mermaid diagram rendering inside Markdown code fences
    * additional chat component types:
      * `stat_grid`
      * `code_block`
      * `action_group`
    * backend proxy uses OpenAI-compatible API at `http://localhost:9006/v1`
    * current backend model: `qwen`

  ```sh
  cd examples/ag-ui-assistant
  npm install

  # In new terminal, start agent server
  uv run python -m services.agent_server

  # In new terminal, start AG-UI
  npm run dev
  ```

  * agent host: `http://localhost:8000`
  * AG-UI host : `http://localhost:5173` or the Vite port shown in terminal
  * frontend API target: `VITE_API_URL=http://localhost:8000/chat`
  * backend LLM target: `http://localhost:9006/v1`

  * Example structured response payload

    ```json
    {
      "components": [
        {
          "type": "markdown",
          "content": "```mermaid\nflowchart LR\n  U[User] --> A[Agent]\n  A --> J[Structured JSON]\n  J --> C[Chat Components]\n```\n"
        },
        {
          "type": "stat_grid",
          "title": "今日營運摘要",
          "items": [
            { "label": "今日案件", "value": "184" },
            { "label": "平均首響時間", "value": "4m" }
          ]
        },
        {
          "type": "action_group",
          "title": "你可以接著做",
          "items": [
            { "label": "改成管理員視角", "action": "switch-admin-view" }
          ]
        }
      ],
      "suggestions": [
        "加入案件趨勢圖"
      ]
    }
    ```
