# 🔍 Drive Search Assistant

A **production-quality Conversational Google Drive Search Assistant** that allows users to search and discover files inside Google Drive using natural language.

Built with **LangChain** · **FastAPI** · **Streamlit** · **Google Drive API**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗣️ **Natural Language Search** | Ask in plain English — "Find PDFs about marketing from last week" |
| 🔄 **Multi-turn Conversations** | Follow-up questions, refinements, and context retention |
| 🛠️ **Tool Calling** | LLM uses structured function calls — never touches Drive directly |
| 🔎 **Advanced Queries** | Searches by name, type, content, date, and combinations |
| 💬 **Clarifying Questions** | Asks for more info when queries are ambiguous |
| 📊 **Rich File Cards** | File type icons, sizes, dates, and clickable Drive links |
| 🌙 **Premium Dark UI** | Polished Streamlit interface with glassmorphism design |
| 🚀 **Deployment Ready** | Configs for Railway, Render, and Docker included |

---

## 📺 Demo

![Drive Search Demo](Working.mp4)

*Note: If the video doesn't play, you can find the source file at `Working.mp4` in the root directory.*

---

## 🏗️ Architecture

```
User
 → Streamlit Frontend (Chat UI)
   → FastAPI Backend (REST API)
     → LangChain Agent (Reasoning + Tool Calling)
       → DriveSearchTool (Query Builder)
         → Google Drive API (File Search)
```

**Key principle:** The LLM **never** calls Google Drive directly. It always goes through the `DriveSearchTool` via LangChain's tool-calling mechanism.

---

## 📁 Project Structure

```
Drive Search/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── drive_agent.py      # LangChain conversational agent
│   │   ├── tools/
│   │   │   └── drive_search_tool.py # LangChain tool for Drive search
│   │   ├── services/
│   │   │   ├── drive_service.py     # Google Drive API client
│   │   │   └── llm_service.py      # LLM provider factory
│   │   ├── prompts/
│   │   │   └── agent_prompts.py     # System prompt templates
│   │   ├── routes/
│   │   │   └── chat.py             # FastAPI endpoints
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic request/response models
│   │   ├── utils/
│   │   │   ├── query_builder.py    # Drive API query builder
│   │   │   └── logger.py          # Structured logging
│   │   ├── config.py              # Environment config
│   │   └── main.py                # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── streamlit_app.py           # Chat UI
│   └── requirements.txt
├── .env.example                   # Environment template
├── .gitignore
├── Dockerfile
├── Procfile
├── railway.toml
├── render.yaml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud project with Drive API enabled
- Service account with Drive access
- OpenAI or Anthropic API key

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd "Drive Search"

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env with your actual API keys and settings
```

### 3. Google Drive Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable the **Google Drive API**
4. Create a **Service Account** → download the JSON key
5. Save as `backend/service_account.json`
6. **Share your target Drive folder** with the service account email
7. Set `GOOGLE_DRIVE_FOLDER_ID` in `.env` (optional — restricts search scope)

### 4. Run the Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 5. Run the Frontend

```bash
cd frontend
streamlit run streamlit_app.py --server.port 8501
```

Open `http://localhost:8501` in your browser.

---

## 🔧 Configuration

All settings are managed through environment variables. See `.env.example` for the full list.

### LLM Provider

**OpenAI (default):**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o
```

**Anthropic:**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-3-5-sonnet-20240620
```

**Google Gemini:**
```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=...
LLM_MODEL=gemini-1.5-flash
```

**Groq:**
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk-...
LLM_MODEL=llama-3.3-70b-versatile
```

### Google Drive Auth

**Local development** — JSON file:
```env
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
```

**Cloud deployment** — JSON as environment variable:
```env
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

---

## 🔍 How It Works

### Query Flow

1. User types: *"Find financial reports from last week"*
2. Streamlit sends the message to `POST /api/chat`
3. FastAPI passes it to the **LangChain Agent**
4. The agent reasons and calls `drive_search` tool with:
   ```json
   {
     "name_contains": "financial report",
     "modified_after": "2026-05-05"
   }
   ```
