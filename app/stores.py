import copy

from app.data.family import _FAMILY_MEMBERS
from app.data.reports import _REPORTS
from app.data.devices import _DEVICES
from app.data.patients import PATIENT_METRICS_SEED

# Per-patient mutable family members (keyed by patient_id)
_FAMILY_STORE: dict[str, list[dict]] = {
    "patient-00429": copy.deepcopy(_FAMILY_MEMBERS),
}

# Per-patient mutable reports (keyed by patient_id)
_REPORTS_STORE: dict[str, list[dict]] = {
    "patient-00429": copy.deepcopy(_REPORTS),
}

# Per-patient mutable devices (keyed by patient_id)
_DEVICES_STORE: dict[str, list[dict]] = {
    "patient-00429": copy.deepcopy(_DEVICES),
}

# Per-patient notification / threshold settings
_SETTINGS_STORE: dict[str, dict] = {
    "patient-00429": {
        "push": True, "email": True, "sms": False,
        "glucoseHigh": 200, "sleepLow": 5.5, "hrHigh": 100,
        "hipaaAudit": True, "encryption": True, "gdprExport": True, "autoPurge": False,
    },
}

# Per-subject symptom log entries (keyed by patient_id or subject_id)
_SYMPTOMS_STORE: dict[str, list[dict]] = {}

# Per-subject wellbeing log entries
_WELLBEING_STORE: dict[str, list[dict]] = {}

# Per-patient vitals metrics (keyed by patient_id)
_PATIENT_METRICS: dict[str, list[dict]] = copy.deepcopy(PATIENT_METRICS_SEED)

# OTP sessions (in-memory, short-lived)
_OTP_SESSIONS: dict[str, dict] = {}
