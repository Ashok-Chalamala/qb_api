"""
Google Health (Google Fit REST API) integration router.

OAuth flow:
  1. GET /google-health/auth?patient_id=<id>   → redirects to Google consent screen
  2. GET /google-health/callback               → Google redirects back here; token stored in memory
  3. GET /google-health/steps                  → daily step counts
  4. GET /google-health/heart-rate             → daily avg heart rate
  5. GET /google-health/sleep                  → sleep sessions
  6. GET /google-health/status                 → check auth state
  7. DELETE /google-health/disconnect          → revoke token

Environment variables (optional overrides):
  GOOGLE_CLIENT_SECRETS  – path to client_secret JSON file
  GOOGLE_REDIRECT_URI    – OAuth callback URL (must be registered in Google Cloud Console)
"""

import json
import os
from datetime import datetime, timezone

import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

router = APIRouter(prefix="/google-health", tags=["google-health"])

# ── Configuration ──────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
]

_DEFAULT_SECRETS = os.path.join(
    os.path.dirname(__file__), "..", "..", "docs",
    "client_secret.json",
)
CLIENT_SECRETS_FILE: str = os.environ.get("GOOGLE_CLIENT_SECRETS", _DEFAULT_SECRETS)
REDIRECT_URI: str = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8001/google-health/callback")

# ── In-memory stores ───────────────────────────────────────────────────────────

# { patient_id: serialised Credentials JSON dict }
_TOKEN_STORE: dict[str, dict] = {}

# { oauth_state: patient_id }  – cleared after use
_OAUTH_STATE: dict[str, str] = {}

# ── Helpers ────────────────────────────────────────────────────────────────────


def _build_flow() -> Flow:
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    return flow


def _get_credentials(patient_id: str) -> Credentials:
    token_data = _TOKEN_STORE.get(patient_id)
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail=(
                f"Patient '{patient_id}' is not authenticated with Google. "
                f"Start the OAuth flow at /google-health/auth?patient_id={patient_id}"
            ),
        )
    creds = Credentials(**token_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _TOKEN_STORE[patient_id] = json.loads(creds.to_json())
    return creds


def _fit_aggregate(
    creds: Credentials,
    data_type: str,
    start_ms: int,
    end_ms: int,
    bucket_ms: int = 86_400_000,  # 1-day buckets by default
) -> dict:
    url = "https://fitness.googleapis.com/fitness/v1/users/me/dataset:aggregate"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }
    body = {
        "aggregateBy": [{"dataTypeName": data_type}],
        "startTimeMillis": str(start_ms),
        "endTimeMillis": str(end_ms),
        "bucketByTime": {"durationMillis": str(bucket_ms)},
    }
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def _date_to_ms(date_str: str, end_of_day: bool = False) -> int:
    """Convert YYYY-MM-DD to epoch milliseconds (start or end of UTC day)."""
    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    ms = int(dt.timestamp() * 1000)
    return ms + 86_400_000 - 1 if end_of_day else ms


# ── Auth routes ────────────────────────────────────────────────────────────────


@router.get("/auth", summary="Start Google OAuth consent flow")
def start_auth(
    patient_id: str = Query(..., description="Patient ID to link to this Google account"),
):
    """Redirects the user to Google's OAuth consent screen."""
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=patient_id,
        prompt="consent",
    )
    _OAUTH_STATE[state] = patient_id
    return RedirectResponse(auth_url)


@router.get("/callback", summary="Google OAuth callback (handled automatically)")
def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """Google redirects here after the user grants consent. Stores the token."""
    patient_id = _OAUTH_STATE.pop(state, state)
    flow = _build_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    _TOKEN_STORE[patient_id] = json.loads(creds.to_json())
    return {
        "status": "authenticated",
        "patient_id": patient_id,
        "message": "Google Health connected successfully. You can now call /steps, /heart-rate, /sleep.",
    }


# ── Data routes ────────────────────────────────────────────────────────────────


