# Calls to Knowledge

Turn meeting and call audio into a structured, searchable knowledge base. A Windows desktop agent detects active calls (Teams, Zoom, Chrome, Edge, Slack, Webex), records system audio via WASAPI loopback, transcribes with Whisper, extracts summaries with an LLM, and stores everything in Supabase. A React dashboard lets you browse calls, review transcripts, and export Markdown.

## What it does

1. **Detect** — Monitors Windows audio sessions and starts recording when a configured call app has active output for at least `min_duration_seconds`.
2. **Record** — Captures loopback audio to WAV files on disk.
3. **Transcribe** — OpenAI Whisper API (default) or local `faster-whisper`.
4. **Summarize** — GPT extracts title, summary, key points, next steps, and decisions as structured JSON.
5. **Store** — Persists calls, transcripts, and summaries in Supabase (Postgres).
6. **Browse** — React UI lists calls, shows detail views, project dashboards, live recording status via WebSocket, and Markdown export.

Manual recording is also supported through the API and UI (mic / override triggers).

## Architecture

```
┌─────────────────┐     WASAPI loopback      ┌──────────────────┐
│  Call apps      │ ───────────────────────► │  AudioMonitor    │
│  (Teams, Zoom…) │                          │  + AudioRecorder │
└─────────────────┘                          └────────┬─────────┘
                                                      │ WAV
                                                      ▼
┌─────────────────┐     REST + WebSocket     ┌──────────────────┐
│  React UI       │ ◄──────────────────────► │  FastAPI backend │
│  (Vite)         │                          │                  │
└─────────────────┘                          │  Transcription   │
                                             │  AIProcessor     │
                                             │  SupabaseClient  │
                                             └────────┬─────────┘
                                                      │
                                                      ▼
                                             ┌──────────────────┐
                                             │  Supabase        │
                                             │  (Postgres)      │
                                             └──────────────────┘
```

**Processing pipeline** (runs after each call ends):

```
audio → transcribe → save transcript → LLM summary → save summary → update call status
```

Live status updates (`recording`, `processing`, `idle`, `call_ready`) are pushed over `WS /ws`.

## Tech stack

| Layer | Technologies |
|-------|--------------|
| Backend | Python 3.11+, FastAPI, uvicorn, uv |
| Audio (Windows) | pycaw (session detection), pyaudiowpatch (WASAPI loopback) |
| Speech-to-text | OpenAI Whisper API or faster-whisper (local) |
| AI | OpenAI Chat Completions (JSON summary) |
| Database | Supabase (Postgres) via supabase-py async client |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query |
| Tests | pytest (backend), Vitest + Testing Library (frontend) |

## Requirements

- **OS:** Windows (audio capture uses WASAPI loopback)
- **Python:** 3.11+
- **Node.js:** 18+ (frontend)
- **Accounts:** OpenAI API key, Supabase project

## Setup

### 1. Clone and install backend

```bash
git clone https://github.com/EdoardoMorucci/calls-to-knowledge.git
cd calls-to-knowledge

# Install Python deps with uv
uv sync
```

### 2. Configure secrets

Copy the example config and fill in your keys:

```bash
cp config.toml.example config.toml
```

Required values in `config.toml`:

| Section | Key | Description |
|---------|-----|-------------|
| `openai` | `api_key` | OpenAI API key (transcription + summarization) |
| `supabase` | `url` | Supabase project URL |
| `supabase` | `service_role_key` | Service role key (backend only; never expose to frontend) |
| `transcription` | `provider` | `"openai"` or `"local"` |
| `ai` | `model` | Chat model for summaries (e.g. `gpt-4o-mini`) |
| `recording` | `audio_dir` | Directory for WAV files |
| `server` | `host`, `port` | Backend bind address |

See also `.env.example` for a flat reference of the same secrets. The app reads **`config.toml` only**.

> **Never commit** `config.toml` — it is listed in `.gitignore`.

### 3. Initialize Supabase

Run the schema in the Supabase SQL Editor:

```bash
# File: backend/db/schema.sql
```

Creates tables: `projects`, `calls`, `transcripts`, `summaries`.

### 4. Install and run frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/ws` to the backend (port 8000).

### 5. Start the backend

From the repo root:

```bash
uv run python -m backend.main
```

Or with uvicorn directly:

```bash
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open the UI at `http://localhost:5173`.

## Configuration reference

### Transcription providers

- **`openai`** — Uses Whisper API (`whisper-1`) with segment timestamps.
- **`local`** — Uses `faster-whisper` with the model size set in `local_model` (e.g. `medium`, `large-v3`). No API cost; requires more CPU/GPU.

### Monitored call apps

Default processes in `recording.call_apps`:

`Teams.exe`, `chrome.exe`, `msedge.exe`, `zoom.exe`, `slack.exe`, `webex.exe`

Recording starts after `min_duration_seconds` of continuous audio activity from a listed app.

## API overview

Base URL: `http://127.0.0.1:8000` (or via frontend proxy at `/api`).

### Calls

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/calls` | List calls (`?project_id=`, `limit`, `offset`) |
| `GET` | `/calls/{id}` | Call detail with transcript and summary |
| `PATCH` | `/calls/{id}` | Update title, project, participants |
| `DELETE` | `/calls/{id}` | Delete call and local audio file |
| `GET` | `/calls/{id}/export` | Download Markdown export |
| `GET` | `/calls/{id}/audio` | Stream WAV recording |
| `POST` | `/calls/{id}/reprocess` | Re-run transcription + summary |

### Projects

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/projects` | List projects |
| `POST` | `/projects` | Create project |
| `GET` | `/projects/{id}` | Project dashboard (aggregated next steps & decisions) |

### Recording

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/recording/status` | Current recording state snapshot |
| `POST` | `/recording/start` | Manual recording start |
| `POST` | `/recording/stop` | Manual recording stop |

### Real-time

| Protocol | Path | Description |
|----------|------|-------------|
| WebSocket | `/ws` | Live recording status and `call_ready` events |

### Planned

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/search` | Full-text search (returns 501 — planned for v2) |

## Testing

```bash
# Backend
uv run pytest backend/tests -v

# Frontend
cd frontend && npm test
```

## Project structure

```
calls-to-knowledge/
├── backend/
│   ├── main.py                 # FastAPI app, lifespan, processing pipeline
│   ├── config.py               # TOML config loader
│   ├── audio/                  # Monitor, recorder, state
│   ├── processing/             # Transcription, AI summarization
│   ├── db/                     # Supabase client + schema.sql
│   ├── api/routes/             # REST endpoints
│   ├── prompts/summary.yaml    # LLM system prompt
│   └── tests/
├── frontend/                   # React dashboard
├── config.toml.example         # Config template (copy → config.toml)
├── .env.example                # Secrets reference (app uses config.toml)
└── pyproject.toml
```

## License

Private / portfolio project. See repository owner for usage terms.
