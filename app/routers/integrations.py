import datetime
import random
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data.admin import _API_LOGS, _INTEGRATIONS_STORE
from app.models import IntegrationCreate

router = APIRouter(tags=["integrations"])


@router.get("/integrations")
def list_integrations(
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """List all patient integrations."""
    items = list(_INTEGRATIONS_STORE)
    if status:
        items = [i for i in items if i.get("status") == status]
    if search:
        q = search.lower()
        items = [i for i in items if q in i.get("name", "").lower()
                 or q in i.get("provider", "").lower()]
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start: start + page_size], "total": total}


@router.get("/integrations/{integration_id}")
def get_integration(integration_id: str) -> dict:
    """Return a single integration record."""
    item = next((i for i in _INTEGRATIONS_STORE if i["id"] == integration_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")
    return item


@router.post("/integrations", status_code=201)
def create_integration(body: IntegrationCreate) -> dict:
    """Create a new integration."""
    now = datetime.datetime.utcnow().isoformat() + "Z"
    new_integration: dict = {
        "id": f"int-{uuid.uuid4().hex[:8]}",
        "status": "Disconnected",
        "lastSync": None,
        "syncHistory": [],
        "totalSyncCount": 0,
        "createdAt": now,
        "updatedAt": now,
        "createdBy": "admin@questbeyond.com",
        **body.model_dump(),
    }
    _INTEGRATIONS_STORE.append(new_integration)
    return new_integration


@router.put("/integrations/{integration_id}")
def update_integration(integration_id: str, body: IntegrationCreate) -> dict:
    """Update an existing integration."""
    idx = next((i for i, it in enumerate(_INTEGRATIONS_STORE) if it["id"] == integration_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")
    updated = {**_INTEGRATIONS_STORE[idx], **body.model_dump(),
               "updatedAt": datetime.datetime.utcnow().isoformat() + "Z"}
    _INTEGRATIONS_STORE[idx] = updated
    return updated


@router.delete("/integrations/{integration_id}", status_code=204)
def delete_integration(integration_id: str) -> None:
    """Remove an integration."""
    before = len(_INTEGRATIONS_STORE)
    _INTEGRATIONS_STORE[:] = [i for i in _INTEGRATIONS_STORE if i["id"] != integration_id]
    if len(_INTEGRATIONS_STORE) == before:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")


@router.post("/integrations/{integration_id}/test")
def test_integration(integration_id: str) -> dict:
    """Test connectivity for an integration."""
    item = next((i for i in _INTEGRATIONS_STORE if i["id"] == integration_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")
    is_connected = item.get("status") == "Connected"
    latency = random.randint(80, 400) if is_connected else 5000
    return {
        "success": is_connected,
        "latency": latency,
        "statusCode": 200 if is_connected else 503,
        "message": (f"Successfully connected to {item['name']}." if is_connected
                    else f"Connection failed for {item['name']}."),
        "errorDetail": (None if is_connected else "Check credentials or network."),
    }


@router.get("/integrations/{integration_id}/logs")
def get_integration_logs(integration_id: str, page: int = 1, page_size: int = 10) -> dict:
    """Return API logs for a specific integration."""
    items = [l for l in _API_LOGS if l.get("integrationId") == integration_id]
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start: start + page_size], "total": total}