@router.get("/steps", summary="Daily step counts from Google Fit")
def get_steps(
    patient_id: str = Query(...),
    start_date: str = Query("2026-07-01", description="YYYY-MM-DD"),
    end_date: str = Query("2026-07-07", description="YYYY-MM-DD"),
):
    """Returns aggregated daily step counts for the given date range."""
    creds = _get_credentials(patient_id)
    raw = _fit_aggregate(
        creds,
        "com.google.step_count.delta",
        _date_to_ms(start_date),
        _date_to_ms(end_date, end_of_day=True),
    )
    result = []
    for bucket in raw.get("bucket", []):
        date = datetime.fromtimestamp(
            int(bucket["startTimeMillis"]) / 1000, tz=timezone.utc
        ).strftime("%Y-%m-%d")
        total = sum(
            val.get("intVal", 0)
            for ds in bucket.get("dataset", [])
            for pt in ds.get("point", [])
            for val in pt.get("value", [])
        )
        result.append({"date": date, "steps": total})
    return {"patient_id": patient_id, "steps": result}


@router.get("/heart-rate", summary="Daily average heart rate from Google Fit")
def get_heart_rate(
    patient_id: str = Query(...),
    start_date: str = Query("2026-07-01", description="YYYY-MM-DD"),
    end_date: str = Query("2026-07-07", description="YYYY-MM-DD"),
):
    """Returns daily average BPM values for the given date range."""
    creds = _get_credentials(patient_id)
    raw = _fit_aggregate(
        creds,
        "com.google.heart_rate.bpm",
        _date_to_ms(start_date),
        _date_to_ms(end_date, end_of_day=True),
    )
    result = []
    for bucket in raw.get("bucket", []):
        date = datetime.fromtimestamp(
            int(bucket["startTimeMillis"]) / 1000, tz=timezone.utc
        ).strftime("%Y-%m-%d")
        bpm_values = [
            val["fpVal"]
            for ds in bucket.get("dataset", [])
            for pt in ds.get("point", [])
            for val in pt.get("value", [])
            if "fpVal" in val
        ]
        avg_bpm = round(sum(bpm_values) / len(bpm_values), 1) if bpm_values else None
        result.append({"date": date, "avg_bpm": avg_bpm, "samples": len(bpm_values)})
    return {"patient_id": patient_id, "heart_rate": result}


@router.get("/sleep", summary="Sleep sessions from Google Fit")
def get_sleep(
    patient_id: str = Query(...),
    start_date: str = Query("2026-07-01", description="YYYY-MM-DD"),
    end_date: str = Query("2026-07-07", description="YYYY-MM-DD"),
):
    """Returns sleep sessions (start, end, duration) for the given date range."""
    creds = _get_credentials(patient_id)
    url = "https://www.googleapis.com/fitness/v1/users/me/sessions"
    headers = {"Authorization": f"Bearer {creds.token}"}
    params = {
        "startTime": f"{start_date}T00:00:00Z",
        "endTime": f"{end_date}T23:59:59Z",
        "activityType": 72,  # 72 = sleeping in Google Fit activity types
    }
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    raw = resp.json()
    sessions = []
    for s in raw.get("session", []):
        start_ms = int(s.get("startTimeMillis", 0))
        end_ms = int(s.get("endTimeMillis", 0))
        sessions.append({
            "name": s.get("name", "Sleep"),
            "start": datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).isoformat(),
            "end": datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc).isoformat(),
            "duration_minutes": (end_ms - start_ms) // 60_000,
        })
    return {"patient_id": patient_id, "sleep_sessions": sessions}


# ── Management routes ──────────────────────────────────────────────────────────


@router.get("/status", summary="Check Google auth status for a patient")
def auth_status(patient_id: str = Query(...)):
    """Returns whether the patient has an active Google token."""
    if patient_id not in _TOKEN_STORE:
        return {"patient_id": patient_id, "authenticated": False}
    creds = Credentials(**_TOKEN_STORE[patient_id])
    return {
        "patient_id": patient_id,
        "authenticated": True,
        "expired": creds.expired,
        "scopes": list(creds.scopes or []),
    }


@router.delete("/disconnect", summary="Revoke and remove Google credentials")
def disconnect(patient_id: str = Query(...)):
    """Revokes the Google token and removes stored credentials for the patient."""
    if patient_id not in _TOKEN_STORE:
        raise HTTPException(status_code=404, detail="No Google token found for this patient")
    token_data = _TOKEN_STORE.pop(patient_id)
    creds = Credentials(**token_data)
    if creds.token:
        # Best-effort revoke — ignore errors
        requests.post(
            f"https://oauth2.googleapis.com/revoke?token={creds.token}",
            timeout=5,
        )
    return {"status": "disconnected", "patient_id": patient_id}
