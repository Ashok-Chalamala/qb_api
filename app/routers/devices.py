import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data.devices import _DEVICES
from app.models import DeviceCreate
from app.stores import _DEVICES_STORE

router = APIRouter(tags=["devices"])


@router.get("/patients/{patient_id}/devices")
def get_devices_route(patient_id: str, status: Optional[str] = None,
                      search: Optional[str] = None) -> dict:
    """Returns connected devices."""
    items = list(_DEVICES_STORE.get(patient_id, _DEVICES))
    if status:
        items = [d for d in items if d.get("status") == status]
    if search:
        q = search.lower()
        items = [d for d in items if q in d.get("name", "").lower()]
    return {"items": items, "total": len(items)}


@router.get("/patients/{patient_id}/devices/all")
def get_devices_all(patient_id: str, status: Optional[str] = None,
                    search: Optional[str] = None) -> dict:
    """Returns devices with optional filtering (mutable store)."""
    items = list(_DEVICES_STORE.get(patient_id, []))
    if status:
        items = [d for d in items if d.get("status") == status]
    if search:
        q = search.lower()
        items = [d for d in items if q in d.get("name", "").lower()]
    return {"items": items, "total": len(items)}


@router.post("/patients/{patient_id}/devices")
def add_device(patient_id: str, device: DeviceCreate) -> dict:
    """Register a new device."""
    new_device = {
        "id": f"d{uuid.uuid4().hex[:8]}",
        **device.model_dump(),
    }
    if patient_id not in _DEVICES_STORE:
        _DEVICES_STORE[patient_id] = []
    _DEVICES_STORE[patient_id].append(new_device)
    return new_device


@router.put("/patients/{patient_id}/devices/{device_id}")
def update_device(patient_id: str, device_id: str, device: DeviceCreate) -> dict:
    """Update a device record."""
    devices = _DEVICES_STORE.get(patient_id, [])
    idx = next((i for i, d in enumerate(devices) if d["id"] == device_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    updated = {**devices[idx], **device.model_dump()}
    devices[idx] = updated
    return updated


@router.delete("/patients/{patient_id}/devices/{device_id}", status_code=204)
def delete_device(patient_id: str, device_id: str) -> None:
    """Remove a device."""
    devices = _DEVICES_STORE.get(patient_id, [])
    before = len(devices)
    _DEVICES_STORE[patient_id] = [d for d in devices if d["id"] != device_id]
    if len(_DEVICES_STORE[patient_id]) == before:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
