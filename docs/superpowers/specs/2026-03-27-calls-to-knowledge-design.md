# Calls to Knowledge — Design Spec
**Data:** 2026-03-27
**Stato:** Approvato

---

## Panoramica

Sistema locale per Windows che rileva automaticamente le chiamate audio (Teams, Chrome Meet, Zoom, ecc.), le registra, le trascrive e genera summary strutturati. I risultati sono consultabili tramite un frontend web con storico e organizzazione per progetto. Ogni chiamata è esportabile in Markdown. Un overlay sempre visibile segnala quando la registrazione è attiva.

---

## Architettura

Tre processi indipendenti che comunicano tra loro:

| Processo | Tecnologia | Porta |
|---|---|---|
| Backend | Python + FastAPI | 8000 |
| Frontend | React + Vite | 5173 (dev) / servito da FastAPI (prod) |
| Overlay | Electron (solo overlay) | — |

**Il backend è il cuore del sistema.** Frontend e overlay sono client passivi: ricevono stato tramite WebSocket e chiamano REST API per leggere/scrivere dati.

```
Windows Audio Sessions (WASAPI)
        │
        ▼
  Audio Monitor ──► rileva chiamata ──► avvia Recorder
        │                                      │
        ▼                                      ▼
  WebSocket emit                        salva WAV 16kHz
        │                                      │
        ▼                               chiamata finisce
  Overlay: pallino                             │
  verde appare                                 ▼
                                     Transcription Service
                                       (OpenAI Whisper)
                                              │
                                              ▼
                                       AI Processor
                                       (GPT-5 mini)
                                              │
                                              ▼
                                         Supabase (PostgreSQL)
                                              │
                                              ▼
                                     WebSocket notify ──► Frontend aggiorna
```

---

## Componenti Backend

### Audio Monitor
- Usa `pycaw` per interrogare le sessioni audio Windows attive ogni secondo
- Confronta i processi attivi con una **whitelist configurabile**: `Teams.exe`, `chrome.exe`, `msedge.exe`, `zoom.exe`, `slack.exe`, `webex.exe`
- Considera una chiamata valida solo dopo **15 secondi continui di audio** (soglia anti-falsi-positivi)
- Quando rileva una chiamata: avvia Recorder, emette evento WebSocket `recording_status` con `status="recording"`, salva record in SQLite con `status = recording`

### Audio Recorder
- Cattura audio di sistema tramite **loopback** con `pyaudiowpatch` (fork di pyaudio con supporto WASAPI loopback su Windows)
- Formato: WAV, 16kHz, mono — ottimale per Whisper
- Bufferizza l'audio e scarica su disco ogni 30 secondi (resilienza ai crash — se il backend si chiude a metà call, il file parziale è preservato)
- Path finale: `~/calls-to-knowledge/audio/YYYY-MM-DD_HH-MM_<app>.wav`
- Alla fine della chiamata: consolida il buffer finale, aggiorna Supabase, avvia pipeline di processing

### Transcription Service
- Provider configurabile via `config.toml`: `openai` (default) o `local`
- **OpenAI:** chiama `POST /audio/transcriptions` con modello `whisper-1`. Restituisce testo + segmenti con timestamp
- **Locale:** usa `faster-whisper` con modello `medium` quantizzato (funziona anche senza GPU)
- Salva `full_text` e array `segments` in tabella `transcripts` su Supabase

### AI Processor
- Modello: **GPT-5 mini** (OpenAI API)
- Input: trascrizione completa
- Output: JSON strutturato con campi:
  - `title` — titolo breve auto-generato
  - `summary` — 3-5 frasi
  - `key_points` — lista di punti chiave
  - `next_steps` — lista con responsabile se menzionato nel testo
  - `decisions` — decisioni prese durante la call
- Il prompt è in italiano di default, rilevamento lingua automatico da Whisper

### REST API (FastAPI)
Endpoint principali:

