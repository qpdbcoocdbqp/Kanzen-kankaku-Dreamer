# Kanzen-kankaku-Dreamer
Test agent driven interface.  Playing with Kanzen kankaku Dreamer [完全感覚Dreamer](https://www.youtube.com/watch?v=NWDAjOsTYC8).

* **About 完全感覚Dreamer**

> 完全感覚Dreamer · ONE OK ROCK
>
> Niche Syndrome

## Refernce

* [streamlit/streamlit](https://github.com/streamlit/streamlit)
  * [build conversational apps](https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps)

* [ag-ui-protocol/ag-ui](https://github.com/ag-ui-protocol/ag-ui)
* [CopilotKit/CopilotKit](https://github.com/CopilotKit/CopilotKit)

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
