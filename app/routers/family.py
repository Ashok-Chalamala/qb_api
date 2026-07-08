import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data.family import _FAMILY_MEMBERS
from app.models import FamilyMemberCreate, MetricEntryCreate
from app.stores import _FAMILY_STORE, _REPORTS_STORE

router = APIRouter(tags=["family"])


@router.get("/patients/{patient_id}/family")
def get_family_members(patient_id: str) -> list:
    """Returns all family members registered to the patient."""
    return _FAMILY_STORE.get(patient_id, _FAMILY_MEMBERS)


@router.get("/patients/{patient_id}/family/all")
def get_family_members_all(patient_id: str) -> list:
    """Returns all family members from the mutable store."""
    return _FAMILY_STORE.get(patient_id, [])


@router.get("/patients/{patient_id}/family/mutable")
def get_family_members_mutable(patient_id: str) -> list:
    """Returns family members from the mutable in-memory CRUD store."""
    return _FAMILY_STORE.get(patient_id, [])


@router.post("/patients/{patient_id}/family")
def add_family_member(patient_id: str, member: FamilyMemberCreate) -> dict:
    """Add a new family member."""
    new_member = {
        "id": f"fm{uuid.uuid4().hex[:8]}",
        "wellbeingStatus": member.wellbeingStatus,
        "lastUpdated": "just now",
        "reportsCount": 0,
        "metrics": [],
        **member.model_dump(),
    }
    if patient_id not in _FAMILY_STORE:
        _FAMILY_STORE[patient_id] = []
    _FAMILY_STORE[patient_id].append(new_member)
    return new_member


@router.put("/patients/{patient_id}/family/{member_id}")
def update_family_member(patient_id: str, member_id: str, member: FamilyMemberCreate) -> dict:
    """Update an existing family member."""
    members = _FAMILY_STORE.get(patient_id, [])
    idx = next((i for i, m in enumerate(members) if m["id"] == member_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Family member '{member_id}' not found")
    existing = members[idx]
    updated = {**existing, **member.model_dump(), "lastUpdated": "just now"}
    members[idx] = updated
    return updated


@router.delete("/patients/{patient_id}/family/{member_id}", status_code=204)
def delete_family_member(patient_id: str, member_id: str) -> None:
    """Remove a family member."""
    members = _FAMILY_STORE.get(patient_id, [])
    before = len(members)
    _FAMILY_STORE[patient_id] = [m for m in members if m["id"] != member_id]
    if len(_FAMILY_STORE[patient_id]) == before:
        raise HTTPException(status_code=404, detail=f"Family member '{member_id}' not found")


@router.post("/patients/{patient_id}/family/{member_id}/metrics")
def add_family_member_metric(patient_id: str, member_id: str, metric: MetricEntryCreate) -> dict:
    """Log a new metric for a family member."""
    members = _FAMILY_STORE.get(patient_id, [])
    idx = next((i for i, m in enumerate(members) if m["id"] == member_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Family member '{member_id}' not found")
    entry = {"id": f"m{uuid.uuid4().hex[:8]}", **metric.model_dump()}
    members[idx].setdefault("metrics", []).insert(0, entry)
    members[idx]["reportsCount"] = len([r for r in _REPORTS_STORE.get(patient_id, [])
                                        if r.get("ownerId") == member_id])
    return entry