| Metodo | Path | Descrizione |
|---|---|---|
| GET | `/calls` | Lista chiamate con filtri (project_id, search, limit, offset) |
| GET | `/calls/{id}` | Dettaglio chiamata con transcript e summary |
| PATCH | `/calls/{id}` | Aggiorna titolo, project_id, partecipanti |
| DELETE | `/calls/{id}` | Elimina chiamata e file audio |
| GET | `/projects` | Lista progetti |
| POST | `/projects` | Crea progetto |
| GET | `/projects/{id}` | Dashboard progetto (chiamate + next steps aggregati) |
| POST | `/recording/start` | Override manuale: avvia registrazione |
| POST | `/recording/stop` | Override manuale: ferma registrazione |
| GET | `/recording/status` | Stato corrente (idle / recording / processing) |
| GET | `/search?q=...` | Ricerca full-text nelle trascrizioni via FTS5 |
| POST | `/calls/{id}/reprocess` | Riavvia trascrizione + AI su una call in stato error |
| GET | `/calls/{id}/export` | Scarica summary + trascrizione in formato Markdown |

### WebSocket
- Endpoint: `ws://localhost:8000/ws`
- Evento `recording_status`: `{ status: "recording"|"processing"|"idle", app, duration_sec }`
- Evento `call_ready`: `{ call_id }` — notifica quando processing è completato

---

## Modello Dati (Supabase — PostgreSQL)

### Tabella `projects`
| Campo | Tipo | Note |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | |
| description | TEXT | nullable |
| created_at | DATETIME | |

### Tabella `calls`
| Campo | Tipo | Note |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK | nullable — assegnabile dopo |
| title | TEXT | auto-generato da GPT-5 mini, modificabile |
| source_app | TEXT | es. "Teams", "Chrome" |
| started_at | DATETIME | |
| ended_at | DATETIME | nullable durante registrazione |
| duration_sec | INTEGER | |
| audio_path | TEXT | path locale al file WAV |
| status | TEXT | `recording` / `processing` / `done` / `error` |
| participants | JSON | array di nomi, editabile manualmente |
| recording_trigger | TEXT | `auto` / `manual` |
| updated_at | DATETIME | aggiornato ad ogni PATCH |

### Tabella `transcripts`
| Campo | Tipo | Note |
|---|---|---|
| id | INTEGER PK | |
| call_id | INTEGER FK | |
| full_text | TEXT | trascrizione completa |
| segments | JSON | `[{start, end, text}]` da Whisper |
| language | TEXT | rilevato automaticamente |
| created_at | DATETIME | |

### Tabella `summaries`
| Campo | Tipo | Note |
|---|---|---|
| id | INTEGER PK | |
| call_id | INTEGER FK | |
| summary | TEXT | |
| key_points | JSON | array di stringhe |
| next_steps | JSON | array di stringhe |
| decisions | JSON | array di stringhe |
| created_at | DATETIME | |

### Note Supabase
- Il backend usa `supabase-py` per tutte le operazioni CRUD
- I tipi JSON (`participants`, `segments`, `key_points`, ecc.) sono colonne `jsonb` in PostgreSQL
- Row Level Security (RLS) disabilitato — accesso solo dal backend tramite `service_role_key`

---

## Frontend (React + Vite)

### Schermate

**Storico Chiamate** (schermata principale)
- Tabella con colonne: Chiamata (titolo + anteprima summary), Progetto, Sorgente, Durata, Data
- Filtri per progetto nella toolbar
- Badge con contatore totale chiamate
- Riga in stato `processing` evidenziata con indicatore di avanzamento

**Dettaglio Chiamata**
- Header: titolo (modificabile inline), metadati, bottone play audio
- Sezioni: Summary, Key Points, Next Steps, Decisions
- Trascrizione completa espandibile
- Dropdown per assegnare/cambiare progetto
- Bottone "Scarica Markdown" — chiama `GET /calls/{id}/export` e scarica file `.md`

**Dashboard Progetto**
- Header: nome progetto, totale chiamate, ore totali
- Counter card: chiamate, next steps, decisioni
- Lista aggregata di tutti i next steps del progetto (con data provenienza)
- Lista chiamate del progetto in ordine cronologico

