# Mic Recording — Design Spec
**Data:** 2026-03-31
**Stato:** Approvato

---

## Panoramica

Aggiunge la registrazione del microfono locale in parallelo al loopback WASAPI già implementato. I due stream producono file WAV separati, sincronizzati per costruzione (partono nella stessa callback). La `TranscriptionService` li trascrive in parallelo e fa il merge dei segmenti per timestamp, aggiungendo il campo `speaker` (`"you"` / `"remote"`) a ogni segmento. Questo abilita la diarizzazione you/remote senza algoritmi, e prepara il terreno per la diarizzazione multi-speaker sui partecipanti remoti in futuro.

---

## Componenti

### `backend/audio/mic_recorder.py` — nuovo

Classe `MicRecorder` con la stessa interfaccia di `AudioRecorder`:

- `start(app_name: str) → None` — apre il default input device di Windows (`pyaudiowpatch`, nessuna config necessaria), avvia thread di registrazione
- `stop() → str | None` — ferma il thread, consolida il buffer finale, restituisce il path del WAV
- `is_recording: bool` — property

Formato output: WAV 16kHz mono, flush ogni 30s, path:
```
~/calls-to-knowledge/audio/YYYY-MM-DD_HH-MM_<app>_mic.wav
```

Usa `pyaudiowpatch` (già installato) per aprire il device di input standard — nessuna logica WASAPI loopback necessaria.

---

### `backend/processing/transcription.py` — modifica

Aggiunge il metodo:

```python
async def transcribe_call(
    self,
    loopback_path: str,
    mic_path: str | None,
) -> dict[str, Any]
```

Comportamento:
1. Se `mic_path` è `None`: logga `WARNING "Mic track not available, transcribing loopback only — speaker labels will be missing"` e trascrive solo il loopback (nessuna speaker label nei segmenti)
2. Se entrambi i path sono presenti: trascrive in parallelo con `asyncio.gather`, poi fa il merge dei segmenti
3. Il merge: unisce i segmenti del loopback (`speaker: "remote"`) e del mic (`speaker: "you"`), ordina per `start` timestamp

Output:
```python
{
    "full_text": str,      # testo interleaved con prefissi [REMOTE] / [YOU]
    "language": str,       # lingua rilevata dal loopback (fonte principale)
    "segments": [
        {"start": float, "end": float, "text": str, "speaker": "remote" | "you"},
        ...
    ]
}
```

Il metodo `transcribe(path)` esistente rimane invariato.

---

### Schema Supabase — migrazione

```sql
ALTER TABLE calls ADD COLUMN mic_path text;
```

La colonna `transcripts.segments` è già `jsonb` — il campo `speaker` viene salvato senza modifiche allo schema.

`SupabaseClient` non richiede modifiche: `update_call` accetta già un payload dict generico.

---

### `backend/main.py` — modifica

**`on_call_start`:** avvia entrambi i recorder:
```python
recorder.start(app_name)
mic_recorder.start(app_name)
```

**`on_call_end`:** ferma entrambi, aggiorna DB e avvia pipeline con entrambi i path:
```python
audio_path = recorder.stop()
mic_path = mic_recorder.stop()

await db.update_call(call_id, {
    "ended_at": ...,
    "duration_sec": ...,
    "audio_path": audio_path,
    "mic_path": mic_path,
    "status": "processing",
})
await pipeline(call_id, audio_path, mic_path)
```

**Firma `pipeline`:** cambia da `(call_id, audio_path)` a `(call_id, audio_path, mic_path)`. Internamente chiama `transcription.transcribe_call(audio_path, mic_path)`.

---

## Test

### Nuovo: `backend/tests/test_mic_recorder.py`
Mirror di `test_recorder.py`:
- Verifica che `stop()` senza `start()` ritorni `None`
- Verifica che venga creato un WAV con suffisso `_mic`
- Verifica che `is_recording` si aggiorni correttamente

### Aggiornamento: `backend/tests/test_transcription.py`
Nuovi test per `transcribe_call`:
- Segmenti del merge ordinati per timestamp
- Campo `speaker` corretto su ogni segmento (`"remote"` / `"you"`)
- Con `mic_path=None`: emette WARNING e ritorna segmenti senza speaker label

---

## Flusso Dati

```
on_call_start(app)
    │
    ├── recorder.start(app)       → loopback WAV (WASAPI)
    └── mic_recorder.start(app)   → mic WAV (default input)

on_call_end()
    │
    ├── recorder.stop()           → loopback_path
    ├── mic_recorder.stop()       → mic_path
    │
    └── pipeline(call_id, loopback_path, mic_path)
            │
            ├── transcribe_call(loopback_path, mic_path)
            │       ├── asyncio.gather(transcribe(loopback), transcribe(mic))
            │       └── merge segments by timestamp + speaker label
            │
            ├── save_transcript(full_text, merged_segments, language)
            └── ai_processor.process(full_text)
```

---

## Gestione Errori

| Scenario | Comportamento |
|---|---|
| Microfono non disponibile al momento di `start` | `MicRecorder` logga ERROR, `is_recording` rimane `False`, `stop()` ritorna `None` |
| `mic_path` è `None` a `transcribe_call` | WARNING nei log, trascrizione procede con solo loopback, nessuna speaker label |
| Mic si disconnette durante la registrazione | Il thread termina, `stop()` consolida il buffer parziale e ritorna il path |

---

## Fuori Scope

- Selezione manuale del dispositivo microfono (v2 via `config.toml`)
- Diarizzazione multi-speaker sui partecipanti remoti
- Visualizzazione del campo `speaker` nel frontend (già salvato in DB, UI può mostrarlo in futuro)
