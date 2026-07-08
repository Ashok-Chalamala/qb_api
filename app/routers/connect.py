import datetime
import uuid

from fastapi import APIRouter, HTTPException

from app.data.admin import _ADMIN_PROVIDERS, _PATIENT_LINKS
from app.models import ConnectProviderRequest, OtpRequest, OtpVerify
from app.stores import _OTP_SESSIONS

router = APIRouter(tags=["connect"])

OTP_TTL_SECONDS = 300
DEMO_OTP = "123456"


@router.get("/patients/{patient_id}/links")
def list_patient_links(patient_id: str) -> list:
    """Return all provider links for this patient."""
    return [l for l in _PATIENT_LINKS if l.get("subjectId") == patient_id
            or l.get("subjectId", "").startswith("fm")]


@router.delete("/patients/{patient_id}/links/{link_id}", status_code=204)
def disconnect_patient_link(patient_id: str, link_id: str) -> None:
    """Disconnect a patient ↔ provider link."""
    idx = next((i for i, l in enumerate(_PATIENT_LINKS) if l["linkId"] == link_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Link '{link_id}' not found")
    _PATIENT_LINKS[idx]["status"] = "disconnected"
    _PATIENT_LINKS[idx]["disconnectedAt"] = datetime.datetime.utcnow().isoformat() + "Z"


@router.post("/connect/request-otp")
def request_otp(body: OtpRequest) -> dict:
    """Generate a 6-digit OTP and return session metadata."""
    session_id = f"otp-{uuid.uuid4().hex}"
    expires_at = (datetime.datetime.utcnow() +
                  datetime.timedelta(seconds=OTP_TTL_SECONDS)).isoformat() + "Z"
    _OTP_SESSIONS[session_id] = {
        "sessionId": session_id,
        "contact": body.contact,
        "channel": body.channel,
        "issuedAt": datetime.datetime.utcnow().isoformat() + "Z",
        "expiresAt": expires_at,
        "verified": False,
        "attempts": 0,
        "otp": DEMO_OTP,
        "providerId": body.providerId,
        "subjectId": body.subjectId,
    }
    if body.channel == "email":
        masked = body.contact[:1] + "***" + body.contact[body.contact.index("@"):]
    else:
        masked = body.contact[:3] + " *** ***-" + body.contact[-4:]
    return {
        "sessionId": session_id,
        "maskedContact": masked,
        "expiresInSeconds": OTP_TTL_SECONDS,
        "channel": body.channel,
    }


@router.post("/connect/verify-otp")
def verify_otp(body: OtpVerify) -> dict:
    """Validate a 6-digit OTP and return a session token."""
    session = _OTP_SESSIONS.get(body.sessionId)
    if not session:
        return {"verified": False, "sessionToken": "",
                "message": "Session expired or not found. Please request a new OTP."}
    session["attempts"] += 1
    is_valid = body.otp == DEMO_OTP or (body.otp.isdigit() and len(body.otp) == 6)
    if not is_valid:
        remaining = max(0, 5 - session["attempts"])
        return {"verified": False, "sessionToken": "",
                "message": f"Incorrect code. {remaining} attempt(s) remaining."}
    session["verified"] = True
    token = f"demo-verified-{body.sessionId}-{uuid.uuid4().hex[:8]}"
    del _OTP_SESSIONS[body.sessionId]
    return {"verified": True, "sessionToken": token, "message": "Identity verified successfully."}


@router.post("/connect/link", status_code=201)
def connect_provider(body: ConnectProviderRequest) -> dict:
    """Create a patient ↔ provider link after OTP verification."""
    if not body.sessionToken.startswith("demo-verified-"):
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    provider = next((p for p in _ADMIN_PROVIDERS if p["id"] == body.providerId), None)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{body.providerId}' not found")
    link: dict = {
        "linkId": f"lnk-{uuid.uuid4().hex[:8]}",
        "subjectId": body.subjectId,
        "subjectName": body.subjectName,
        "subjectType": body.subjectType,
        "providerId": body.providerId,
        "providerName": provider["displayName"],
        "providerType": provider["providerType"],
        "status": "connected",
        "dataTypes": list(body.dataTypes),
        "connectedAt": datetime.datetime.utcnow().isoformat() + "Z",
        "otpVerified": True,
        "consentId": f"con-{uuid.uuid4().hex[:8]}",
    }
    _PATIENT_LINKS.append(link)
    return {
        "linkId": link["linkId"],
        "providerName": provider["displayName"],
        "status": "connected",
        "dataTypes": link["dataTypes"],
        "connectedAt": link["connectedAt"],
        "message": f"Successfully connected to {provider['displayName']}.",
    }
