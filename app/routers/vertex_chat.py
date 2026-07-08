"""
Vertex AI Gemini — RAG Health Chatbot for Quest Beyond.

Architecture (traditional RAG):
  1. Patient query arrives at POST /ai/chat or POST /ai/chat/session
  2. Patient's live health records are fetched from in-memory stores
     (profile, vitals, metrics, alerts, timeline, symptoms, wellbeing, devices)
  3. Records are serialised into a plain-text CONTEXT block
  4. A strict grounded system prompt tells Gemini: answer ONLY from the context
  5. Gemini returns a response; the router formats it and returns JSON

Authentication (one-step setup):
  Download a GCP Service Account JSON key from:
    https://console.cloud.google.com → IAM → Service Accounts → Keys → Add Key
  Grant the SA the "Vertex AI User" role, then set:
    $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\\path\\to\\sa-key.json"
    $env:VERTEX_PROJECT = "questbeyond"   # your GCP project ID

Endpoints:
  POST   /ai/chat                        – single-turn RAG chat (stateless)
  POST   /ai/chat/session                – multi-turn RAG chat (session memory)
  GET    /ai/chat/session/{id}/history   – conversation history
  DELETE /ai/chat/session/{id}           – clear session
  GET    /ai/models                      – list Gemini models
"""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["vertex-ai-chat"])

# ── Configuration ──────────────────────────────────────────────────────────────

VERTEX_PROJECT: str = os.environ.get("VERTEX_PROJECT", "")
VERTEX_LOCATION: str = os.environ.get("VERTEX_LOCATION", "us-central1")
VERTEX_MODEL: str = os.environ.get("VERTEX_MODEL", "gemini-2.0-flash-001")

# ── In-memory conversation store: { session_id: [{"role": str, "content": str}] }
_SESSIONS: dict[str, list[dict]] = {}

# ── Pydantic models ────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    patient_id: str
    message: str
    session_id: Optional[str] = None  # only used by /ai/chat/session


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    turn: Optional[int] = None
    model: str
    grounded_on: list[str]       # which data sections were included in context
    usage: Optional[dict] = None


# ── RAG: Patient context builder ───────────────────────────────────────────────

