# Agent Conversation Renderer

雙欄式 AI agent 介面：左側對話、右側展示（預覽 HTML、PDF、DOCX、圖片）。

## 專案結構

```
agent-ui/
├── app.py                        # 主程式
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── .streamlit/
│   ├── config.toml               # 主題與 server 設定
│   └── secrets.toml.example      # API key 範本（複製後填入）
├── uploads/                      # 使用者上傳的檔案（自動建立）
└── generated/                    # 模型產出的檔案（自動建立）
```

---

## 🚀 本機啟動

### 1. 建立虛擬環境

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 設定 API Key

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 用編輯器打開 .streamlit/secrets.toml，填入你的 Anthropic API key
```

### 4. 啟動

```bash
streamlit run app.py
```

瀏覽器開啟 `http://localhost:8501`

---

## 🐳 Docker 部署

### 前置：建立 secrets 檔案

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 填入 ANTHROPIC_API_KEY
```

### 用 Docker Compose 啟動（推薦）

```bash
docker compose up --build -d
```

- 應用程式在 `http://localhost:8501`
- `uploads/` 與 `generated/` 資料夾會掛載到容器，重啟後檔案不遺失

### 停止

```bash
docker compose down
```

### 單獨用 Docker

```bash
docker build -t agent-ui .

docker run -p 8501:8501 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/generated:/app/generated \
  -v $(pwd)/.streamlit/secrets.toml:/app/.streamlit/secrets.toml:ro \
  agent-ui
```

---

## ☁️ 雲端部署（Railway / Render / Fly.io）

任何支援 Docker 的雲端平台都可部署。以 Railway 為例：

```bash
# 安裝 Railway CLI
npm i -g @railway/cli

railway login
railway new
railway up
```

在 Railway Dashboard → Variables 加入：
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
```

---

## 功能說明

| 功能 | 說明 |
|------|------|
| 對話介面 | 左欄，與 Claude 對話，氣泡內嵌 info-card、表格等元件 |
| 展示介面 | 右欄，常駐 sidebar 列出所有檔案 |
| 上傳檔案 | PDF、DOCX、圖片，可在對話中附加或從展示介面上傳 |
| 模型產出 | Agent 生成的 HTML/DOCX/PDF 自動出現在展示介面 |
| 預覽 Tab | PDF iframe、圖片顯示、DOCX 文字、HTML 渲染 |
| 原始碼 Tab | 文字類檔案的 syntax highlight 原始碼 |
| JSON Tab | 檔案 metadata payload |
| 下載 | 每個檔案都有下載按鈕 |
