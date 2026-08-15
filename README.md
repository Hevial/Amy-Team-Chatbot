# Amy Team Chatbot 🎮

![Banner](https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Esports_Logo.svg/1024px-Esports_Logo.svg.png)

> **"Your tactical and regulatory companion."**

Amnesia Esports' internal RAG-powered Assistant Coach. Amy connects to the team's live documents (tournament rules, patch notes, tactical playbooks) and provides accurate, immediate answers with citations to help players and coaching staff prepare for competitive play.

Built with **FastAPI**, **LlamaIndex**, **Streamlit**, and **Google Gemini 2.0 Flash**.

---

## 🚀 Features

- **Retrieval-Augmented Generation (RAG):** Answers questions based strictly on the team's internal documents.
- **Source Citations:** Every answer includes exact references to the source files (e.g., `valorant_patch_notes_9_04.md`).
- **Esports Context:** The system prompt is fine-tuned to act as an Assistant Coach, giving direct and structured tactical advice.
- **Cloud-Native Architecture:** Dockerized and ready to deploy on Google Cloud Run.
- **Beautiful UI:** A dark-themed, esports-styled Streamlit chat interface.

---

## 🛠️ Technology Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Streamlit
- **LLM Engine:** Google Gemini 2.0 Flash (via `google-genai` SDK)
- **Embeddings:** Google text-embedding-004
- **Web Grounding:** Native Google Search Grounding (`types.GoogleSearch`)
- **Vector Database:** ChromaDB (Persistent local storage)
- **Containerization:** Docker & Google Cloud Run

---

## 💻 Local Development

### Prerequisites

- Python 3.11+
- Google AI Studio API Key ([Get one here](https://aistudio.google.com/app/apikey))

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-org/amy-team-chatbot.git
cd amy-team-chatbot

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Settings

Copy the example environment file and add your Google API Key:

```bash
cp .env.example .env
```
Edit `.env` and set `GOOGLE_API_KEY="your_api_key_here"`.

### 3. Ingest Data

The `data/samples/` directory contains sample rulebooks and patch notes. To generate embeddings and store them in ChromaDB, run the ingestion script:

```bash
python -m scripts.ingest
```

*(You can add more markdown, PDF, or text files to the `data/` folder and re-run the script with `--clear` to update the index).*

### 4. Run the Application

You can start the backend and frontend separately:

**Start FastAPI Backend:**
```bash
uvicorn src.main:app --reload --port 8080
```
- API Docs (Swagger): http://localhost:8080/docs
- Health Check: http://localhost:8080/health

**Start Streamlit Frontend:**
```bash
streamlit run frontend/app.py --server.port 8501
```
- Chat Interface: http://localhost:8501

---

## 🐳 Running with Docker

The easiest way to run the full stack locally is with Docker Compose. This starts both the API and the Frontend, and mounts the data/chroma directories for persistence.

```bash
# Make sure your .env file exists with the GOOGLE_API_KEY
docker-compose up --build
```

- **Frontend:** [http://localhost:8501](http://localhost:8501)
- **API Backend:** [http://localhost:8080/docs](http://localhost:8080/docs)

---

## ☁️ Google Cloud Run Deployment

This project is optimized for deployment on **Google Cloud Run** as a scalable, serverless container.

### Prerequisites
1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Authenticate: `gcloud auth login`
3. Set your project: `gcloud config set project YOUR_PROJECT_ID`
4. Ensure Secret Manager and Cloud Build APIs are enabled.

### 1-Click Deployment
You can deploy the full architecture to Cloud Run using the included deployment scripts:

**Windows (PowerShell):**
```powershell
.\deploy_gcp.ps1
```

**Linux / macOS:**
```bash
chmod +x deploy_gcp.sh
./deploy_gcp.sh
```

These scripts will:
1. Build the multi-stage Docker image via Google Cloud Build.
2. Push it to Artifact Registry.
3. Deploy a stateless Cloud Run service using the `$PORT` environment variable.
4. Pass the required LLM environment settings.

---

## 🏗️ Project Structure

```text
amy-team-chatbot/
├── data/                  # Source documents (Markdown, PDFs, etc.)
│   └── samples/           # Demo files (Valorant rules, patch notes)
├── chroma_db/             # Local vector database storage (ignored in git)
├── frontend/
│   └── app.py             # Streamlit chat interface
├── scripts/
│   └── ingest.py          # Document embedding pipeline
├── src/
│   ├── config.py          # Pydantic settings & env management
│   ├── engine.py          # LlamaIndex RAG query engine setup
│   ├── main.py            # FastAPI application
│   └── models.py          # Pydantic schemas for API validation
├── .env.example           # Environment variables template
├── docker-compose.yml     # Local multi-container setup
├── Dockerfile             # Multi-stage build for Cloud Run
├── requirements.txt       # Production dependencies
└── requirements-dev.txt   # Dev dependencies (ruff, testing)
```

---

## ✨ Code Quality & Conventions

This project follows Google-level engineering standards:
- **Linting & Formatting:** Enforced using `ruff`.
- **Git History:** Strict adherence to [Conventional Commits](https://www.conventionalcommits.org/).
- **Typing:** Strict Python type hints (`mypy` compatible) and Pydantic validation.

To run the linter:
```bash
ruff check src/ scripts/ frontend/
ruff format src/ scripts/ frontend/
```