def _build_patient_context(patient_id: str) -> tuple[str, list[str]]:
    """
    Fetches all available patient data from the in-memory stores and
    serialises it into a plain-text CONTEXT block for the RAG prompt.

    Returns:
        context_text  – the full context string to inject into the prompt
        sections_used – list of section names included (for response metadata)
    """
    from app.data.patients import USERS, _SARAH_PAGE_DATA, _MEMBER_DATA_MAP
    from app.stores import (
        _PATIENT_METRICS, _DEVICES_STORE, _REPORTS_STORE,
        _SYMPTOMS_STORE, _WELLBEING_STORE, _SETTINGS_STORE,
    )

    lines: list[str] = []
    sections: list[str] = []

    # ── 1. Profile ─────────────────────────────────────────────────────────────
    user = next((u for u in USERS.values() if u["id"] == patient_id), None)
    if user:
        lines += [
            "## Patient Profile",
            f"Name: {user['fullName']}",
            f"MRN: {user['mrn']}",
            f"Age: {user['age']}",
            f"Primary Condition: {user['condition']}",
        ]
        sections.append("profile")

    # ── 2. Dashboard snapshot ──────────────────────────────────────────────────
    page = _SARAH_PAGE_DATA if patient_id == "patient-00429" else _MEMBER_DATA_MAP.get(patient_id)
    if page and "dashboard" in page:
        d = page["dashboard"]
        lines += [
            "",
            "## Dashboard Snapshot",
            f"Health Score: {d.get('healthScore', 'N/A')} / 100",
            f"Active Alerts: {d.get('activeAlerts', 0)}",
            f"Steps Today: {d.get('stepsToday', 0)} / {d.get('stepsGoal', 0)} goal",
            f"Latest Glucose: {d.get('glucoseLatest', 'N/A')} {d.get('glucoseUnit', '')} (Trend: {d.get('glucoseTrend', '')})",
        ]
        if "forecast" in d:
            f = d["forecast"]
            lines.append(f"Glucose Forecast: peak {f.get('peak')} mg/dL, risk score {f.get('risk')}%, trend {f.get('trend')}")
        sections.append("dashboard")

    # ── 3. Active alerts ───────────────────────────────────────────────────────
    if page and "alertsData" in page:
        lines += ["", "## Active Alerts"]
        for a in page["alertsData"]:
            lines.append(f"[{a.get('severity','?')}] {a.get('title','')}: {a.get('description','')}")
        sections.append("alerts")

    # ── 4. Vitals metrics (last 7 entries) ─────────────────────────────────────
    metrics = _PATIENT_METRICS.get(patient_id, [])
    if metrics:
        lines += ["", "## Recent Vitals (latest first)"]
        for m in metrics[:7]:
            parts = [f"Date: {m.get('date','')}"]
            if m.get("bloodPressure"):  parts.append(f"BP: {m['bloodPressure']}")
            if m.get("bloodSugar"):     parts.append(f"Blood Sugar: {m['bloodSugar']} mg/dL")
            if m.get("heartRate"):      parts.append(f"HR: {m['heartRate']} bpm")
            if m.get("weight"):         parts.append(f"Weight: {m['weight']} lbs")
            if m.get("oxygenSaturation"): parts.append(f"SpO2: {m['oxygenSaturation']}%")
            if m.get("notes"):          parts.append(f"Note: {m['notes']}")
            lines.append("  " + " | ".join(parts))
        sections.append("vitals")

    # ── 5. Glucose / metric 14-day trend ──────────────────────────────────────
    if page and "metricTrends" in page:
        t = page["metricTrends"]
        if "glucose" in t:
            lines += ["", "## 14-Day Glucose Trend (oldest → newest, mg/dL)",
                      "  " + " → ".join(str(v) for v in t["glucose"])]
        if "steps" in t:
            lines += ["## 14-Day Step Count Trend",
                      "  " + " → ".join(str(v) for v in t["steps"])]
        if "health" in t:
            lines += ["## 14-Day Health Score Trend",
                      "  " + " → ".join(str(v) for v in t["health"])]
        sections.append("trends")

    # ── 6. Recent timeline events ──────────────────────────────────────────────
    if page and "timelineData" in page:
        lines += ["", "## Recent Timeline Events"]
        for day in page["timelineData"][:3]:
            lines.append(f"\n{day.get('date', '')}:")
            for ev in day.get("events", []):
                detail = f" ({ev['detail']})" if ev.get("detail") else ""
                severity = f" [{ev['severity']}]" if ev.get("severity") else ""
                lines.append(f"  {ev.get('time','')} — {ev.get('title','')}{detail}{severity}")
        sections.append("timeline")

    # ── 7. Symptom log (last 5) ────────────────────────────────────────────────
    symptoms = _SYMPTOMS_STORE.get(patient_id, [])
    if symptoms:
        lines += ["", "## Symptom Log (recent)"]
        for s in symptoms[-5:]:
            lines.append(f"  {s.get('date','')}: {s.get('symptom','')} severity {s.get('severity','')} — {s.get('notes','')}")
        sections.append("symptoms")

    # ── 8. Wellbeing log (last 5) ─────────────────────────────────────────────
    wellbeing = _WELLBEING_STORE.get(patient_id, [])
    if wellbeing:
        lines += ["", "## Wellbeing Log (recent)"]
        for w in wellbeing[-5:]:
            lines.append(f"  {w.get('date','')}: mood {w.get('mood','')} energy {w.get('energy','')} sleep {w.get('sleep','')}h — {w.get('notes','')}")
        sections.append("wellbeing")

    # ── 9. Connected devices ───────────────────────────────────────────────────
    devices = _DEVICES_STORE.get(patient_id, [])
    if devices:
        lines += ["", "## Connected Devices"]
        for dv in devices:
            lines.append(f"  {dv.get('name','')} ({dv.get('type','')}) — Status: {dv.get('status','')}, Last sync: {dv.get('lastSync','')}")
        sections.append("devices")

    # ── 10. Weekly glucose trend ───────────────────────────────────────────────
    if page and "weeklyTrend" in page:
        lines += ["", "## 7-Day Glucose (mg/dL by day)"]
        lines.append("  " + "  ".join(f"{e['day']}: {e['value']}" for e in page["weeklyTrend"]))
        sections.append("weekly_glucose")

    return "\n".join(lines), sections


