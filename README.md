# Amy Team Chatbot

> Your tactical and regulatory companion.

Amy is an internal RAG-powered Assistant Coach for Amnesia Esports. It connects to the team's live documents (tournament rules, patch notes, tactical playbooks) and provides accurate, cited answers to help players and coaching staff prepare for competitive play.

Built with **FastAPI**, **LlamaIndex**, **React (Vite)**, and **Google Gemini**.

<!-- Replace the path below with an actual screenshot of the new React chat interface -->
![Amy Chat Interface](docs/assets/app_screenshot.png)

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Local Development](#local-development)
- [Running with Docker](#running-with-docker)
- [Google Cloud Run Deployment](#google-cloud-run-deployment)
- [Project Structure](#project-structure)
- [Code Quality](#code-quality)

---

## Features

- **Retrieval-Augmented Generation (RAG)** — Answers questions based strictly on the team's internal documents stored in a persistent vector database.
- **Source Citations** — Every answer includes exact references to the source files, making it easy to verify information.
- **Web & Deep Search Grounding** — Integrated UI toggles for live Google Search grounding and Deep Search (`top_k=15`) for extensive research.
- **Esports-Tuned System Prompt** — The assistant is configured to behave as a professional esports coach: precise, direct, and scoped exclusively to the gaming domain.
- **Premium User Interface** — A modern, highly polished React frontend built with Tailwind CSS, shadcn/ui, and fluid micro-interactions designed to flagship standards.

---

## Technology Stack

| Layer            | Technology                                                        |
|------------------|-------------------------------------------------------------------|
| Backend API      | FastAPI (Python 3.11+)                                            |
| Frontend         | React 18, Vite, Tailwind CSS, shadcn/ui                           |
| LLM              | Google Gemini 3.5 Flash Lite (via `google-genai` SDK)             |
| Embeddings       | Google `gemini-embedding-2`                                       |
| Web Grounding    | Native Google Search Grounding (`types.GoogleSearch`)             |
| Vector Database  | ChromaDB (persistent local storage)                               |
| Orchestration    | LlamaIndex                                                        |

---

## Local Development

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for the frontend)
- A Google AI Studio API Key — [get one here](https://aistudio.google.com/app/apikey)

### 1. Setup Backend Environment

```bash
# Clone the repository
git clone https://github.com/Hevial/Amy-Team-Chatbot.git
cd Amy-Team-Chatbot

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\Activate.ps1       # Windows (PowerShell)

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Settings

Copy the example environment file and insert your API key:

```bash
cp .env.example .env
```

Open `.env` and set `GOOGLE_API_KEY` to the value you obtained from Google AI Studio.

### 3. Ingest Documents

The `data/samples/` directory ships with sample rulebooks and patch notes. To generate embeddings and store them in ChromaDB, run:

```bash
python -m scripts.ingest
```

### 4. Start the Application

Start the backend and frontend in two separate terminal windows.

**Terminal 1: FastAPI Backend**
```bash
# Ensure your virtual environment is active
uvicorn src.main:app --reload --port 8080
```
- API Docs: `http://localhost:8080/docs`

**Terminal 2: React Frontend**
```bash
cd frontend-web
npm install
npm run dev
```
- Web App: `http://localhost:5173` (or the port specified by Vite)

---

## Running with Docker

This project uses a **Unified Container Architecture** (Multi-stage build). The React frontend is compiled into static files and served directly by the FastAPI backend. This is the optimal architecture for production deployments.

```bash
# Ensure your .env file exists with the GOOGLE_API_KEY set
docker-compose up --build
```

| Service          | URL                                       |
|------------------|-------------------------------------------|
| Web App & API    | [http://localhost:8080](http://localhost:8080)   |
| API Docs         | [http://localhost:8080/docs](http://localhost:8080/docs) |

> **Note:** Docker copies the source code into the image at build time. For rapid iteration during development, running the backend and frontend natively (see Local Development above) is recommended.

---

## Google Cloud Run Deployment

This project is optimized for deployment on **Google Cloud Run** as a scalable, serverless container, leveraging **Google Cloud Build** for the CI/CD pipeline.

### Why this architecture?
This project implements a **Multi-stage Dockerfile**:
1. **Frontend Builder**: Uses Node.js to compile the React/Vite app into highly optimized static files.
2. **Backend Builder**: Uses Python to install all dependencies securely.
3. **Unified Runtime**: A lightweight Python image that bundles FastAPI and the compiled React app. FastAPI serves the frontend on the root `/` path, acting as a single, stateless deployable unit. 

This ensures Cloud Run only needs to manage and scale **one container** per instance, listening on `$PORT`.

### Prerequisites

1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
2. Authenticate: `gcloud auth login`
3. Set your project: `gcloud config set project YOUR_PROJECT_ID`
4. Enable Secret Manager and Cloud Build APIs in your GCP console.

### CI/CD Deployment (Recommended)

This project uses `cloudbuild.yaml` to define a professional Continuous Deployment pipeline directly from GitHub.

1. Create an **Artifact Registry** repository (e.g., `amnesia-repo`) in your preferred region.
2. Store your Google AI Studio API Key in **Secret Manager** as `google_api_key`.
3. Open `cloudbuild.yaml` and update the `substitutions` block at the bottom to match your repository name, service name, and region.
4. In the GCP Console, go to **Cloud Run** -> **Create Service**.
5. Select **Continuously deploy from a repository**, connect your GitHub repo, and choose **Cloud Build (cloudbuild.yaml)** as the build type.

Every `git push` will now automatically trigger Cloud Build, compile the multi-stage Dockerfile, and update the Cloud Run service with zero downtime.

### Alternative: Manual Deployment

If you prefer to deploy manually from your local machine without GitHub integration, use the included deployment scripts:

**Windows (PowerShell):**
```powershell
.\deploy_gcp.ps1
```

**Linux / macOS:**
```bash
./deploy_gcp.sh
```

These scripts use `gcloud run deploy --source .` to automatically trigger a Cloud Build job from your local files.

---

## Project Structure

```text
Amy-Team-Chatbot/
├── data/                      Source documents (Markdown, PDFs, etc.)
│   └── samples/               Demo files (Valorant rules, patch notes)
├── chroma_db/                 Local vector database storage
├── frontend-web/              Modern React UI (Vite + Tailwind + shadcn/ui)
│   ├── src/                   React components, hooks, and API client
│   └── package.json           Node dependencies
├── scripts/
│   └── ingest.py              Document embedding and ingestion pipeline
├── src/
│   ├── config.py              Pydantic settings
│   ├── engine.py              Hybrid RAG engine (ChromaDB + Google Search)
│   ├── main.py                FastAPI application
│   └── models.py              Pydantic schemas
└── requirements.txt           Backend dependencies
```

---

## Code Quality

This project enforces strict engineering standards:

- **Linting and Formatting**: Enforced using [Ruff](https://docs.astral.sh/ruff/) for Python and ESLint/Prettier for TypeScript.
- **Git History**: Follows [Conventional Commits](https://www.conventionalcommits.org/).
- **Type Safety**: Strict Python type hints (Pydantic) and TypeScript interfaces on all boundaries.
