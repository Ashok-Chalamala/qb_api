import datetime
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data.patients import (
    _MEMBER_DATA_MAP,
    _SARAH_PAGE_DATA,
    _GENIE_SUMMARY,
    USERS,
)
from app.models import ChatRequest, MetricEntryCreate, NoteCreate, SettingsUpdate
from app.stores import (
    _PATIENT_METRICS,
    _REPORTS_STORE,
    _SETTINGS_STORE,
    _SYMPTOMS_STORE,
    _WELLBEING_STORE,
)

router = APIRouter(tags=["patients"])


@router.get("/patients/{patient_id}/page-data")
def get_page_data(patient_id: str, member_id: Optional[str] = None) -> dict:
    """
    Returns the full MemberPageData payload for the given patient context.
    Pass `member_id` to get a family member's data view (e.g. fm1, fm2, fm3).
    """
    key = member_id if member_id else "primary"
    data = _MEMBER_DATA_MAP.get(key)
    if not data:
        raise HTTPException(status_code=404, detail=f"Page data not found for member '{key}'")
    return data


@router.get("/patients/{patient_id}/dashboard")
def get_dashboard(patient_id: str) -> dict:
    """Returns primary patient dashboard metrics."""
    return _SARAH_PAGE_DATA["dashboard"]


@router.get("/patients/{patient_id}/metrics/trends")
def get_metric_trends(patient_id: str) -> dict:
    """Returns 14-day sparkline trends."""
    return _SARAH_PAGE_DATA["metricTrends"]


@router.get("/patients/{patient_id}/forecast/glucose")
def get_glucose_forecast(patient_id: str, hours: int = 24) -> list:
    """Returns 24-hour glucose forecast."""
    return _SARAH_PAGE_DATA["glucoseForecast"][:hours]


@router.get("/patients/{patient_id}/timeline")
def get_timeline(patient_id: str) -> list:
    """Returns patient timeline events."""
    return _SARAH_PAGE_DATA["timelineData"]


@router.get("/patients/{patient_id}/alerts")
def get_alerts(patient_id: str) -> list:
    """Returns active patient alerts."""
    return _SARAH_PAGE_DATA["alertsData"]


@router.get("/patients/{patient_id}/alerts/history")
def get_alerts_history(patient_id: str) -> list:
    """Returns 30-day alert history."""
    return _SARAH_PAGE_DATA["alertHistory"]


@router.get("/patients/{patient_id}/genie/messages")
def get_genie_messages(patient_id: str) -> list:
    """Returns initial Genie conversation messages."""
    return _SARAH_PAGE_DATA["genieMessages"]


@router.get("/patients/{patient_id}/genie/summary")
def get_genie_summary(patient_id: str) -> dict:
    """Returns Genie's daily health briefing."""
    return _GENIE_SUMMARY


@router.post("/patients/{patient_id}/genie/chat")
def genie_chat(patient_id: str, req: ChatRequest) -> dict:
    """
    Genie chat — RAG-grounded via Vertex AI Gemini.
    Falls back to a mock response when Vertex AI is not configured.
    """
    import uuid
    from app.routers.vertex_chat import (
        _get_client, _build_patient_context, _call_gemini,
        _format_response, _RAG_SYSTEM_PROMPT, _SESSIONS, VERTEX_MODEL,
    )

    conversation_id = req.conversationId or str(uuid.uuid4())

    try:
        _get_client()
        if conversation_id not in _SESSIONS:
            _SESSIONS[conversation_id] = []
        history = _SESSIONS[conversation_id]
        history.append({"role": "user", "content": req.message})
        context, sections = _build_patient_context(patient_id)
        system_prompt = _RAG_SYSTEM_PROMPT.format(context=context)
        text, usage = _call_gemini(history, system_prompt)
        history.append({"role": "model", "content": text})
        return {
            "response": _format_response(text),
            "conversationId": conversation_id,
            "model": VERTEX_MODEL,
            "groundedOn": sections,
            "suggestedActions": [],
            "usage": usage or None,
        }
    except Exception:
        # Vertex AI not configured — return mock response
        response = (
            f"Thanks for your message: '{req.message}'\n\n"
            "Based on your recent data, I can see glucose has been elevated. "
            "I recommend checking with your care team if this pattern continues."
        )
        return {
            "response": response,
            "conversationId": conversation_id,
            "suggestedActions": ["schedule_telehealth", "log_meal"],
            "confidence": 0.88,
        }


