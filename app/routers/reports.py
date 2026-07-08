import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data.reports import _REPORTS
from app.models import ReportCreate
from app.stores import _FAMILY_STORE, _REPORTS_STORE

router = APIRouter(tags=["reports"])


@router.get("/patients/{patient_id}/reports")
def get_reports(patient_id: str, owner_type: Optional[str] = None,
                owner_id: Optional[str] = None, search: Optional[str] = None,
                category: Optional[str] = None, page: int = 1, page_size: int = 50) -> dict:
    """Returns reports with optional filtering and pagination."""
    items = list(_REPORTS_STORE.get(patient_id, _REPORTS))
    if owner_type:
        items = [r for r in items if r.get("ownerType") == owner_type]
    if owner_id:
        items = [r for r in items if r.get("ownerId") == owner_id]
    if category:
        items = [r for r in items if r.get("reportCategory") == category]
    if search:
        q = search.lower()
        items = [r for r in items if q in r.get("reportName", "").lower()
                 or q in r.get("reportCategory", "").lower()
                 or q in r.get("healthcareFacility", "").lower()]
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start: start + page_size], "total": total,
            "page": page, "pageSize": page_size}


@router.get("/patients/{patient_id}/reports/all")
def get_reports_all(patient_id: str, owner_type: Optional[str] = None,
                    owner_id: Optional[str] = None, search: Optional[str] = None,
                    page: int = 1, page_size: int = 50) -> dict:
    """Returns reports with optional filtering and pagination (mutable store)."""
    items = list(_REPORTS_STORE.get(patient_id, []))
    if owner_type:
        items = [r for r in items if r.get("ownerType") == owner_type]
    if owner_id:
        items = [r for r in items if r.get("ownerId") == owner_id]
    if search:
        q = search.lower()
        items = [r for r in items if q in r.get("reportName", "").lower()
                 or q in r.get("reportCategory", "").lower()
                 or q in r.get("healthcareFacility", "").lower()]
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start: start + page_size], "total": total}


@router.post("/patients/{patient_id}/reports")
def create_report(patient_id: str, report: ReportCreate) -> dict:
    """Upload / create a new medical report."""
    new_report = {
        "id": f"r{uuid.uuid4().hex[:8]}",
        **report.model_dump(),
    }
    if patient_id not in _REPORTS_STORE:
        _REPORTS_STORE[patient_id] = []
    _REPORTS_STORE[patient_id].insert(0, new_report)
    owner_id = report.ownerId
    if report.ownerType == "FAMILY_MEMBER" and owner_id:
        members = _FAMILY_STORE.get(patient_id, [])
        for m in members:
            if m["id"] == owner_id:
                m["reportsCount"] = len([r for r in _REPORTS_STORE[patient_id]
                                         if r.get("ownerId") == owner_id])
    return new_report


@router.delete("/patients/{patient_id}/reports/{report_id}", status_code=204)
def delete_report(patient_id: str, report_id: str) -> None:
    """Delete a report by ID."""
    reports = _REPORTS_STORE.get(patient_id, [])
    before = len(reports)
    _REPORTS_STORE[patient_id] = [r for r in reports if r["id"] != report_id]
    if len(_REPORTS_STORE[patient_id]) == before:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
