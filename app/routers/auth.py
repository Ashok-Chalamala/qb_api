from fastapi import APIRouter, HTTPException

from app.models import LoginRequest
from app.data.patients import USERS

router = APIRouter(tags=["auth"])


@router.post("/auth/login")
def login(req: LoginRequest) -> dict:
    """Authenticate user and return profile (no JWT for demo — uses sessionStorage on client)."""
    user = USERS.get(req.email.strip().lower())
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {
        "id": user["id"],
        "email": req.email,
        "fullName": user["fullName"],
        "mrn": user["mrn"],
        "condition": user["condition"],
        "age": user["age"],
        "roles": user["roles"],
    }