@router.get("/patients/{patient_id}/profile")
def get_patient_profile(patient_id: str) -> dict:
    """Returns the primary patient's profile, including metrics."""
    user = next((u for u in USERS.values() if u["id"] == patient_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="Patient not found")
    metrics = _PATIENT_METRICS.get(patient_id, [])
    return {
        "id": patient_id,
        "fullName": user["fullName"],
        "mrn": user["mrn"],
        "condition": user["condition"],
        "age": user["age"],
        "gender": "F" if "sarah" in user["fullName"].lower() else "M",
        "bloodGroup": "O+",
        "phone": "+1 (555) 912-3456",
        "email": next((e for e, u in USERS.items() if u["id"] == patient_id), ""),
        "emergencyContact": "Carlos Martinez · +1 (555) 234-5678",
        "riskScore": "High",
        "conditions": [user["condition"]] if user["condition"] else [],
        "allergies": [],
        "medications": ["Metformin 500mg"],
        "healthNotes": "Primary patient. Continue routine monitoring and care plan follow-up.",
        "wellbeingNotes": "Symptoms and device trends monitored continuously via connected sources.",
        "wellbeingStatus": "Alert",
        "lastUpdated": "just now",
        "metrics": metrics,
        "reportsCount": len([r for r in _REPORTS_STORE.get(patient_id, []) if r["ownerType"] == "PATIENT"]),
    }


@router.post("/patients/{patient_id}/metrics")
def add_patient_metric(patient_id: str, metric: MetricEntryCreate) -> dict:
    """Add a new metric entry for the primary patient."""
    entry = {
        "id": f"pm{uuid.uuid4().hex[:8]}",
        **metric.model_dump(),
    }
    if patient_id not in _PATIENT_METRICS:
        _PATIENT_METRICS[patient_id] = []
    _PATIENT_METRICS[patient_id].insert(0, entry)
    return entry


@router.get("/patients/{patient_id}/settings")
def get_settings(patient_id: str) -> dict:
    """Returns the patient's preference settings."""
    return _SETTINGS_STORE.get(patient_id, {
        "push": True, "email": True, "sms": False,
        "glucoseHigh": 200, "sleepLow": 5.5, "hrHigh": 100,
        "hipaaAudit": True, "encryption": True, "gdprExport": True, "autoPurge": False,
    })


@router.put("/patients/{patient_id}/settings")
def update_settings(patient_id: str, body: SettingsUpdate) -> dict:
    """Persist the patient's preference settings."""
    current = _SETTINGS_STORE.setdefault(patient_id, {})
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    current.update(patch)
    return current


@router.get("/patients/{patient_id}/source-data/symptoms")
def list_symptoms(patient_id: str, subject_id: Optional[str] = None) -> list:
    """List symptom log entries, optionally filtered by subject_id."""
    key = subject_id or patient_id
    entries = _SYMPTOMS_STORE.get(key, [])
    return sorted(entries, key=lambda x: x["createdAt"], reverse=True)


@router.post("/patients/{patient_id}/source-data/symptoms")
def create_symptom(patient_id: str, body: NoteCreate,
                   subject_id: Optional[str] = None) -> dict:
    """Create a new symptom log entry."""
    key = subject_id or patient_id
    entry = {
        "id": f"sym-{uuid.uuid4().hex[:8]}",
        "patientId": key,
        "note": body.note,
        "createdBy": body.createdBy or "Unknown",
        "createdAt": datetime.datetime.utcnow().isoformat() + "Z",
    }
    _SYMPTOMS_STORE.setdefault(key, []).append(entry)
    return entry


@router.get("/patients/{patient_id}/source-data/wellbeing")
def list_wellbeing(patient_id: str, subject_id: Optional[str] = None) -> list:
    """List general wellbeing log entries."""
    key = subject_id or patient_id
    entries = _WELLBEING_STORE.get(key, [])
    return sorted(entries, key=lambda x: x["createdAt"], reverse=True)


@router.post("/patients/{patient_id}/source-data/wellbeing")
def create_wellbeing(patient_id: str, body: NoteCreate,
                     subject_id: Optional[str] = None) -> dict:
    """Create a new wellbeing log entry."""
    key = subject_id or patient_id
    entry = {
        "id": f"wb-{uuid.uuid4().hex[:8]}",
        "patientId": key,
        "note": body.note,
        "createdBy": body.createdBy or "Unknown",
        "createdAt": datetime.datetime.utcnow().isoformat() + "Z",
    }
    _WELLBEING_STORE.setdefault(key, []).append(entry)
    return entry