# ── System prompt (strict RAG grounding) ──────────────────────────────────────

_RAG_SYSTEM_PROMPT = """\
You are Genie, the AI health assistant built into Quest Beyond — a patient health management platform.

STRICT RULES — follow every rule without exception:
1. Answer ONLY using information contained in the PATIENT CONTEXT section below.
   Do NOT use any external medical knowledge, general facts, or assumptions.
2. If the answer cannot be found in the context, say exactly:
   "I don't have enough data in your health records to answer that. Please consult your care team."
3. Never diagnose, prescribe, or recommend specific medications.
4. Speak in plain language — avoid clinical jargon.
5. If you detect a possible medical emergency in the user's message, immediately say:
   "This sounds like it may need urgent care. Please call 911 or go to the nearest emergency room."
6. Keep responses concise (under 200 words). Use bullet points for clarity where helpful.
7. Always end with one suggested follow-up action when relevant (e.g. "You may want to log this symptom" or "Consider contacting your care team").

RESPONSE FORMAT:
- Start with a 1-sentence direct answer to the question.
- Follow with supporting evidence pulled from the PATIENT CONTEXT (quote specific values).
- End with a brief "Next step" suggestion.

---PATIENT CONTEXT---
{context}
---END CONTEXT---
"""


# ── Vertex AI helpers ──────────────────────────────────────────────────────────

_vertex_initialised = False


def _get_client():
    global _vertex_initialised
    if _vertex_initialised:
        return
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel  # noqa: F401
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="google-cloud-aiplatform not installed. Run: python -m pip install google-cloud-aiplatform",
        )
    if not VERTEX_PROJECT:
        raise HTTPException(
            status_code=503,
            detail=(
                "VERTEX_PROJECT env var not set. "
                "Set it to your GCP project ID (e.g. 'questbeyond'). "
                "Also set GOOGLE_APPLICATION_CREDENTIALS to the path of your service account JSON key."
            ),
        )
    vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
    _vertex_initialised = True


def _call_gemini(
    history: list[dict],  # [{"role": "user"|"model", "content": str}]
    system_prompt: str,
) -> tuple[str, dict]:
    from vertexai.generative_models import Content, GenerativeModel, Part, SystemInstruction

    model = GenerativeModel(
        model_name=VERTEX_MODEL,
        system_instruction=SystemInstruction(parts=[Part.from_text(system_prompt)]),
    )
    vertex_history = [
        Content(
            role="user" if m["role"] == "user" else "model",
            parts=[Part.from_text(m["content"])],
        )
        for m in history[:-1]
    ]
    chat = model.start_chat(history=vertex_history)
    raw = chat.send_message(history[-1]["content"])

    text = raw.text.strip()
    usage = {}
    if hasattr(raw, "usage_metadata") and raw.usage_metadata:
        um = raw.usage_metadata
        usage = {
            "prompt_tokens": getattr(um, "prompt_token_count", None),
            "output_tokens": getattr(um, "candidates_token_count", None),
            "total_tokens": getattr(um, "total_token_count", None),
        }
    return text, usage


