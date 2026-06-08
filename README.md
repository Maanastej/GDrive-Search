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
| ⚙️ **CI/CD Pipeline** | Automated testing and Docker Hub deployment via GitHub Actions |

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
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # GitHub Actions CI/CD pipeline
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
├── tests/
│   ├── __init__.py
│   └── test_api.py                # pytest test suite for FastAPI endpoints
├── .env                           # Local secrets (gitignored — never commit)
├── .env.example                   # Environment template (safe to commit)
├── .gitignore
├── docker-compose.yml             # Multi-container local dev stack
├── Dockerfile                     # Container definition
├── deploy.ps1                     # PowerShell deployment automation script
├── Procfile
├── railway.toml
├── render.yaml
└── README.md
```

---

## ⚙️ CI/CD Pipeline

This project includes a fully automated CI/CD pipeline using **GitHub Actions** and **Docker Hub**.

### Pipeline Flow

```
Pull Request to main
  → GitHub Actions triggers
  → Runs pytest on FastAPI endpoints
  → Must pass before merge is allowed (branch protection)

Merge to main
  → GitHub Actions triggers
  → Runs pytest
  → Builds Docker image
  → Pushes image to Docker Hub
```

### Pipeline Jobs

**Job 1 — Test** *(runs on both PRs and pushes to main)*
- Sets up Python 3.11
- Installs dependencies from `backend/requirements.txt`
- Runs `pytest tests/ -v` against the live FastAPI app

**Job 2 — Build & Push** *(only runs on merge to main, after tests pass)*
- Logs into Docker Hub using GitHub Secrets
- Builds Docker image from `Dockerfile`
- Pushes image tagged as `latest` to Docker Hub

### Branch Protection

The `main` branch is protected with the following rules:
- **Pull request required** — no direct pushes to main; all changes go through a PR
- **Status checks required** — CI tests must pass before a PR can be merged

This ensures broken code never reaches main.

### GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `DOCKER_USERNAME` | Your Docker Hub username |
| `DOCKER_TOKEN` | Docker Hub personal access token (Read/Write/Delete) |
| `APP_SECRET_KEY` | Application secret key injected at runtime |

Credentials are **never hardcoded** — they are injected securely at runtime via GitHub Secrets.

---

## 🔐 Secrets Management

This project follows a strict secrets management pattern to ensure no credentials are ever exposed in code or logs.

### Local Development

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill in your actual values in `.env`
3. `.env` is listed in `.gitignore` — it will never be committed

### CI/CD Pipeline

Secrets are stored in **GitHub Repository Secrets** (Settings → Secrets and variables → Actions) and injected into the workflow at runtime:

```yaml
env:
  SECRET_KEY: ${{ secrets.APP_SECRET_KEY }}
```

GitHub automatically masks secret values in logs, replacing them with `***`.

### Docker Runtime

Secrets are passed into the container via the `--env-file` flag locally:

```bash
docker run --env-file .env -p 8000:8000 maanastej/gdrive-search:latest
```

Or via the `-e` flag in the CI pipeline:

```bash
docker run -e SECRET_KEY=$SECRET_KEY maanastej/gdrive-search:latest
```

**Rule:** secrets live in `.env` locally, in GitHub Secrets in CI, and are injected at runtime into containers. They never appear in source code.

---

## 🐳 Docker Compose

For local development, Docker Compose spins up the full stack — app and database — with a single command.

### Usage

```bash
docker-compose up
```

This starts:
- **app** — the Drive Search backend on port 8000
- **db** — a PostgreSQL 15 database on port 5432

### Configuration

```yaml
services:
  app:
    image: maanastej/gdrive-search:latest
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
```

`depends_on` ensures the database container is ready before the app starts. Containers communicate using service names as hostnames — the app connects to the database at `db:5432`.

### Stop the stack

```bash
docker-compose down
```

---

## 🖥️ PowerShell Deployment Script

For manual local deployments, use the included `deploy.ps1` script:

```powershell
# Set your Docker Hub username as an environment variable
$env:DOCKER_USERNAME = "your-dockerhub-username"

# Run the deployment script
.\deploy.ps1
```

The script will:
1. Build the Docker image locally
2. Tag it with your Docker Hub username
3. Push it to Docker Hub
4. Exit with a clear error message if any step fails

Optionally pass a custom image name or tag:

```powershell
.\deploy.ps1 -ImageName "gdrive-search" -Tag "v1.0"
```

---

## 🧪 Testing

Tests are located in the `tests/` directory and use **pytest** with FastAPI's `TestClient`.

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest tests/ -v
```

### Test Coverage

| Test | What it checks |
|------|---------------|
| `test_root` | App starts and root endpoint responds |
| `test_app_starts` | FastAPI app object is correctly initialized |

Tests run automatically on every `git push` and on every Pull Request via the CI/CD pipeline.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud project with Drive API enabled
- Service account with Drive access
- OpenAI or Anthropic API key
- Docker Desktop (for containerized deployment)

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

### 4. Run with Docker Compose (recommended)

```bash
docker-compose up
```

The API will be available at `http://localhost:8000`

### 5. Run Manually

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
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

### Docker Hub

The latest image is automatically built and pushed to Docker Hub on every merge to `main`.

```bash
# Pull the latest image
docker pull maanastej/gdrive-search:latest

# Run the container
docker run -p 8000:8000 --env-file .env maanastej/gdrive-search:latest
```

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

### Docker (Local)

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

5. **CI/CD Pipeline Failing:**
   - Check that `DOCKER_USERNAME` and `DOCKER_TOKEN` secrets are correctly set in GitHub repo Settings.
   - Ensure the Docker Hub token has Read, Write, and Delete permissions.

6. **Docker Compose: app can't connect to database:**
   - Make sure you're using `db` as the hostname in your connection string, not `localhost`.
   - Check that `depends_on` is set correctly in `docker-compose.yml`.

---

## 📝 License

MIT

---

<div align="center">
  <sub>Built with ❤️ using LangChain, FastAPI, Streamlit, and Google Drive API</sub>
</div>