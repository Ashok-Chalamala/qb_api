import datetime
import random
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data.admin import (
    _ADMIN_MAPPINGS,
    _ADMIN_PROVIDERS,
    _API_LOGS,
    _CERTIFICATES,
    _INTEGRATION_TEMPLATES,
)
from app.models import AdminProviderCreate, CertUpload, StatusUpdate

router = APIRouter(tags=["admin"])


@router.get("/admin/providers")
def list_admin_providers(
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """List all admin-configured providers with optional filtering."""
    items = list(_ADMIN_PROVIDERS)
    if status:
        items = [p for p in items if p.get("status") == status]
    if type:
        items = [p for p in items if p.get("providerType") == type]
    if search:
        q = search.lower()
        items = [p for p in items if q in p.get("displayName", "").lower()
                 or q in p.get("description", "").lower()]
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start: start + page_size], "total": total,
            "page": page, "pageSize": page_size}


@router.get("/admin/providers/{provider_id}")
def get_admin_provider(provider_id: str) -> dict:
    """Return a single admin provider configuration."""
    p = next((p for p in _ADMIN_PROVIDERS if p["id"] == provider_id), None)
    if not p:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    return p


@router.post("/admin/providers", status_code=201)
def create_admin_provider(body: AdminProviderCreate) -> dict:
    """Create a new admin provider configuration."""
    scope_list = [s.strip() for s in (body.scopes or "").split(",") if s.strip()]
    whitelist = [s.strip() for s in (body.ipWhitelist or "").split("\n") if s.strip()]
    now = datetime.datetime.utcnow().isoformat() + "Z"
    new_provider: dict = {
        "id": f"ap-{uuid.uuid4().hex[:8]}",
        "name": body.displayName.lower().replace(" ", "-"),
        "displayName": body.displayName,
        "description": body.description,
        "logoInitials": body.displayName[:2].upper(),
        "logoColor": "bg-teal-soft text-teal",
        "providerType": body.providerType,
        "fhirEndpoint": body.fhirEndpoint,
        "apiVersion": body.apiVersion,
        "webhookUrl": body.webhookUrl,
        "environment": body.environment,
        "status": "pending",
        "authType": body.authType,
        "ipWhitelist": whitelist,
        "supportedDataTypes": body.supportedDataTypes,
        "templateId": body.templateId,
        "connectedPatients": 0,
        "supportsOtp": body.supportsOtp,
        "supportsOAuth": body.supportsOAuth,
        "otpContactMethods": body.otpContactMethods,
        "createdAt": now,
        "updatedAt": now,
        "createdBy": "admin@questbeyond.com",
        "notes": body.notes,
    }
    if body.authType == "oauth2":
        new_provider["oauth2"] = {
            "clientId": body.clientId or "",
            "tokenUrl": body.tokenUrl or "",
            "authorizationUrl": body.authorizationUrl or "",
            "scopes": scope_list,
        }
    elif body.authType == "api-key":
        new_provider["apiKey"] = {
            "keyId": f"key-{uuid.uuid4().hex[:8]}",
            "headerName": body.apiKeyHeader or "X-API-Key",
        }
    _ADMIN_PROVIDERS.append(new_provider)
    return new_provider


