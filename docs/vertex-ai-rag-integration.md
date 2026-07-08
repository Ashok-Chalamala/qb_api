# Vertex AI RAG Chatbot Integration — Developer Guide

**Service:** Quest Beyond API  
**Module:** `app/routers/vertex_chat.py`  
**Base path:** `/ai`  
**Model:** Google Gemini (via Vertex AI)  
**Pattern:** Traditional Retrieval-Augmented Generation (RAG)  
**Auth:** GCP Service Account (Application Default Credentials)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [RAG Pipeline — How It Works](#2-rag-pipeline--how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [GCP Setup — One-Time Steps](#4-gcp-setup--one-time-steps)
5. [Environment Variables](#5-environment-variables)
6. [Starting the Server](#6-starting-the-server)
7. [API Reference](#7-api-reference)
8. [Request & Response Examples](#8-request--response-examples)
9. [Patient Context Sections](#9-patient-context-sections)
10. [System Prompt & Grounding Rules](#10-system-prompt--grounding-rules)
11. [Available Gemini Models](#11-available-gemini-models)
12. [Error Reference](#12-error-reference)
13. [Genie Chat Integration (existing endpoint)](#13-genie-chat-integration-existing-endpoint)
14. [Limitations & Production Notes](#14-limitations--production-notes)

---

## 1. Architecture Overview

```
Frontend
   │
   │  POST /ai/chat  { "patient_id": "patient-00429", "message": "..." }
   ▼
Quest Beyond API
   │
   ├─ 1. _build_patient_context(patient_id)
   │      Fetches from in-memory stores:
   │      profile · dashboard · alerts · vitals · trends
   │      timeline · symptoms · wellbeing · devices · weekly glucose
   │      → ~2,000-char plain-text CONTEXT block
   │
   ├─ 2. Inject context into RAG system prompt
   │      "Answer ONLY from the PATIENT CONTEXT below..."
   │
   ├─ 3. _call_gemini(history, system_prompt)
   │      Vertex AI → gemini-2.0-flash-001
   │
   ├─ 4. _format_response(text)
   │      Normalise bullet styles, collapse whitespace
   │
   └─ 5. Return ChatResponse
          { response, model, grounded_on, usage }
   │
   ▼
Frontend renders formatted response
```

---

## 2. RAG Pipeline — How It Works

Traditional RAG replaces a vector database with a **live structured context block** assembled directly from the patient's health records on every request.

| RAG step | Implementation |
|----------|---------------|
| **Retrieval** | `_build_patient_context()` pulls from `app/stores.py` and `app/data/patients.py` |
| **Context window** | ~2,000 chars of structured plain text injected into the system prompt |
| **Grounding** | System prompt instructs Gemini to answer *only* from the provided context |
| **Generation** | `vertexai.generative_models.GenerativeModel.start_chat().send_message()` |
| **Formatting** | `_format_response()` normalises bullet characters and whitespace |

**Why no vector DB?** Patient health records are small, structured, and change frequently. Embedding + similarity search would add latency and complexity with no benefit over direct structured retrieval at this data size.

---

## 3. Prerequisites

### Python packages

```
google-cloud-aiplatform>=1.60.0
```

Already in `requirements.txt`. Install:
```powershell
python -m pip install -r requirements.txt
```

### GCP requirements

- A GCP project with **Vertex AI API** enabled
- A **Service Account** with the `Vertex AI User` role
- A downloaded **Service Account JSON key file**

---

## 4. GCP Setup — One-Time Steps

### Step 1 — Enable the Vertex AI API

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select project **questbeyond**
3. **APIs & Services → Library**
4. Search **"Vertex AI API"** → Enable

### Step 2 — Create a Service Account

1. **IAM & Admin → Service Accounts → Create Service Account**
2. Name: `questbeyond-vertex-sa` (or any name)
3. Click **Create and Continue**

### Step 3 — Grant the required role

On the Service Account, click **Grant Access** and add:
- Role: **Vertex AI User** (`roles/aiplatform.user`)

### Step 4 — Download the JSON key

1. Click the Service Account → **Keys** tab
2. **Add Key → Create new key → JSON**
3. Save the downloaded file — for example:  
   `C:\vivek\Lifelabs\QuestBeyond\sa-key.json`

> **Security:** Never commit the key file to source control. Add it to `.gitignore`.

---

## 5. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | ✅ | — | Absolute path to the Service Account JSON key file |
| `VERTEX_PROJECT` | ✅ | — | GCP project ID (e.g. `questbeyond`) |
| `VERTEX_LOCATION` | ❌ | `us-central1` | GCP region for Vertex AI endpoint |
| `VERTEX_MODEL` | ❌ | `gemini-2.0-flash-001` | Gemini model name |

Set in PowerShell:
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\vivek\Lifelabs\QuestBeyond\sa-key.json"
$env:VERTEX_PROJECT                  = "questbeyond"
$env:VERTEX_LOCATION                 = "us-central1"       # optional
$env:VERTEX_MODEL                    = "gemini-2.0-flash-001"  # optional
```

---

## 6. Starting the Server

```powershell
cd C:\vivek\Lifelabs\QuestBeyond\qb_api-main

$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\sa-key.json"
$env:VERTEX_PROJECT = "questbeyond"

python -m uvicorn main:app --reload --port 8001
```

Verify Vertex AI routes loaded:
```
INFO:     Started server process
INFO:     Application startup complete.
```

Check routes at: `http://localhost:8001/docs` → scroll to **vertex-ai-chat** section.

---

## 7. API Reference

### `POST /ai/chat`
**Single-turn RAG chat — stateless.**  
Each call independently retrieves fresh patient context and queries Gemini.  
No conversation history is retained between calls.

#### Request body

```json
{
  "patient_id": "patient-00429",
  "message": "Why has my glucose been so high this week?"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `patient_id` | string | ✅ | Must match an existing patient (see patient IDs below) |
| `message` | string | ✅ | The patient's question |
| `session_id` | string | ❌ | Ignored for this endpoint |

#### Response `200`

```json
{
  "response": "Your glucose has been elevated this week, reaching 234 mg/dL on fasting readings...\n\n• Your 7-day trend shows a rise from 138 → 234 mg/dL\n• Active alerts: Glucose >200 for 3 consecutive days\n\nNext step: Contact your care team to review your readings.",
  "session_id": null,
  "turn": null,
  "model": "gemini-2.0-flash-001",
  "grounded_on": ["profile", "dashboard", "alerts", "vitals", "trends", "timeline", "devices", "weekly_glucose"],
  "usage": {
    "prompt_tokens": 842,
    "output_tokens": 124,
    "total_tokens": 966
  }
}
```

---

### `POST /ai/chat/session`
**Multi-turn RAG chat — with conversation memory.**  
Maintains full conversation history within a session.  
Patient context is **re-fetched on every turn** so Gemini always sees fresh data.

#### Request body

```json
{
  "patient_id": "patient-00429",
  "message": "What about my sleep?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `patient_id` | string | ✅ | Patient ID |
| `message` | string | ✅ | Patient's message |
| `session_id` | string | ❌ | Omit to start a new session; include to continue |

#### Response `200`

```json
{
  "response": "Your sleep has averaged 4.5 hours this week, below the recommended 7-8 hours...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "turn": 2,
  "model": "gemini-2.0-flash-001",
  "grounded_on": ["profile", "dashboard", "alerts", "vitals", "trends", "timeline", "devices", "weekly_glucose"],
  "usage": { "prompt_tokens": 1044, "output_tokens": 98, "total_tokens": 1142 }
}
```

> **Frontend pattern:** Store the returned `session_id` and send it on all follow-up messages to maintain conversation context.

---

### `GET /ai/chat/session/{session_id}/history`
Retrieve the full conversation history for a session.

**Response `200`:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "turns": 2,
  "messages": [
    { "role": "user",  "content": "Why has my glucose been so high?" },
    { "role": "model", "content": "Your glucose has been elevated..." },
    { "role": "user",  "content": "What about my sleep?" },
    { "role": "model", "content": "Your sleep has averaged 4.5 hours..." }
  ]
}
```

---

### `DELETE /ai/chat/session/{session_id}`
Clear a session and its conversation history.

**Response:** `204 No Content`

---

### `GET /ai/models`
List available Gemini models and show current configuration + setup instructions.

**Response `200`:**
```json
{
  "configured_model": "gemini-2.0-flash-001",
  "project": "questbeyond",
  "location": "us-central1",
  "setup": {
    "step_1": "Download Service Account JSON from GCP Console → IAM → Service Accounts → Keys",
    "step_2": "Grant the SA the 'Vertex AI User' role",
    "step_3": "Set env: GOOGLE_APPLICATION_CREDENTIALS=<path-to-sa-key.json>",
    "step_4": "Set env: VERTEX_PROJECT=questbeyond"
  },
  "available_models": [...]
}
```

---

## 8. Request & Response Examples

### Example 1 — Single-turn question about glucose

```bash
curl -X POST http://localhost:8001/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-00429",
    "message": "Why has my glucose been elevated this week?"
  }'
```

### Example 2 — Start a multi-turn session

```bash
# Turn 1 — start new session (no session_id)
curl -X POST http://localhost:8001/ai/chat/session \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-00429",
    "message": "Give me a summary of my health this week"
  }'

# Response includes: "session_id": "abc-123-..."

# Turn 2 — continue the same session
curl -X POST http://localhost:8001/ai/chat/session \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-00429",
    "message": "Which alert is the most urgent?",
    "session_id": "abc-123-..."
  }'
```

### Example 3 — Fetch history then clear

```bash
# Get history
curl http://localhost:8001/ai/chat/session/abc-123-.../history

# Clear session
curl -X DELETE http://localhost:8001/ai/chat/session/abc-123-...
```

---

## 9. Patient Context Sections

The following sections are assembled by `_build_patient_context()` and injected into every Gemini call. The `grounded_on` field in the response lists which sections were included.

| Section key | Source | Content |
|-------------|--------|---------|
| `profile` | `USERS` dict | Name, MRN, age, primary condition |
| `dashboard` | `_SARAH_PAGE_DATA` | Health score, active alerts count, steps today, latest glucose + forecast |
| `alerts` | `_SARAH_PAGE_DATA.alertsData` | Active alerts with severity and description |
| `vitals` | `_PATIENT_METRICS` store | Last 7 vitals readings (BP, blood sugar, HR, weight, SpO2) |
| `trends` | `_SARAH_PAGE_DATA.metricTrends` | 14-day glucose, steps, and health score arrays |
| `timeline` | `_SARAH_PAGE_DATA.timelineData` | Last 3 days of timeline events from all data sources |
| `symptoms` | `_SYMPTOMS_STORE` | Last 5 logged symptom entries |
| `wellbeing` | `_WELLBEING_STORE` | Last 5 wellbeing log entries |
| `devices` | `_DEVICES_STORE` | Connected devices with status and last sync time |
| `weekly_glucose` | `_SARAH_PAGE_DATA.weeklyTrend` | 7-day glucose values by day-of-week |

Sections with no data (empty store) are automatically omitted.

---

## 10. System Prompt & Grounding Rules

The RAG system prompt enforces strict grounding. Key rules sent to Gemini on every call:

```
1. Answer ONLY from the PATIENT CONTEXT below.
   Do NOT use external medical knowledge or assumptions.

2. If the answer is not in the context:
   "I don't have enough data in your health records to answer that.
    Please consult your care team."

3. Never diagnose or prescribe medications.

4. Speak in plain language — no clinical jargon.

5. If a medical emergency is detected in the message:
   "This sounds like it may need urgent care.
    Please call 911 or go to the nearest emergency room."

6. Keep responses under 200 words. Use bullet points for clarity.

7. Always end with one "Next step" suggestion.
```

**Response format enforced:**
1. One-sentence direct answer
2. Supporting evidence quoted from patient context
3. "Next step" suggestion

To modify the grounding rules, edit `_RAG_SYSTEM_PROMPT` in `app/routers/vertex_chat.py`.

---

## 11. Available Gemini Models

| Model name | Speed | Best for |
|------------|-------|----------|
| `gemini-2.0-flash-001` | ⚡ Fastest | Default — recommended for real-time chat |
| `gemini-2.0-pro-001` | Moderate | Complex clinical reasoning, longer answers |
| `gemini-1.5-flash-002` | Fast | Large context window (1M tokens) |
| `gemini-1.5-pro-002` | Slow | Most capable, 2M token context |

Switch model without code change:
```powershell
$env:VERTEX_MODEL = "gemini-2.0-pro-001"
```

---

## 12. Error Reference

| HTTP Status | Cause | Resolution |
|-------------|-------|------------|
| `503` — `google-cloud-aiplatform not installed` | Package missing | `python -m pip install google-cloud-aiplatform` |
| `503` — `VERTEX_PROJECT env var not set` | Missing config | Set `VERTEX_PROJECT` and `GOOGLE_APPLICATION_CREDENTIALS` env vars |
| `403` from Vertex AI | SA lacks Vertex AI User role | Add role in GCP IAM |
| `404` — Session not found | `session_id` does not exist or was cleared | Start a new session (omit `session_id`) |
| `404` — Patient not found | `patient_id` not in stores | Use `patient-00429` or `patient-00312` |

If Vertex AI is not configured, the `/patients/{id}/genie/chat` endpoint automatically falls back to a mock response — **no error is returned to the frontend**.

---

## 13. Genie Chat Integration (existing endpoint)

The existing `POST /patients/{patient_id}/genie/chat` endpoint also uses the RAG pipeline when Vertex AI is configured:

```json
POST /patients/patient-00429/genie/chat
{
  "message": "Why is my glucose so high?",
  "conversationId": "conv-001"
}
```

**Response when Vertex AI is active:**
```json
{
  "response": "Your glucose trend shows a rise from 138 to 234 mg/dL...",
  "conversationId": "conv-001",
  "model": "gemini-2.0-flash-001",
  "groundedOn": ["profile", "dashboard", "alerts", "vitals", "trends", "timeline", "devices", "weekly_glucose"],
  "suggestedActions": [],
  "usage": { "prompt_tokens": 842, "output_tokens": 96, "total_tokens": 938 }
}
```

**Response when Vertex AI is NOT configured (fallback):**
```json
{
  "response": "Thanks for your message: '...'\n\nBased on your recent data, I can see glucose has been elevated...",
  "conversationId": "conv-001",
  "suggestedActions": ["schedule_telehealth", "log_meal"],
  "confidence": 0.88
}
```

The `conversationId` maps to a session in `_SESSIONS` — conversation history is shared between `/genie/chat` and `/ai/chat/session`.

---

## 14. Limitations & Production Notes

| Concern | Current behaviour | Production recommendation |
|---------|-------------------|--------------------------|
| **Session storage** | In-memory dict — lost on restart | Store sessions in Redis with TTL |
| **Context size** | ~2,000 chars (8 sections) | For large patient histories, implement semantic chunking |
| **No vector embeddings** | Context is raw structured text | Add embedding-based retrieval if unstructured notes are added |
| **Token cost** | ~800-1000 tokens per request | Cache context for 60s per patient to reduce API calls |
| **Model availability** | `gemini-2.0-flash-001` | Verify model is available in your `VERTEX_LOCATION` region |
| **SA key file** | Stored on disk | Use GCP Workload Identity (for GKE) or Secret Manager in production |
| **No auth on `/ai/*`** | Endpoints are open | Add JWT/Bearer token validation matching the existing `/auth/login` flow |
| **Rate limits** | Vertex AI: 60 QPM on flash | Implement request queuing for high-traffic scenarios |

---

## Known Patient IDs (development)

| Patient | `patient_id` | Condition |
|---------|-------------|-----------|
| Sarah Martinez | `patient-00429` | Type 2 Diabetes |
| James Lee | `patient-00312` | Hypertension |