def _format_response(text: str) -> str:
    """Light formatting pass — ensure consistent bullet style and spacing."""
    lines = text.splitlines()
    formatted = []
    for line in lines:
        stripped = line.strip()
        # Normalise various bullet styles to "• "
        if stripped.startswith(("- ", "* ", "· ")):
            stripped = "• " + stripped[2:]
        formatted.append(stripped)
    # Collapse 3+ blank lines to 2
    result = []
    blank_count = 0
    for line in formatted:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    return "\n".join(result)


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse, summary="Single-turn RAG health chat")
def single_turn_chat(req: ChatRequest) -> ChatResponse:
    """
    Stateless single-turn RAG chat.
    Fetches the patient's live health data, grounds the query in it,
    and calls Vertex AI Gemini. Each call is independent (no session history).
    """
    _get_client()
    context, sections = _build_patient_context(req.patient_id)
    system_prompt = _RAG_SYSTEM_PROMPT.format(context=context)
    history = [{"role": "user", "content": req.message}]
    text, usage = _call_gemini(history, system_prompt)
    return ChatResponse(
        response=_format_response(text),
        model=VERTEX_MODEL,
        grounded_on=sections,
        usage=usage or None,
    )


@router.post(
    "/chat/session",
    response_model=ChatResponse,
    summary="Multi-turn RAG health chat with session memory",
)
def session_chat(req: ChatRequest) -> ChatResponse:
    """
    Multi-turn RAG chat. Provide `session_id` in the request body to continue
    a conversation, or omit it to start a new one.
    Patient context is re-fetched on every turn so the bot always sees fresh data.
    """
    _get_client()

    sid = req.session_id or str(uuid.uuid4())
    if sid not in _SESSIONS:
        _SESSIONS[sid] = []

    history = _SESSIONS[sid]
    history.append({"role": "user", "content": req.message})

    context, sections = _build_patient_context(req.patient_id)
    system_prompt = _RAG_SYSTEM_PROMPT.format(context=context)
    text, usage = _call_gemini(history, system_prompt)

    history.append({"role": "model", "content": text})

    return ChatResponse(
        response=_format_response(text),
        session_id=sid,
        turn=sum(1 for m in history if m["role"] == "user"),
        model=VERTEX_MODEL,
        grounded_on=sections,
        usage=usage or None,
    )


@router.get(
    "/chat/session/{session_id}/history",
    summary="Get full conversation history for a session",
)
def get_session_history(session_id: str) -> dict:
    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    msgs = _SESSIONS[session_id]
    return {
        "session_id": session_id,
        "turns": sum(1 for m in msgs if m["role"] == "user"),
        "messages": msgs,
    }


@router.delete(
    "/chat/session/{session_id}",
    status_code=204,
    summary="Clear a conversation session",
)
def delete_session(session_id: str) -> None:
    _SESSIONS.pop(session_id, None)


@router.get("/models", summary="List available Gemini models on Vertex AI")
def list_models() -> dict:
    return {
        "configured_model": VERTEX_MODEL,
        "project": VERTEX_PROJECT or "(not set — set VERTEX_PROJECT env var)",
        "location": VERTEX_LOCATION,
        "setup": {
            "step_1": "Download Service Account JSON from GCP Console → IAM → Service Accounts → Keys",
            "step_2": "Grant the SA the 'Vertex AI User' role",
            "step_3": "Set env: GOOGLE_APPLICATION_CREDENTIALS=<path-to-sa-key.json>",
            "step_4": "Set env: VERTEX_PROJECT=questbeyond",
        },
        "available_models": [
            {"name": "gemini-2.0-flash-001", "description": "Fast, cost-efficient — recommended for chat"},
            {"name": "gemini-2.0-pro-001",   "description": "More capable — complex clinical reasoning"},
            {"name": "gemini-1.5-flash-002", "description": "Stable flash model with 1M token context"},
            {"name": "gemini-1.5-pro-002",   "description": "Most capable 1.5 model, 2M token context"},
        ],
    }