### Comunicazione
- REST API per lettura/scrittura dati
- WebSocket per aggiornamenti in tempo reale (stato recording, call_ready)

---

## Overlay (Electron)

Finestra Electron con `alwaysOnTop: true`, `transparent: true`, `frame: false`. Posizionata in basso a destra. Draggable.

**Stato minimale:** pallino colorato + timer in monospace
- 🟢 Verde: registrazione attiva
- 🟡 Giallo: elaborazione in corso
- ⚫ Grigio/nascosto: inattivo

**Stato espanso** (click sul badge):
- Nome app rilevata (es. "Microsoft Teams")
- Timer
- Bottone "Ferma registrazione"

L'overlay si connette al WebSocket del backend e aggiorna lo stato in base agli eventi `recording_status`.

---

## Configurazione

File `config.toml` nella directory dell'app:

```toml
[openai]
api_key = ""                 # usata da trascrizione e AI processor

[transcription]
provider = "openai"          # "openai" | "local"
local_model = "medium"       # usato solo se provider = "local"

[ai]
model = "gpt-5-mini"

[supabase]
url = ""                     # es. https://xxxx.supabase.co
anon_key = ""                # chiave pubblica (Settings → API → anon public)
service_role_key = ""        # chiave privata (Settings → API → service_role secret)

[recording]
min_duration_seconds = 15
call_apps = ["Teams.exe", "chrome.exe", "msedge.exe", "zoom.exe", "slack.exe", "webex.exe"]
audio_dir = "~/calls-to-knowledge/audio"

[server]
host = "127.0.0.1"
port = 8000
```

---

## Gestione Errori

| Scenario | Comportamento |
|---|---|
| Backend riavviato durante registrazione | Al riavvio, cerca call con `status = recording` e completa il processing |
| Whisper API non raggiungibile | Salva la call con `status = error`, riprova via `POST /calls/{id}/reprocess` |
| GPT-5 mini fallisce | Salva la trascrizione comunque, summary vuoto, riprova via `POST /calls/{id}/reprocess` |
| File audio corrotto | Log errore, `status = error`, audio path preservato per debug |
| Overlay perde connessione WebSocket | Riconnessione automatica ogni 3 secondi |
| Supabase non raggiungibile | Il recording continua localmente, il salvataggio riprova con backoff esponenziale |

---

## Struttura Directory

```
calls-to-knowledge/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Lettura config.toml
│   ├── audio/
│   │   ├── monitor.py           # WASAPI session monitor
│   │   └── recorder.py          # Loopback recorder
│   ├── processing/
│   │   ├── transcription.py     # Whisper (openai + local)
│   │   └── ai_processor.py      # GPT-5 mini summary
│   ├── api/
│   │   ├── routes/
│   │   │   ├── calls.py
│   │   │   ├── projects.py
│   │   │   ├── recording.py
│   │   │   └── search.py
│   │   └── websocket.py
│   └── db/
│       └── supabase_client.py   # Inizializzazione client supabase-py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── CallsList.tsx
│   │   │   ├── CallDetail.tsx
│   │   │   └── ProjectDashboard.tsx
│   │   ├── components/
│   │   └── hooks/
│   │       └── useWebSocket.ts
│   └── vite.config.ts
├── overlay/
│   ├── main.js                  # Electron main process
│   ├── preload.js
│   └── renderer/                # HTML/CSS/JS overlay UI
├── config.toml
└── README.md
```

---

## Fuori Scope (v1)

- Ricerca full-text nelle trascrizioni (implementata in v2 tramite PostgreSQL FTS)
- Diarizzazione (identificazione automatica di chi parla)
- Filtro audio per sorgente specifica (escludere musica di sottofondo)
- App mobile
- Integrazione calendario (rilevamento automatico nome meeting)

## Ordine di Implementazione

Il progetto viene sviluppato e validato un componente alla volta:

1. **Backend** — Audio Monitor + Recorder + Transcription + AI Processor + REST API + WebSocket
2. **Frontend** — Storico chiamate + Dettaglio + Dashboard progetto + Export Markdown
3. **Overlay** — Electron always-on-top con WebSocket
