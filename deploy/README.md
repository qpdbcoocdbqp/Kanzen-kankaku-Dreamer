## 核心設計資源

- `design-systems`：大量品牌/風格系統紀錄於 DESIGN.md，是「設計風格資料包」。

   <details>
   給 agent 套用的設計系統 preset。
   典型內容是 `DESIGN.md`、`tokens.css`、`components.html`，
   新版一點的還有 `manifest.json`、`design-tokens.json`、`components.manifest.json`、`preview/`。
   功能是讓生成 UI、deck、artifact、prototype 時能讀取指定品牌/風格規則。

   **特殊目錄**
   - `_schema`：design system schema/tooling，定義 token、manifest、default CSS，不是可套用風格。
   - `default`：預設 Neutral Modern 設計系統。
   - `atelier-zero`、`totality-festival`、`urdu`、`warm-editorial`：較自訂/專案型的設計系統，不只是仿品牌。

   **品牌 / 產品風格系統**
   - `airbnb`：Airbnb 風格。
   - `airtable`：Airtable 風格。
   - `ant`：Ant Design 風格。
   - `apple`：Apple 風格。
   - `arc`：Arc Browser 風格。
   - `binance`：Binance.US 風格。
   - `bmw`、`bmw-m`：BMW / BMW M 風格。
   - `bugatti`、`ferrari`、`lamborghini`、`renault`、`tesla`：汽車品牌風格。
   - `cal`：Cal.com 風格。
   - `canva`、`figma`、`framer`、`miro`、`webflow`：設計/創作工具風格。
   - `cisco`、`ibm`、`mongodb`、`shopify`、`stripe`、`supabase`、`vercel`：企業/SaaS/開發者產品風格。
   - `claude`、`cohere`、`elevenlabs`、`huggingface`、`mistral-ai`、`openai`、`perplexity`、`replicate`、`runwayml`、`together-ai`、`x-ai`：AI 公司/工具風格。
   - `clickhouse`、`composio`、`cursor`、`github`、`hashicorp`、`mintlify`、`ollama`、`opencode-ai`、`posthog`、`raycast`、`resend`、`sentry`、`shadcn`、`warp`、`zapier`：developer/tooling 產品風格。
   - `coinbase`、`kraken`、`mastercard`、`revolut`、`wise`：金融/支付/crypto 風格。
   - `discord`、`duolingo`、`intercom`、`loom`、`notion`、`slack`、`spotify`、`superhuman`：consumer/productivity app 風格。
   - `nike`、`pinterest`、`playstation`、`starbucks`、`theverge`、`wired`、`xiaohongshu`、`wechat`、`vodafone`、`webex`、`uber`：媒體、社群、消費品牌風格。
   - `lovable`、`linear-app`、`lingo`、`minimax`、`nvidia`、`sanity`、`spacex`、`voltagent`：特定產品/品牌風格。

   **通用視覺風格系統**
   - `agentic`：agent/AI-native 感的產品風格。
   - `application`、`dashboard`、`enterprise`、`professional`、`trading-terminal`：偏 app/dashboard/企業工具 UI。
   - `artistic`、`creative`、`expressive`、`storytelling`：創意/敘事型視覺。
   - `bento`、`clean`、`minimal`、`modern`、`simple`、`sleek`、`refined`、`spacious`：乾淨、現代、通用產品 UI。
   - `bold`、`dramatic`、`energetic`、`premium`、`luxury`、`elegant`：高張力或高端感視覺。
   - `brutalism`、`neobrutalism`：粗黑框、強對比、刻意生硬的 brutalist UI。
   - `clay`、`claymorphism`、`glassmorphism`、`neumorphism`、`skeumorphism`：特定 UI 質感/擬物風格。
   - `colorful`、`gradient`、`neon`、`vibrant`、`cosmic`、`futuristic`、`hud`、`mission-control`：高彩度、科技感、未來感或控制台風格。
   - `cafe`、`paper`、`editorial`、`publication`、`warm-editorial`：文字、出版、溫暖紙感/編輯感。
   - `contemporary`、`corporate`、`friendly`、`flat`：通用商業/平面/親和風格。
   - `dithered`、`doodle`、`retro`、`vintage`、`pacman`、`tetris`：復古、遊戲、像素或手繪趣味風格.
   - `fantasy`、`perspective`、`levels`、`mono`、`material`、`meta`：特定視覺語彙或系統感 preset。
   </details>

- design-templates：生成用模板庫，包含 deck、image、video、frontend、Figma、motion、design review、theme factory 等。
- craft：品牌無關的設計 craft 規則。
- skills：agent 可用的設計/生成技能。
- templates/live-artifacts：live artifact 相關模板。
- prompt-templates/image、prompt-templates/video：媒體生成 prompt 模板。