5. The tool builds a Drive API query:
   ```
   name contains 'financial report' and modifiedTime > '2026-05-05T00:00:00' and trashed = false
   ```
6. `GoogleDriveService` executes the query and returns results
7. The agent formats a conversational response with file cards
8. Response is sent back to Streamlit for display

### Supported Search Types

| Search Type | Example Query | Drive API `q` Generated |
|-------------|--------------|------------------------|
| Name search | "Find budget files" | `name contains 'budget'` |
| File type | "Show me PDFs" | `mimeType = 'application/pdf'` |
| Content search | "Files about revenue" | `fullText contains 'revenue'` |
| Date filter | "Modified yesterday" | `modifiedTime > '2026-05-11T00:00:00'` |
| Combined | "PDFs about marketing from last week" | Multiple `and` clauses |

---

## 🚢 Deployment

### Railway

1. Push code to GitHub
2. Connect your repo in [Railway](https://railway.app)
3. Add environment variables from `.env.example`
4. For Google credentials, paste the JSON into `GOOGLE_SERVICE_ACCOUNT_JSON`
5. Railway auto-detects `railway.toml` and deploys

### Render

1. Push code to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your repo
4. Render uses `render.yaml` for config
5. Add secrets in the Render dashboard

### Docker

```bash
docker build -t drive-search .
docker run -p 8000:8000 --env-file .env drive-search
```

---

## 📡 API Reference

### `POST /api/chat`

Send a message to the assistant.

**Request:**
```json
{
  "message": "Find PDFs about marketing",
  "conversation_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "I found 3 PDF files related to marketing...",
  "files": [
    {
      "id": "abc123",
      "name": "Marketing Plan Q4.pdf",
      "mime_type": "application/pdf",
      "web_view_link": "https://drive.google.com/...",
      "modified_time": "2026-05-10T14:30:00Z"
    }
  ],
  "query_explanation": "Drive API query: `mimeType = 'application/pdf' and fullText contains 'marketing' and trashed = false`",
  "conversation_id": "abc-123-def",
  "timestamp": "2026-05-12T12:00:00"
}
```

### `POST /api/clear?conversation_id=xxx`

Clear conversation history for a session.

### `GET /health`

Health check endpoint.

---

## 🧪 Example Conversations

**Simple search:**
> **User:** Find budget spreadsheets  
> **Bot:** I found 4 spreadsheets matching "budget":  
> 📊 Budget 2026.xlsx — Modified May 8  
> 📊 Q1 Budget Review — Modified Apr 15  
> …

**Ambiguous query:**
> **User:** Find reports  
> **Bot:** What type of reports are you looking for? I can search for:  
> - 📄 Documents (Google Docs, Word)  
> - 📊 Spreadsheets (Sheets, Excel)  
> - 📕 PDFs  
> Any specific keywords or date range?

**Follow-up:**
> **User:** The PDF ones from this month  
> **Bot:** Found 2 PDF reports modified in May 2026:  
> 📕 Monthly Sales Report.pdf — May 10  
> 📕 Expense Report May.pdf — May 7

---

## 🛠️ Troubleshooting

### Common Issues

1. **"File not found" or empty results:**
   - Ensure you've shared the specific folder/files with the service account email found in your `service_account.json`.
   - Check if `GOOGLE_DRIVE_FOLDER_ID` in `.env` is correct. If left empty, it searches the entire Drive accessible to the service account.

2. **LLM Connection Errors:**
   - Verify your `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is valid and has enough credits.
   - Check your internet connection.

3. **Streamlit cannot connect to Backend:**
   - Ensure the backend is running on `http://localhost:8000` (or the URL set in `BACKEND_URL`).
   - Check for CORS issues if running on different domains.

4. **Service Account Authentication Failed:**
   - Make sure `service_account.json` is in the `backend/` directory and is a valid Google Cloud key.

---

## 📝 License

MIT

---

<div align="center">
  <sub>Built with ❤️ using LangChain, FastAPI, Streamlit, and Google Drive API</sub>
</div>