@router.put("/admin/providers/{provider_id}")
def update_admin_provider(provider_id: str, body: AdminProviderCreate) -> dict:
    """Update an existing admin provider."""
    idx = next((i for i, p in enumerate(_ADMIN_PROVIDERS) if p["id"] == provider_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    existing = _ADMIN_PROVIDERS[idx]
    updated = {**existing,
               "displayName": body.displayName or existing["displayName"],
               "description": body.description or existing.get("description", ""),
               "fhirEndpoint": body.fhirEndpoint or existing.get("fhirEndpoint", ""),
               "apiVersion": body.apiVersion or existing.get("apiVersion", "R4"),
               "environment": body.environment or existing.get("environment", "sandbox"),
               "supportedDataTypes": body.supportedDataTypes or existing.get("supportedDataTypes", []),
               "updatedAt": datetime.datetime.utcnow().isoformat() + "Z"}
    _ADMIN_PROVIDERS[idx] = updated
    return updated


@router.delete("/admin/providers/{provider_id}", status_code=204)
def delete_admin_provider(provider_id: str) -> None:
    """Soft-delete (set status = 'inactive') an admin provider."""
    idx = next((i for i, p in enumerate(_ADMIN_PROVIDERS) if p["id"] == provider_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    _ADMIN_PROVIDERS[idx]["status"] = "inactive"
    _ADMIN_PROVIDERS[idx]["updatedAt"] = datetime.datetime.utcnow().isoformat() + "Z"


@router.put("/admin/providers/{provider_id}/status")
def set_admin_provider_status(provider_id: str, body: StatusUpdate) -> dict:
    """Change the status of an admin provider."""
    idx = next((i for i, p in enumerate(_ADMIN_PROVIDERS) if p["id"] == provider_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    _ADMIN_PROVIDERS[idx]["status"] = body.status
    _ADMIN_PROVIDERS[idx]["updatedAt"] = datetime.datetime.utcnow().isoformat() + "Z"
    return _ADMIN_PROVIDERS[idx]


@router.post("/admin/providers/{provider_id}/test")
def test_admin_provider(provider_id: str) -> dict:
    """Test connectivity to a configured FHIR endpoint."""
    p = next((p for p in _ADMIN_PROVIDERS if p["id"] == provider_id), None)
    if not p:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    is_active = p.get("status") == "active"
    return {
        "success": is_active,
        "latencyMs": 212 if is_active else 5000,
        "statusCode": 200 if is_active else 503,
        "message": (f"Connected to {p['displayName']}. CapabilityStatement retrieved."
                    if is_active else f"Connection timeout reaching {p.get('fhirEndpoint', '')}"),
        "fhirCapabilityStatement": (
            {"resourceType": "CapabilityStatement",
             "fhirVersion": p.get("apiVersion", "R4"), "format": ["json", "xml"]}
            if is_active else None
        ),
        "errorDetail": (None if is_active
                        else "TCP connection timed out. Check IP whitelist or provider downtime."),
    }


@router.get("/admin/templates")
def list_integration_templates(provider_type: Optional[str] = None) -> list:
    """List all integration templates."""
    items = list(_INTEGRATION_TEMPLATES)
    if provider_type:
        items = [t for t in items if t.get("providerType") == provider_type]
    return items


@router.get("/admin/security/certificates")
def list_certificates(provider_id: Optional[str] = None) -> list:
    """List all security certificates, optionally filtered by provider."""
    items = list(_CERTIFICATES)
    if provider_id:
        items = [c for c in items if c.get("providerId") == provider_id]
    return items


@router.post("/admin/security/certificates", status_code=201)
def upload_certificate(body: CertUpload) -> dict:
    """Upload a TLS certificate or API key for a provider."""
    provider = next((p for p in _ADMIN_PROVIDERS if p["id"] == body.providerId), None)
    cert: dict = {
        "id": f"cert-{uuid.uuid4().hex[:8]}",
        "providerId": body.providerId,
        "providerName": provider["displayName"] if provider else "Unknown",
        "keyType": body.keyType,
        "keyId": f"key-{uuid.uuid4().hex[:8]}",
        "fingerprint": f"SHA256:{':'.join(f'{random.randint(0, 255):02x}' for _ in range(10))}",
        "uploadedAt": datetime.datetime.utcnow().isoformat() + "Z",
        "uploadedBy": body.actorUserId,
        "expiresAt": body.expiresAt,
        "status": "active",
        "notes": body.notes,
    }
    _CERTIFICATES.append(cert)
    return cert


@router.get("/admin/mappings")
def list_admin_mappings(provider_id: Optional[str] = None) -> list:
    """List all data field mappings, optionally filtered by provider."""
    items = list(_ADMIN_MAPPINGS)
    if provider_id:
        items = [m for m in items if m.get("providerId") == provider_id]
    return items


@router.get("/admin/api-logs")
def list_api_logs(
    integration_id: Optional[str] = None,
    method: Optional[str] = None,
    status_code_gte: Optional[int] = None,
    status_code_lte: Optional[int] = None,
    subject_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "timestamp",
    sort_dir: str = "desc",
) -> dict:
    """List API / audit logs with filtering, sorting, and pagination."""
    items = list(_API_LOGS)
    if integration_id:
        items = [l for l in items if l.get("integrationId") == integration_id]
    if method:
        items = [l for l in items if l.get("method") == method.upper()]
    if status_code_gte is not None:
        items = [l for l in items if l.get("statusCode", 0) >= status_code_gte]
    if status_code_lte is not None:
        items = [l for l in items if l.get("statusCode", 0) <= status_code_lte]
    if subject_type:
        items = [l for l in items if l.get("subjectType") == subject_type.upper()]
    if search:
        q = search.lower()
        items = [l for l in items if
                 q in l.get("endpoint", "").lower() or
                 q in l.get("integrationName", "").lower() or
                 q in l.get("subjectName", "").lower() or
                 q in l.get("correlationId", "").lower()]
    reverse = sort_dir.lower() == "desc"
    items.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start: start + page_size], "total": total,
            "page": page, "pageSize": page_size}
