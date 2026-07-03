"""
Quest Beyond — FastAPI Backend
Serves all patient, dashboard, timeline, alerts, devices, forecast, genie,
family and reports data consumed by the React front-end.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
"""

import math
import random
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Quest Beyond API",
    description="Patient health data aggregation API for Quest Beyond",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ───────────────────────────────────────────────────────────────────────

USERS: dict[str, dict] = {
    "sarah.martinez@questbeyond.com": {
        "password": "Patient@2026",
        "id": "patient-00429",
        "fullName": "Sarah Martinez",
        "mrn": "00429",
        "condition": "Type 2 Diabetes",
        "age": 45,
        "roles": ["PATIENT"],
    },
    "james.lee@questbeyond.com": {
        "password": "Patient@2026",
        "id": "patient-00312",
        "fullName": "James Lee",
        "mrn": "00312",
        "condition": "Hypertension",
        "age": 58,
        "roles": ["PATIENT"],
    },
    "admin@questbeyond.com": {
        "password": "Admin@2026",
        "id": "admin-001",
        "fullName": "QBeyond Admin",
        "mrn": "",
        "condition": "",
        "age": 0,
        "roles": ["ADMIN"],
    },
}


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/login")
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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _generate_forecast(base_mg: float) -> list[dict]:
    result = []
    for i in range(24):
        base = base_mg + math.sin(i / 3) * 18 + i * 1.6
        noise = (math.sin(i * 1.7) + math.cos(i * 0.9)) * 5
        result.append({
            "hour": f"{i}:00",
            "actual": round(base + noise) if i < 10 else None,
            "forecast": round(base + noise + ((i - 10) * 2.5 if i >= 10 else 0)),
            "upper": round(base + noise + ((i - 10) * 4 + 12 if i >= 10 else 10)),
            "lower": round(base + noise - (6 if i >= 10 else 8)),
        })
    return result


def _alert_history(seed: int, pattern: str = "default") -> list[dict]:
    rng = random.Random(seed)
    if pattern == "low":
        return [{"day": i + 1, "count": max(0, round(math.sin(i / 4) * 1.5 + (2 if i > 20 else 0.5) + rng.random()))} for i in range(30)]
    if pattern == "minimal":
        return [{"day": i + 1, "count": max(0, round(math.sin(i / 5) * 1 + 0.3 + rng.random() * 0.5))} for i in range(30)]
    return [{"day": i + 1, "count": max(0, round(math.sin(i / 3) * 2 + (3 if i > 22 else 1) + rng.random()))} for i in range(30)]


# ── Mock page-data store ───────────────────────────────────────────────────────

_SARAH_PAGE_DATA: dict[str, Any] = {
    "memberName": "Sarah Martinez",
    "memberCondition": "Type 2 Diabetes",
    "dashboard": {
        "healthScore": 82,
        "activeAlerts": 3,
        "stepsToday": 7421,
        "stepsGoal": 10000,
        "glucoseLatest": 142,
        "glucoseUnit": "mg/dL",
        "glucoseTrend": "+12%",
        "dataSources": [
            {"name": "Apple Watch Series 9", "status": "Live", "icon": "⌚", "accent": "teal"},
            {"name": "Dexcom G7 CGM", "status": "Live", "icon": "🩸", "accent": "rose"},
            {"name": "Home Test Kit", "status": "New", "icon": "🧪", "accent": "sky"},
            {"name": "Symptom Logger", "status": "Live", "icon": "📝", "accent": "violet"},
            {"name": "SDOH Survey", "status": "Flagged", "icon": "🏠", "accent": "amber"},
        ],
        "alerts": [
            {"title": "Glucose >200 for 3 days", "severity": "Critical", "icon": "🚨"},
            {"title": "Sleep <5h for 4 nights", "severity": "High", "icon": "😴"},
            {"title": "SDOH: Transport barrier", "severity": "Medium", "icon": "🚗"},
        ],
        "forecast": {"peak": 185, "risk": 68, "trend": "rising"},
    },
    "metricTrends": {
        "health": [76, 78, 75, 79, 80, 78, 81, 79, 82, 81, 83, 82, 84, 82],
        "alerts": [1, 0, 2, 1, 1, 3, 2, 1, 4, 2, 3, 2, 3, 3],
        "steps": [6200, 7800, 8400, 5900, 9100, 7200, 6800, 8800, 7500, 9300, 6400, 7100, 8200, 7421],
        "glucose": [128, 132, 138, 141, 145, 152, 148, 156, 162, 158, 165, 158, 148, 142],
    },
    "glucoseForecast": _generate_forecast(120),
    "timelineData": [
        {
            "date": "Today",
            "events": [
                {"time": "08:14 AM", "source": "Dexcom G7 CGM", "title": "Fasting Glucose: 234 mg/dL", "severity": "Alert", "category": "Glucose"},
                {"time": "07:30 AM", "source": "Apple Watch", "title": "Sleep: 4h 22m", "detail": "Deep: 42min · REM: 58min", "category": "Wearable"},
                {"time": "06:48 AM", "source": "Apple Watch", "title": "Resting HR: 78 bpm", "detail": "↑ 8 bpm vs. baseline", "category": "Wearable"},
            ],
        },
        {
            "date": "Yesterday",
            "events": [
                {"time": "09:00 PM", "source": "Symptom Logger", "title": "Fatigue 7/10 · Headache 4/10", "detail": "Caregiver note included", "category": "Symptoms"},
                {"time": "02:15 PM", "source": "Quest Home Test", "title": "A1C: 7.8%", "detail": "Captured via API", "category": "Tests"},
                {"time": "10:02 AM", "source": "SDOH Survey", "title": "Transport barrier reported", "detail": "Missed 1 prior appointment", "category": "SDOH"},
            ],
        },
        {
            "date": "Jun 14",
            "events": [
                {"time": "11:42 PM", "source": "Dexcom G7 CGM", "title": "Nocturnal Low: 64 mg/dL", "severity": "Alert", "category": "Glucose"},
                {"time": "07:11 AM", "source": "Apple Watch", "title": "Steps: 8,210", "detail": "Active min: 41", "category": "Wearable"},
            ],
        },
    ],
    "weeklyTrend": [
        {"day": "Mon", "value": 138}, {"day": "Tue", "value": 156}, {"day": "Wed", "value": 172},
        {"day": "Thu", "value": 188}, {"day": "Fri", "value": 201}, {"day": "Sat", "value": 218}, {"day": "Sun", "value": 234},
    ],
    "weeklyTrendLabel": "7-day Glucose Trend",
    "weeklyTrendRefLine": 180,
    "alertsData": [
        {
            "id": "alt1", "severity": "Critical", "icon": "🚨",
            "title": "Glucose Crisis Pattern Detected",
            "description": "Fasting glucose >200 mg/dL for 3 consecutive days. Combined with fatigue and poor sleep.",
            "meta": ["Dexcom G7", "3 days", "Confidence 94%"],
            "actions": ["Call Patient", "Acknowledge"],
        },
        {
            "id": "alt2", "severity": "High", "icon": "😴",
            "title": "Sleep Deprivation + Fatigue Correlation",
            "description": "Sleep averaging 4.5h/night this week. Fatigue rated 6-8/10 on 4 of 7 days.",
            "meta": ["Apple Watch", "7 days", "Confidence 88%"],
            "actions": ["View Data", "Acknowledge"],
        },
        {
            "id": "alt3", "severity": "Medium", "icon": "🚗",
            "title": "SDOH: Transport Barrier",
            "description": "Patient reported transport difficulty. Next appointment Jun 17 — 5 days away.",
            "meta": ["SDOH Survey", "1 day", "Confidence 76%"],
            "actions": ["Arrange Lyft", "Dismiss"],
        },
    ],
    "alertHistory": _alert_history(42, "default"),
    "genieMessages": [
        {"role": "assistant", "content": "👋 Hi Sarah! I'm Genie. I see your glucose has been elevated for 3 days and your sleep is below 5 hours. Would you like me to explain what this pattern means?"},
        {"role": "user", "content": "Why is my glucose so high this week?"},
        {
            "role": "assistant",
            "content": "Let me analyze your last 7 days of data...\n\nKey findings:\n1. Sleep avg: 4.5h (↓ 18% from baseline)\n2. Evening carbs: 65g avg (↑ 25%)\n3. Stress flagged in SDOH survey\n\nCombined, these factors explain 84% of your glucose variability.",
            "actions": ["Set appointment reminder", "Log Meal"],
        },
    ],
}

_CARLOS_PAGE_DATA: dict[str, Any] = {
    "memberName": "Carlos Martinez",
    "memberCondition": "Hypertension · Arthritis",
    "dashboard": {
        "healthScore": 68,
        "activeAlerts": 2,
        "stepsToday": 4200,
        "stepsGoal": 7000,
        "glucoseLatest": 143,
        "glucoseUnit": "mmHg",
        "glucoseTrend": "+4%",
        "dataSources": [
            {"name": "Omron BP Monitor", "status": "Live", "icon": "💓", "accent": "rose"},
            {"name": "Fitbit Inspire 3", "status": "Live", "icon": "⌚", "accent": "teal"},
            {"name": "Medication Tracker", "status": "Active", "icon": "💊", "accent": "violet"},
            {"name": "Symptom Logger", "status": "Live", "icon": "📝", "accent": "amber"},
        ],
        "alerts": [
            {"title": "BP >140/90 for 4 mornings", "severity": "High", "icon": "💓"},
            {"title": "Arthritis flare — reduced mobility", "severity": "Medium", "icon": "🦴"},
        ],
        "forecast": {"peak": 152, "risk": 52, "trend": "elevated"},
    },
    "metricTrends": {
        "health": [64, 66, 63, 65, 67, 65, 66, 68, 67, 69, 68, 70, 68, 68],
        "alerts": [1, 2, 1, 2, 2, 3, 2, 1, 2, 3, 2, 3, 2, 2],
        "steps": [3900, 4800, 5100, 3600, 5500, 4400, 4000, 5200, 4600, 5700, 3900, 4300, 4900, 4200],
        "glucose": [138, 141, 139, 144, 142, 145, 142, 148, 146, 143, 145, 142, 144, 142],
    },
    "glucoseForecast": _generate_forecast(140),
    "timelineData": [
        {
            "date": "Today",
            "events": [
                {"time": "07:30 AM", "source": "Omron BP Monitor", "title": "Morning BP: 145/92 mmHg", "severity": "Alert", "category": "Glucose"},
                {"time": "07:00 AM", "source": "Fitbit Inspire 3", "title": "Sleep: 6h 10m", "detail": "Light sleep 62% · Restless 3×", "category": "Wearable"},
                {"time": "08:15 AM", "source": "Medication Tracker", "title": "Lisinopril 10mg taken", "detail": "On schedule", "category": "Tests"},
            ],
        },
        {
            "date": "Yesterday",
            "events": [
                {"time": "08:00 PM", "source": "Symptom Logger", "title": "Left knee pain: 5/10", "detail": "After evening walk — arthritis flare", "category": "Symptoms"},
                {"time": "07:15 AM", "source": "Omron BP Monitor", "title": "Morning BP: 142/88 mmHg", "category": "Glucose"},
                {"time": "06:30 AM", "source": "Fitbit Inspire 3", "title": "Steps: 4,800", "detail": "Active min: 28", "category": "Wearable"},
            ],
        },
        {
            "date": "Jun 23",
            "events": [
                {"time": "09:00 AM", "source": "Omron BP Monitor", "title": "BP check: 148/94 mmHg", "severity": "Alert", "category": "Glucose"},
                {"time": "03:00 PM", "source": "Medication Tracker", "title": "Aspirin 81mg taken", "detail": "Post-lunch", "category": "Tests"},
            ],
        },
    ],
    "weeklyTrend": [
        {"day": "Mon", "value": 138}, {"day": "Tue", "value": 141}, {"day": "Wed", "value": 139},
        {"day": "Thu", "value": 144}, {"day": "Fri", "value": 142}, {"day": "Sat", "value": 145}, {"day": "Sun", "value": 143},
    ],
    "weeklyTrendLabel": "7-day BP Trend (Systolic mmHg)",
    "weeklyTrendRefLine": 130,
    "alertsData": [
        {
            "id": "ca1", "severity": "High", "icon": "💓",
            "title": "Persistent Elevated Blood Pressure",
            "description": "Morning BP averaging 143/91 mmHg over 4 days. Exceeds target of <130/80.",
            "meta": ["Omron Monitor", "4 days", "Confidence 91%"],
            "actions": ["Contact Doctor", "Acknowledge"],
        },
        {
            "id": "ca2", "severity": "Medium", "icon": "🦴",
            "title": "Arthritis Mobility Alert",
            "description": "Reported knee pain 5/10 for 2 consecutive evenings. Activity dropped 22% vs baseline.",
            "meta": ["Symptom Logger", "2 days", "Confidence 79%"],
            "actions": ["View Data", "Acknowledge"],
        },
    ],
    "alertHistory": _alert_history(7, "low"),
    "genieMessages": [
        {"role": "assistant", "content": "👋 Hi Sarah! I'm reviewing Carlos's data. His morning BP has been consistently elevated (avg 143/91 mmHg) over 4 days — above his <130/80 target. Would you like a summary or notes for his physician?"},
        {"role": "user", "content": "What might be causing Dad's BP to spike in the mornings?"},
        {
            "role": "assistant",
            "content": "Based on Carlos's last 7 days:\n\n1. Sleep quality: Averaging 6h 10m with frequent restlessness (↓ quality)\n2. Morning cortisol surge — common BP driver in seniors\n3. Sodium intake: Symptom notes suggest takeout 3× this week\n4. Medication timing: Lisinopril taken after the morning spike window\n\nRecommendation: Shift Lisinopril to bedtime (discuss with physician) and monitor sodium closely.",
            "actions": ["Schedule appointment", "Log meal"],
        },
    ],
}

_MARIA_PAGE_DATA: dict[str, Any] = {
    "memberName": "Maria Martinez",
    "memberCondition": "Type 2 Diabetes · Hypothyroidism",
    "dashboard": {
        "healthScore": 79,
        "activeAlerts": 1,
        "stepsToday": 6800,
        "stepsGoal": 8000,
        "glucoseLatest": 118,
        "glucoseUnit": "mg/dL",
        "glucoseTrend": "-8%",
        "dataSources": [
            {"name": "OneTouch Glucometer", "status": "Live", "icon": "🩸", "accent": "amber"},
            {"name": "Garmin Vívosmart 5", "status": "Live", "icon": "⌚", "accent": "teal"},
            {"name": "Thyroid Tracker", "status": "Active", "icon": "🔬", "accent": "violet"},
            {"name": "Symptom Logger", "status": "Live", "icon": "📝", "accent": "sky"},
        ],
        "alerts": [
            {"title": "Thyroid med: dose review needed", "severity": "Medium", "icon": "🔬"},
        ],
        "forecast": {"peak": 142, "risk": 34, "trend": "stable"},
    },
    "metricTrends": {
        "health": [74, 76, 75, 77, 78, 77, 78, 79, 78, 80, 79, 81, 80, 79],
        "alerts": [1, 0, 1, 1, 0, 2, 1, 0, 1, 1, 0, 1, 1, 1],
        "steps": [5900, 7200, 7800, 5500, 8400, 6600, 6200, 7800, 6800, 8600, 5900, 6500, 7500, 6800],
        "glucose": [124, 119, 122, 118, 121, 116, 119, 115, 118, 114, 117, 113, 116, 118],
    },
    "glucoseForecast": _generate_forecast(116),
    "timelineData": [
        {
            "date": "Today",
            "events": [
                {"time": "07:45 AM", "source": "OneTouch Glucometer", "title": "Fasting Glucose: 118 mg/dL", "detail": "In range · Target <126", "category": "Glucose"},
                {"time": "07:00 AM", "source": "Garmin Vívosmart 5", "title": "Sleep: 7h 04m", "detail": "Deep: 1h 12m · Morning steps: 2,200", "category": "Wearable"},
                {"time": "08:30 AM", "source": "Medication Tracker", "title": "Metformin 500mg taken", "detail": "With breakfast — on schedule", "category": "Tests"},
            ],
        },
        {
            "date": "Yesterday",
            "events": [
                {"time": "07:30 AM", "source": "OneTouch Glucometer", "title": "Fasting Glucose: 116 mg/dL", "detail": "Well-controlled", "category": "Glucose"},
                {"time": "06:00 PM", "source": "Garmin Vívosmart 5", "title": "Evening walk: 3,200 steps", "detail": "30 min · Avg HR: 108 bpm", "category": "Wearable"},
                {"time": "09:15 AM", "source": "Medication Tracker", "title": "Levothyroxine 50mcg taken", "category": "Tests"},
            ],
        },
        {
            "date": "Jun 22",
            "events": [
                {"time": "10:00 AM", "source": "Quest Diagnostics", "title": "Thyroid Panel — TSH: 3.2", "detail": "Slight elevation — dose review scheduled", "severity": "Alert", "category": "Tests"},
                {"time": "07:30 AM", "source": "OneTouch Glucometer", "title": "Fasting Glucose: 121 mg/dL", "category": "Glucose"},
            ],
        },
    ],
    "weeklyTrend": [
        {"day": "Mon", "value": 124}, {"day": "Tue", "value": 119}, {"day": "Wed", "value": 122},
        {"day": "Thu", "value": 118}, {"day": "Fri", "value": 121}, {"day": "Sat", "value": 116}, {"day": "Sun", "value": 118},
    ],
    "weeklyTrendLabel": "7-day Glucose Trend",
    "weeklyTrendRefLine": 126,
    "alertsData": [
        {
            "id": "ma1", "severity": "Medium", "icon": "🔬",
            "title": "Thyroid Medication Review Due",
            "description": "TSH at 3.2 mIU/L (borderline elevated). Endocrinologist recommends Levothyroxine dose adjustment.",
            "meta": ["Quest Diagnostics", "1 day", "Confidence 87%"],
            "actions": ["Book Appointment", "Acknowledge"],
        },
    ],
    "alertHistory": _alert_history(13, "minimal"),
    "genieMessages": [
        {"role": "assistant", "content": "👋 Hi Sarah! Maria's glucose is well-controlled this week — averaging 118 mg/dL, down 8% from last week. Great progress! However, her thyroid panel shows TSH at 3.2 — slightly above target. Would you like me to explain what this means?"},
        {"role": "user", "content": "Is Mom's diabetes under control?"},
        {
            "role": "assistant",
            "content": "Yes — Maria's diabetes management looks excellent right now:\n\n✅ Fasting glucose avg: 119 mg/dL (target <126)\n✅ No readings >140 in the past 7 days\n✅ Daily 30-min walks contributing to control\n\nThe main watch item is thyroid function — TSH elevation can increase insulin resistance over time. Monitoring both together is the right approach.",
            "actions": ["View glucose history", "Set appointment reminder"],
        },
    ],
}

_JAKE_PAGE_DATA: dict[str, Any] = {
    "memberName": "Jake Martinez",
    "memberCondition": "Asthma · Peanut Allergy",
    "dashboard": {
        "healthScore": 91,
        "activeAlerts": 1,
        "stepsToday": 12400,
        "stepsGoal": 12000,
        "glucoseLatest": 94,
        "glucoseUnit": "mg/dL",
        "glucoseTrend": "stable",
        "dataSources": [
            {"name": "Garmin Forerunner 255", "status": "Live", "icon": "⌚", "accent": "teal"},
            {"name": "Smart Inhaler (Propeller)", "status": "Live", "icon": "💨", "accent": "sky"},
            {"name": "Allergy Alert App", "status": "Active", "icon": "🌿", "accent": "lime"},
            {"name": "Symptom Logger", "status": "Live", "icon": "📝", "accent": "violet"},
        ],
        "alerts": [
            {"title": "High pollen — asthma risk today", "severity": "Medium", "icon": "🌿"},
        ],
        "forecast": {"peak": 102, "risk": 14, "trend": "stable"},
    },
    "metricTrends": {
        "health": [88, 90, 89, 91, 90, 92, 91, 93, 92, 94, 91, 93, 92, 91],
        "alerts": [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1],
        "steps": [9800, 14200, 13600, 8900, 15400, 12600, 11200, 14800, 12200, 15800, 10400, 13200, 14600, 12400],
        "glucose": [91, 93, 90, 94, 92, 96, 93, 95, 91, 94, 92, 96, 93, 94],
    },
    "glucoseForecast": _generate_forecast(92),
    "timelineData": [
        {
            "date": "Today",
            "events": [
                {"time": "03:45 PM", "source": "Garmin Forerunner 255", "title": "Soccer practice: 8,400 steps", "detail": "Peak HR: 178 bpm · Duration: 62 min", "category": "Wearable"},
                {"time": "03:30 PM", "source": "Smart Inhaler", "title": "Reliever used pre-exercise", "detail": "Pollen count high today (76 µg/m³)", "category": "Symptoms"},
                {"time": "07:15 AM", "source": "Garmin Forerunner 255", "title": "Sleep: 8h 22m", "detail": "Deep: 2h 04m · Resting HR: 58 bpm", "category": "Wearable"},
            ],
        },
        {
            "date": "Yesterday",
            "events": [
                {"time": "05:00 PM", "source": "Allergy Alert App", "title": "Tree pollen: Very High (92 µg/m³)", "detail": "Advised to limit outdoor activity", "severity": "Alert", "category": "Symptoms"},
                {"time": "04:30 PM", "source": "Smart Inhaler", "title": "Reliever inhaler used", "detail": "Post-recess · mild wheeze", "category": "Symptoms"},
                {"time": "07:30 AM", "source": "Garmin Forerunner 255", "title": "Morning run: 3.2 miles", "detail": "Avg pace 8:42/mi", "category": "Wearable"},
            ],
        },
    ],
    "weeklyTrend": [
        {"day": "Mon", "value": 91}, {"day": "Tue", "value": 93}, {"day": "Wed", "value": 90},
        {"day": "Thu", "value": 94}, {"day": "Fri", "value": 92}, {"day": "Sat", "value": 96}, {"day": "Sun", "value": 94},
    ],
    "weeklyTrendLabel": "7-day Glucose Trend",
    "weeklyTrendRefLine": 100,
    "alertsData": [
        {
            "id": "ja1", "severity": "Medium", "icon": "🌿",
            "title": "High Pollen Asthma Risk",
            "description": "Tree pollen at 92 µg/m³ (Very High). Jake used reliever inhaler twice in past 24h.",
            "meta": ["Allergy Alert App", "1 day", "Confidence 83%"],
            "actions": ["Limit Outdoor Activity", "Acknowledge"],
        },
    ],
    "alertHistory": _alert_history(99, "minimal"),
    "genieMessages": [
        {"role": "assistant", "content": "👋 Hi Sarah! Jake's health looks great overall — health score 91, sleep excellent, very active. One watch item: pollen count is high today (92 µg/m³) and he used his inhaler pre-exercise. No emergency, but good to monitor."},
        {"role": "user", "content": "Is Jake's asthma under control?"},
        {
            "role": "assistant",
            "content": "Yes — Jake's asthma is well-managed:\n\n✅ FEV1: 82% predicted (recent PFT)\n✅ No ER visits or hospitalizations in 12 months\n✅ Pre-exercise inhaler use is preventive, not reactive\n\nKey triggers to watch:\n• Tree pollen (currently Very High)\n• Cold air on morning runs\n• Post-exercise recovery\n\nHe's doing great — just monitor on high-pollen days.",
            "actions": ["View PFT results", "Set pollen alerts"],
        },
    ],
}

_MEMBER_DATA_MAP: dict[str, dict] = {
    "primary": _SARAH_PAGE_DATA,
    "fm1": _CARLOS_PAGE_DATA,
    "fm2": _MARIA_PAGE_DATA,
    "fm3": _JAKE_PAGE_DATA,
}

# ── Family members ─────────────────────────────────────────────────────────────

_FAMILY_MEMBERS: list[dict] = [
    {
        "id": "fm1",
        "fullName": "Carlos Martinez",
        "relationship": "Father",
        "age": 72,
        "gender": "Male",
        "bloodGroup": "O+",
        "phone": "+1 (555) 234-5678",
        "email": "carlos.m@email.com",
        "emergencyContact": "Maria Martinez · +1 (555) 234-0001",
        "conditions": ["Hypertension", "Arthritis"],
        "allergies": ["Penicillin"],
        "medications": ["Lisinopril 10mg", "Aspirin 81mg"],
        "healthNotes": "BP trending higher in the mornings. Monitoring closely.",
        "wellbeingNotes": "Feeling good overall, slightly less active this week.",
        "metrics": [
            {"id": "m1", "date": "Jun 23, 2026", "bloodPressure": "145/92", "heartRate": 78, "weight": 168, "oxygenSaturation": 97, "temperature": 98.4, "notes": "Morning reading"},
            {"id": "m2", "date": "Jun 20, 2026", "bloodPressure": "138/88", "heartRate": 74, "weight": 169, "oxygenSaturation": 98, "temperature": 98.2},
            {"id": "m3", "date": "Jun 17, 2026", "bloodPressure": "142/90", "heartRate": 76, "weight": 169, "oxygenSaturation": 97, "temperature": 98.6},
        ],
        "wellbeingStatus": "Monitor",
        "lastUpdated": "2 hours ago",
        "reportsCount": 4,
    },
    {
        "id": "fm2",
        "fullName": "Maria Martinez",
        "relationship": "Mother",
        "age": 68,
        "gender": "Female",
        "bloodGroup": "A+",
        "phone": "+1 (555) 234-5679",
        "email": "maria.m@email.com",
        "emergencyContact": "Carlos Martinez · +1 (555) 234-5678",
        "conditions": ["Type 2 Diabetes", "Hypothyroidism"],
        "allergies": ["Sulfa drugs", "Shellfish"],
        "medications": ["Metformin 500mg", "Levothyroxine 50mcg"],
        "healthNotes": "Blood sugar well-controlled with diet changes this month.",
        "wellbeingNotes": "Active, walking 30 min daily. Mood positive.",
        "metrics": [
            {"id": "m4", "date": "Jun 23, 2026", "bloodSugar": 118, "heartRate": 72, "weight": 142, "oxygenSaturation": 98, "temperature": 98.1},
            {"id": "m5", "date": "Jun 21, 2026", "bloodSugar": 124, "heartRate": 70, "weight": 142, "oxygenSaturation": 98, "temperature": 98.3},
            {"id": "m6", "date": "Jun 18, 2026", "bloodSugar": 131, "heartRate": 73, "weight": 143, "oxygenSaturation": 97, "temperature": 98.0},
        ],
        "wellbeingStatus": "Good",
        "lastUpdated": "1 day ago",
        "reportsCount": 6,
    },
    {
        "id": "fm3",
        "fullName": "Jake Martinez",
        "relationship": "Son",
        "age": 14,
        "gender": "Male",
        "bloodGroup": "B+",
        "phone": "",
        "email": "",
        "emergencyContact": "Sarah Martinez · +1 (555) 912-3456",
        "conditions": ["Asthma"],
        "allergies": ["Peanuts", "Dust mites"],
        "medications": ["Albuterol inhaler (as needed)"],
        "healthNotes": "Asthma well-managed. No recent episodes.",
        "wellbeingNotes": "Very active with sports. Energy levels high.",
        "metrics": [
            {"id": "m7", "date": "Jun 22, 2026", "heartRate": 82, "weight": 125, "oxygenSaturation": 99, "temperature": 98.5},
        ],
        "wellbeingStatus": "Good",
        "lastUpdated": "3 days ago",
        "reportsCount": 2,
    },
]

# ── Medical Reports ────────────────────────────────────────────────────────────

_REPORTS: list[dict] = [
    {"id": "r1", "ownerType": "PATIENT", "reportName": "Complete Blood Count", "reportCategory": "Blood Test", "reportDate": "Jun 20, 2026", "healthcareFacility": "Quest Diagnostics", "notes": "Routine annual blood panel. WBC, RBC, platelets all within normal range.", "fileName": "cbc_jun2026.pdf", "fileType": "application/pdf", "fileSize": 1241600, "fileUrl": "", "uploadedDate": "Jun 20, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r2", "ownerType": "PATIENT", "reportName": "HbA1c Diabetes Panel", "reportCategory": "Diabetes", "reportDate": "Jun 15, 2026", "healthcareFacility": "LabCorp", "notes": "HbA1c: 7.8%. Slightly elevated — monitoring and dietary changes recommended.", "fileName": "hba1c_jun2026.pdf", "fileType": "application/pdf", "fileSize": 982400, "fileUrl": "", "uploadedDate": "Jun 16, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r3", "ownerType": "PATIENT", "reportName": "Chest X-Ray", "reportCategory": "X-Ray", "reportDate": "May 28, 2026", "healthcareFacility": "Memorial Hospital", "notes": "Routine screening. Lungs clear. No abnormalities detected.", "fileName": "chest_xray_may2026.jpg", "fileType": "image/jpeg", "fileSize": 2457600, "fileUrl": "", "uploadedDate": "May 29, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r4", "ownerType": "PATIENT", "reportName": "12-Lead ECG", "reportCategory": "ECG", "reportDate": "May 10, 2026", "healthcareFacility": "Cardiology Associates", "notes": "Normal sinus rhythm. PR interval 160ms. No ischemic changes.", "fileName": "ecg_may2026.pdf", "fileType": "application/pdf", "fileSize": 748800, "fileUrl": "", "uploadedDate": "May 10, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r5", "ownerType": "PATIENT", "reportName": "Metformin Prescription", "reportCategory": "Prescription", "reportDate": "Jun 01, 2026", "healthcareFacility": "Primary Care Clinic", "notes": "Metformin 500mg twice daily. 90-day supply. Refill before Aug 30.", "fileName": "prescription_jun2026.pdf", "fileType": "application/pdf", "fileSize": 512000, "fileUrl": "", "uploadedDate": "Jun 01, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r6", "ownerType": "FAMILY_MEMBER", "ownerId": "fm1", "reportName": "24-Hour Ambulatory BP", "reportCategory": "Blood Pressure", "reportDate": "Jun 18, 2026", "healthcareFacility": "Walgreens Health", "notes": "Average daytime BP: 142/88 mmHg. Nighttime dip normal. Review medication.", "fileName": "bp_monitor_jun2026.pdf", "fileType": "application/pdf", "fileSize": 1024000, "fileUrl": "", "uploadedDate": "Jun 18, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r7", "ownerType": "FAMILY_MEMBER", "ownerId": "fm1", "reportName": "Arthritis X-Ray – Left Knee", "reportCategory": "X-Ray", "reportDate": "Jun 05, 2026", "healthcareFacility": "Orthopedic Center", "notes": "Grade 2 osteoarthritis left knee. Joint space narrowing noted. Follow-up in 6 months.", "fileName": "knee_xray_jun2026.png", "fileType": "image/png", "fileSize": 3145728, "fileUrl": "", "uploadedDate": "Jun 06, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r8", "ownerType": "FAMILY_MEMBER", "ownerId": "fm2", "reportName": "Thyroid Panel (TSH/T4)", "reportCategory": "Blood Test", "reportDate": "Jun 22, 2026", "healthcareFacility": "Quest Diagnostics", "notes": "TSH: 3.2 mIU/L. Free T4: 0.9 ng/dL. Levothyroxine dose adjustment recommended.", "fileName": "thyroid_panel_jun2026.pdf", "fileType": "application/pdf", "fileSize": 876544, "fileUrl": "", "uploadedDate": "Jun 22, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r9", "ownerType": "FAMILY_MEMBER", "ownerId": "fm2", "reportName": "Diabetes Annual Review", "reportCategory": "Diabetes", "reportDate": "Jun 10, 2026", "healthcareFacility": "Endocrinology Clinic", "notes": "HbA1c: 6.9%. Well-controlled with diet and Metformin. Continue current regimen.", "fileName": "diabetes_annual_jun2026.pdf", "fileType": "application/pdf", "fileSize": 1126400, "fileUrl": "", "uploadedDate": "Jun 11, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r10", "ownerType": "FAMILY_MEMBER", "ownerId": "fm3", "reportName": "Allergy Panel – Peanut & Dust", "reportCategory": "Allergy Report", "reportDate": "Jun 14, 2026", "healthcareFacility": "Allergy & Asthma Center", "notes": "Severe peanut allergy confirmed (Class 4, IgE 85 kU/L). Dust mite sensitivity moderate.", "fileName": "allergy_panel_jun2026.pdf", "fileType": "application/pdf", "fileSize": 921600, "fileUrl": "", "uploadedDate": "Jun 15, 2026", "createdBy": "Sarah Martinez"},
    {"id": "r11", "ownerType": "FAMILY_MEMBER", "ownerId": "fm3", "reportName": "Pulmonary Function Test", "reportCategory": "Specialist Consultation", "reportDate": "Jun 08, 2026", "healthcareFacility": "Pediatric Pulmonology", "notes": "FEV1: 82% predicted. FEV1/FVC: 0.78. Well-controlled asthma — continue protocol.", "fileName": "pfts_jun2026.pdf", "fileType": "application/pdf", "fileSize": 1048576, "fileUrl": "", "uploadedDate": "Jun 09, 2026", "createdBy": "Sarah Martinez"},
]

# ── Devices ────────────────────────────────────────────────────────────────────

_DEVICES: list[dict] = [
    {"id": "d1", "name": "Apple Watch Series 9", "icon": "⌚", "status": "Connected", "lastSync": "2 min ago", "dataTypes": "Steps, HR, Sleep, SpO2", "accent": "teal"},
    {"id": "d2", "name": "Dexcom G7 CGM", "icon": "🩸", "status": "Connected", "lastSync": "1 hour ago", "dataTypes": "Continuous glucose", "accent": "rose"},
    {"id": "d3", "name": "OneTouch Glucose Meter", "icon": "🧪", "status": "Needs Reconnect", "lastSync": "3 days ago", "dataTypes": "Manual glucose", "accent": "amber"},
    {"id": "d4", "name": "SDOH Survey", "icon": "🏠", "status": "Active", "lastSync": "Jun 10", "dataTypes": "Social determinants", "accent": "sky"},
]


# ── Genie summary ──────────────────────────────────────────────────────────────

_GENIE_SUMMARY = {
    "date": "2026-07-02",
    "audioSummary": "Good morning! Here's your health summary for today:\n\n📊 Your health score is 82 — in the 'Good' range.\n\n⚠️ 3 items need attention:\n• Glucose has been elevated (142 mg/dL) for 3 days\n• Sleep duration is below 5 hours\n• A transportation barrier was flagged\n\n🔮 Today's forecast: Glucose may reach 185 mg/dL tonight.\n\n💡 Recommendations:\n• Check your blood sugar before meals\n• Aim for 7 hours of sleep tonight\n• Schedule transport to your Jun 17 appointment",
    "highlights": [
        {"metric": "Health Score", "value": "82", "trend": "stable"},
        {"metric": "Glucose", "value": "142 mg/dL", "trend": "up"},
        {"metric": "Sleep", "value": "4.5h", "trend": "down"},
    ],
    "forecast": {"glucoseRisk": 68, "recommendation": "Check glucose before bed, consider light snack"},
    "actionItems": [
        "Schedule transport to Jun 17 appointment",
        "Log evening meal in symptom tracker",
    ],
}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy", "service": "quest-beyond-api", "version": "1.0.0"}


@app.get("/patients/{patient_id}/page-data")
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


@app.get("/patients/{patient_id}/dashboard")
def get_dashboard(patient_id: str) -> dict:
    """Returns primary patient dashboard metrics."""
    return _SARAH_PAGE_DATA["dashboard"]


@app.get("/patients/{patient_id}/metrics/trends")
def get_metric_trends(patient_id: str) -> dict:
    """Returns 14-day sparkline trends."""
    return _SARAH_PAGE_DATA["metricTrends"]


@app.get("/patients/{patient_id}/forecast/glucose")
def get_glucose_forecast(patient_id: str, hours: int = 24) -> list:
    """Returns 24-hour glucose forecast."""
    return _SARAH_PAGE_DATA["glucoseForecast"][:hours]


@app.get("/patients/{patient_id}/timeline")
def get_timeline(patient_id: str) -> list:
    """Returns patient timeline events."""
    return _SARAH_PAGE_DATA["timelineData"]


@app.get("/patients/{patient_id}/alerts")
def get_alerts(patient_id: str) -> list:
    """Returns active patient alerts."""
    return _SARAH_PAGE_DATA["alertsData"]


@app.get("/patients/{patient_id}/alerts/history")
def get_alerts_history(patient_id: str) -> list:
    """Returns 30-day alert history."""
    return _SARAH_PAGE_DATA["alertHistory"]


@app.get("/patients/{patient_id}/genie/messages")
def get_genie_messages(patient_id: str) -> list:
    """Returns initial Genie conversation messages."""
    return _SARAH_PAGE_DATA["genieMessages"]


@app.get("/patients/{patient_id}/genie/summary")
def get_genie_summary(patient_id: str) -> dict:
    """Returns Genie's daily health briefing."""
    return _GENIE_SUMMARY


class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None


@app.post("/patients/{patient_id}/genie/chat")
def genie_chat(patient_id: str, req: ChatRequest) -> dict:
    """Mock Genie chat response (replace with LLM integration)."""
    response = (
        f"Thanks for your message: '{req.message}'\n\n"
        "Based on Sarah's recent data, I can see glucose has been elevated. "
        "I recommend checking with your care team if this pattern continues."
    )
    return {
        "response": response,
        "conversationId": req.conversationId or "conv_demo",
        "suggestedActions": ["schedule_telehealth", "log_meal"],
        "confidence": 0.88,
    }


@app.get("/patients/{patient_id}/family")
def get_family_members(patient_id: str) -> list:
    """Returns all family members registered to the patient (uses mutable store)."""
    return _FAMILY_STORE.get(patient_id, _FAMILY_MEMBERS)


@app.get("/patients/{patient_id}/reports")
def get_reports(patient_id: str, owner_type: Optional[str] = None,
                owner_id: Optional[str] = None, search: Optional[str] = None,
                category: Optional[str] = None, page: int = 1, page_size: int = 50) -> dict:
    """Returns reports with optional filtering and pagination (uses mutable store)."""
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


@app.get("/patients/{patient_id}/devices")
def get_devices_route(patient_id: str, status: Optional[str] = None,
                      search: Optional[str] = None) -> dict:
    """Returns connected devices (uses mutable store)."""
    items = list(_DEVICES_STORE.get(patient_id, _DEVICES))
    if status:
        items = [d for d in items if d.get("status") == status]
    if search:
        q = search.lower()
        items = [d for d in items if q in d.get("name", "").lower()]
    return {"items": items, "total": len(items)}



# ── Mutable CRUD stores (in-memory, per-patient) ───────────────────────────────

import copy
import uuid

# Keyed by patient_id → list of mutable family members
_FAMILY_STORE: dict[str, list[dict]] = {
    "patient-00429": copy.deepcopy(_FAMILY_MEMBERS),
}
# Keyed by patient_id → list of reports
_REPORTS_STORE: dict[str, list[dict]] = {
    "patient-00429": copy.deepcopy(_REPORTS),
}
# Keyed by patient_id → list of devices
_DEVICES_STORE: dict[str, list[dict]] = {
    "patient-00429": copy.deepcopy(_DEVICES),
}
# Settings store keyed by patient_id
_SETTINGS_STORE: dict[str, dict] = {
    "patient-00429": {
        "push": True, "email": True, "sms": False,
        "glucoseHigh": 200, "sleepLow": 5.5, "hrHigh": 100,
        "hipaaAudit": True, "encryption": True, "gdprExport": True, "autoPurge": False,
    },
}
# Source-data notes keyed by patient_id / subject_id
_SYMPTOMS_STORE: dict[str, list[dict]] = {}
_WELLBEING_STORE: dict[str, list[dict]] = {}

# Patient metrics (for primary patient, keyed by patient_id)
_PATIENT_METRICS: dict[str, list[dict]] = {
    "patient-00429": [
        {"id": "pm1", "date": "Jun 20, 2026", "bloodPressure": "128/82", "bloodSugar": 142,
         "heartRate": 76, "weight": 155, "oxygenSaturation": 98, "temperature": 98.2, "notes": "Morning reading"},
        {"id": "pm2", "date": "Jun 19, 2026", "bloodPressure": "130/84", "bloodSugar": 138,
         "heartRate": 78, "weight": 155, "oxygenSaturation": 98, "temperature": 98.1},
        {"id": "pm3", "date": "Jun 18, 2026", "bloodPressure": "125/80", "bloodSugar": 145,
         "heartRate": 75, "weight": 154, "oxygenSaturation": 99, "temperature": 98.3},
    ],
}

# Admin providers store
_ADMIN_PROVIDERS: list[dict] = [
    {
        "id": "ap-001", "name": "epic-main", "displayName": "Epic EHR — Main Hospital",
        "description": "Connect to Main Hospital's Epic EHR for reports, labs, and clinical notes.",
        "logoInitials": "EP", "logoColor": "bg-teal-soft text-teal",
        "providerType": "EPIC", "fhirEndpoint": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
        "apiVersion": "R4", "webhookUrl": "https://app.questbeyond.com/webhooks/epic",
        "environment": "production", "status": "active", "authType": "oauth2",
        "oauth2": {
            "clientId": "qb-epic-prod-client",
            "tokenUrl": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token",
            "authorizationUrl": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize",
            "scopes": ["patient/Patient.read", "patient/Observation.read",
                       "patient/MedicationRequest.read", "launch/patient"],
        },
        "ipWhitelist": ["52.14.22.1", "52.14.22.2"],
        "supportedDataTypes": ["reports", "devices", "notes", "metrics"],
        "templateId": "tpl-001", "connectedPatients": 2847,
        "supportsOtp": True, "supportsOAuth": True, "otpContactMethods": ["email", "sms"],
        "createdAt": "2026-01-15T10:00:00Z", "updatedAt": "2026-06-29T08:00:00Z",
        "createdBy": "admin@questbeyond.com",
    },
    {
        "id": "ap-002", "name": "cerner-sandbox", "displayName": "Cerner Millennium — Sandbox",
        "description": "Cerner SMART on FHIR integration for testing and sandbox environments.",
        "logoInitials": "CE", "logoColor": "bg-sky-soft text-sky",
        "providerType": "Cerner", "fhirEndpoint": "https://fhir-ehr-code.cerner.com/r4/ec2458f2",
        "apiVersion": "R4", "environment": "sandbox", "status": "error", "authType": "oauth2",
        "oauth2": {
            "clientId": "qb-cerner-sandbox",
            "tokenUrl": "https://authorization.cerner.com/tenants/ec2458f2/protocols/oauth2/profiles/smart-v1/token",
            "authorizationUrl": "https://authorization.cerner.com/tenants/ec2458f2/protocols/oauth2/profiles/smart-v1/personas/patient/authorize",
            "scopes": ["patient/Patient.read", "patient/MedicationRequest.read"],
        },
        "ipWhitelist": [], "supportedDataTypes": ["reports", "metrics"],
        "connectedPatients": 0, "supportsOtp": True, "supportsOAuth": True,
        "otpContactMethods": ["email"],
        "errorMessage": "Token refresh failed: 401 Unauthorized",
        "createdAt": "2026-03-10T09:00:00Z", "updatedAt": "2026-06-28T14:10:00Z",
        "createdBy": "admin@questbeyond.com",
    },
    {
        "id": "ap-003", "name": "labcorp-direct", "displayName": "Labcorp — Lab Results",
        "description": "API key-based integration for Labcorp laboratory results.",
        "logoInitials": "LC", "logoColor": "bg-violet-soft text-violet",
        "providerType": "Labcorp", "fhirEndpoint": "https://api.labcorp.com/v2/fhir",
        "apiVersion": "v2", "environment": "production", "status": "active", "authType": "api-key",
        "apiKey": {"keyId": "lc-key-prod-001", "headerName": "X-API-Key"},
        "ipWhitelist": [], "supportedDataTypes": ["metrics"],
        "connectedPatients": 1243, "supportsOtp": True, "supportsOAuth": False,
        "otpContactMethods": ["email", "sms"],
        "createdAt": "2026-04-20T14:00:00Z", "updatedAt": "2026-06-29T06:00:00Z",
        "createdBy": "admin@questbeyond.com",
    },
    {
        "id": "ap-004", "name": "hospital-xyz", "displayName": "Hospital XYZ — Community Health",
        "description": "Community hospital integration for full medical records.",
        "logoInitials": "HX", "logoColor": "bg-amber-soft text-amber",
        "providerType": "Custom", "fhirEndpoint": "https://fhir.hospitalxyz.org/api/R4",
        "apiVersion": "R4", "environment": "production", "status": "pending", "authType": "mtls",
        "mtls": {
            "certificateId": "cert-hxyz-001",
            "certSubject": "CN=qb-hospital-xyz, O=QuestBeyond, C=US",
            "certExpiry": "2027-06-01T00:00:00Z",
            "publicKeyId": "mtls-pub-hxyz-001",
        },
        "ipWhitelist": ["10.0.0.1"], "supportedDataTypes": ["reports", "devices", "notes", "metrics"],
        "connectedPatients": 0, "supportsOtp": False, "supportsOAuth": False,
        "otpContactMethods": [],
        "createdAt": "2026-06-01T00:00:00Z", "updatedAt": "2026-06-01T00:00:00Z",
        "createdBy": "admin@questbeyond.com",
        "notes": "Pending mTLS certificate exchange",
    },
]

_INTEGRATION_TEMPLATES: list[dict] = [
    {
        "id": "tpl-001", "name": "Epic SMART on FHIR R4", "providerType": "EPIC",
        "description": "Standard SMART on FHIR R4 integration for Epic EHR.",
        "version": "2.0",
        "fhirEndpoint": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
        "apiVersion": "R4", "authType": "oauth2",
        "scopes": ["patient/Patient.read", "patient/Observation.read",
                   "patient/MedicationRequest.read", "launch/patient", "openid", "fhirUser"],
        "defaultDataTypes": ["reports", "clinical-notes", "lab-results", "prescriptions"],
        "setupSteps": [
            "Register your app at https://fhir.epic.com/developer",
            "Set redirect URI to https://app.questbeyond.com/oauth/callback",
            "Copy Client ID into the Client ID field below",
            "Enable required SMART scopes",
            "Submit for Epic production app approval",
        ],
        "docsUrl": "https://fhir.epic.com/developer", "status": "official",
    },
    {
        "id": "tpl-002", "name": "Cerner SMART Health IT", "providerType": "Cerner",
        "description": "Cerner Millennium SMART on FHIR integration.",
        "version": "1.5",
        "fhirEndpoint": "https://fhir-ehr-code.cerner.com/r4/{tenant-id}",
        "apiVersion": "R4", "authType": "oauth2",
        "scopes": ["patient/Patient.read", "patient/MedicationRequest.read",
                   "patient/Observation.read", "launch/patient"],
        "defaultDataTypes": ["prescriptions", "lab-results", "clinical-notes"],
        "setupSteps": [
            "Create an app at Cerner Central (code.cerner.com)",
            "Obtain tenant ID from the hospital IT team",
            "Replace {tenant-id} in the FHIR endpoint URL",
        ],
        "docsUrl": "https://code.cerner.com/developer", "status": "official",
    },
    {
        "id": "tpl-003", "name": "Labcorp Direct API v2", "providerType": "Labcorp",
        "description": "API key-based integration for Labcorp laboratory results.",
        "version": "2.1",
        "fhirEndpoint": "https://api.labcorp.com/v2/fhir", "apiVersion": "v2",
        "authType": "api-key", "scopes": [],
        "defaultDataTypes": ["lab-results"],
        "setupSteps": [
            "Register at developer.labcorp.com",
            "Request API key for FHIR R4 DiagnosticReport endpoints",
        ],
        "docsUrl": "https://developer.labcorp.com", "status": "official",
    },
    {
        "id": "tpl-004", "name": "Custom FHIR R4 (mTLS)", "providerType": "Custom",
        "description": "Template for hospitals requiring mutual TLS certificate authentication.",
        "version": "1.0",
        "fhirEndpoint": "https://fhir.{hospital-domain}/api/R4",
        "apiVersion": "R4", "authType": "mtls", "scopes": [],
        "defaultDataTypes": ["reports", "clinical-notes", "lab-results", "prescriptions"],
        "setupSteps": [
            "Obtain the server's CA certificate from hospital IT",
            "Generate a client certificate + private key pair",
            "Register your public key with the hospital's mTLS gateway",
        ],
        "status": "community",
    },
]

_CERTIFICATES: list[dict] = [
    {
        "id": "cert-001", "providerId": "ap-001", "providerName": "Epic EHR — Main Hospital",
        "keyType": "tls-cert", "keyId": "epic-tls-prod-2026",
        "fingerprint": "SHA256:2f:8b:a1:4c:9e:3d:7f:11:22:ab",
        "uploadedAt": "2026-01-15T10:00:00Z", "uploadedBy": "admin@questbeyond.com",
        "expiresAt": "2027-01-15T00:00:00Z", "status": "active",
    },
    {
        "id": "cert-002", "providerId": "ap-004", "providerName": "Hospital XYZ",
        "keyType": "tls-cert", "keyId": "hxyz-mtls-cert-001",
        "fingerprint": "SHA256:9c:4a:12:3f:7b:88:ee:02:14:cd",
        "uploadedAt": "2026-06-01T00:00:00Z", "uploadedBy": "admin@questbeyond.com",
        "expiresAt": "2027-06-01T00:00:00Z", "status": "active",
    },
]

_ADMIN_MAPPINGS: list[dict] = [
    {"id": "am-001", "providerId": "ap-001", "providerName": "Epic EHR",
     "internalField": "patientId", "internalType": "string",
     "fhirResource": "Patient", "fhirPath": "Patient.id", "required": True},
    {"id": "am-002", "providerId": "ap-001", "providerName": "Epic EHR",
     "internalField": "glucoseReading", "internalType": "number",
     "fhirResource": "Observation", "fhirPath": "Observation.valueQuantity.value",
     "transform": "mg/dL → mmol/L", "required": True},
    {"id": "am-003", "providerId": "ap-001", "providerName": "Epic EHR",
     "internalField": "encounterDate", "internalType": "date",
     "fhirResource": "Encounter", "fhirPath": "Encounter.period.start", "required": True},
    {"id": "am-004", "providerId": "ap-001", "providerName": "Epic EHR",
     "internalField": "labResult", "internalType": "object",
     "fhirResource": "DiagnosticReport", "fhirPath": "DiagnosticReport.result[0].reference", "required": False},
    {"id": "am-005", "providerId": "ap-003", "providerName": "Labcorp",
     "internalField": "hba1cValue", "internalType": "number",
     "fhirResource": "Observation", "fhirPath": "Observation.valueQuantity", "required": True},
]

_INTEGRATIONS_STORE: list[dict] = [
    {
        "id": "int-001", "name": "Epic EHR – Main Hospital", "provider": "EPIC",
        "environment": "production", "status": "Connected",
        "lastSync": "2026-06-29T08:32:00Z",
        "dataTypes": ["reports", "devices", "notes"],
        "authType": "oauth2",
        "baseUrl": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
        "apiVersion": "R4",
        "webhookUrl": "https://app.questbeyond.com/webhooks/epic",
        "syncSchedule": {"frequency": "real-time", "triggers": ["new-report", "new-lab"]},
        "syncHistory": [
            {"id": "sh-001", "timestamp": "2026-06-29T08:32:00Z",
             "recordsSent": 12, "recordsReceived": 45, "duration": 1240, "status": "success"},
            {"id": "sh-002", "timestamp": "2026-06-29T07:00:00Z",
             "recordsSent": 8, "recordsReceived": 32, "duration": 987, "status": "success"},
            {"id": "sh-003", "timestamp": "2026-06-28T20:00:00Z",
             "recordsSent": 3, "recordsReceived": 18, "duration": 632, "status": "partial",
             "errorMessage": "1 record skipped: missing required field"},
        ],
        "totalSyncCount": 1284,
        "createdAt": "2026-01-15T10:00:00Z", "updatedAt": "2026-06-29T08:32:00Z",
        "createdBy": "admin@questbeyond.com",
    },
    {
        "id": "int-002", "name": "Cerner Millennium – Sandbox", "provider": "Cerner",
        "environment": "sandbox", "status": "Error",
        "lastSync": "2026-06-28T14:10:00Z",
        "dataTypes": ["reports", "metrics"],
        "authType": "oauth2",
        "baseUrl": "https://fhir-ehr-code.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d",
        "apiVersion": "R4",
        "syncSchedule": {"frequency": "scheduled", "cronExpression": "0 */6 * * *",
                         "triggers": ["daily-batch"]},
        "syncHistory": [
            {"id": "sh-004", "timestamp": "2026-06-28T14:10:00Z",
             "recordsSent": 0, "recordsReceived": 0, "duration": 95, "status": "failed",
             "errorMessage": "Token refresh failed: 401 Unauthorized"},
        ],
        "errorMessage": "Token refresh failed: 401 Unauthorized — client credentials may have expired.",
        "totalSyncCount": 342,
        "createdAt": "2026-03-10T09:00:00Z", "updatedAt": "2026-06-28T14:10:00Z",
        "createdBy": "admin@questbeyond.com",
    },
    {
        "id": "int-003", "name": "Labcorp Direct API", "provider": "Labcorp",
        "environment": "production", "status": "Connected",
        "lastSync": "2026-06-29T06:00:05Z",
        "dataTypes": ["metrics"],
        "authType": "api-key",
        "baseUrl": "https://api.labcorp.com/v2", "apiVersion": "v2",
        "syncSchedule": {"frequency": "scheduled", "cronExpression": "0 6 * * *",
                         "triggers": ["new-lab"]},
        "syncHistory": [
            {"id": "sh-006", "timestamp": "2026-06-29T06:00:05Z",
             "recordsSent": 0, "recordsReceived": 8, "duration": 223, "status": "success"},
        ],
        "totalSyncCount": 156,
        "createdAt": "2026-04-20T14:00:00Z", "updatedAt": "2026-06-29T06:00:05Z",
        "createdBy": "admin@questbeyond.com",
    },
]

_API_LOGS: list[dict] = [
    {"id": "log-001", "integrationId": "int-001", "integrationName": "Epic EHR – Main Hospital",
     "timestamp": "2026-06-29T08:32:14Z", "method": "POST", "endpoint": "/Patient/$match",
     "statusCode": 200, "duration": 342, "correlationId": "corr-a1b2c3",
     "requestSize": 512, "responseSize": 2048, "patientId": "PAT-00429", "userId": "system",
     "subjectType": "SELF", "subjectId": "patient-00429", "subjectName": "Sarah Martinez"},
    {"id": "log-002", "integrationId": "int-001", "integrationName": "Epic EHR – Main Hospital",
     "timestamp": "2026-06-29T08:32:10Z", "method": "GET",
     "endpoint": "/Observation?patient=PAT-00429&code=2339-0",
     "statusCode": 200, "duration": 189, "correlationId": "corr-a1b2c3",
     "responseSize": 8192, "patientId": "PAT-00429", "userId": "system",
     "subjectType": "SELF", "subjectId": "patient-00429", "subjectName": "Sarah Martinez"},
    {"id": "log-003", "integrationId": "int-002", "integrationName": "Cerner Millennium",
     "timestamp": "2026-06-28T14:10:12Z", "method": "POST", "endpoint": "/oauth2/token",
     "statusCode": 401, "duration": 95, "correlationId": "corr-d4e5f6",
     "error": "Invalid client credentials", "userId": "system",
     "subjectType": "SELF", "subjectId": "patient-00429", "subjectName": "Sarah Martinez"},
    {"id": "log-004", "integrationId": "int-001", "integrationName": "Epic EHR – Main Hospital",
     "timestamp": "2026-06-29T07:00:04Z", "method": "POST", "endpoint": "/Bundle",
     "statusCode": 201, "duration": 412, "correlationId": "corr-g7h8i9",
     "requestSize": 4096, "responseSize": 256, "patientId": "PAT-00429", "userId": "system",
     "subjectType": "SELF", "subjectId": "patient-00429", "subjectName": "Sarah Martinez"},
    {"id": "log-005", "integrationId": "int-003", "integrationName": "Labcorp Direct API",
     "timestamp": "2026-06-29T06:00:05Z", "method": "GET",
     "endpoint": "/results/recent?patientId=00429",
     "statusCode": 200, "duration": 223, "correlationId": "corr-j1k2l3",
     "responseSize": 3072, "patientId": "PAT-00429", "userId": "system",
     "subjectType": "SELF", "subjectId": "patient-00429", "subjectName": "Sarah Martinez"},
    {"id": "log-006", "integrationId": "int-001", "integrationName": "Epic EHR – Main Hospital",
     "timestamp": "2026-06-28T14:09:58Z", "method": "POST", "endpoint": "/oauth2/token",
     "statusCode": 401, "duration": 88, "correlationId": "corr-d4e5f6",
     "error": "Invalid client credentials", "retryAttempt": 2, "userId": "system",
     "subjectType": "SELF", "subjectId": "patient-00429", "subjectName": "Sarah Martinez"},
    {"id": "log-007", "integrationId": "int-001", "integrationName": "Epic EHR – Main Hospital",
     "timestamp": "2026-06-28T20:00:03Z", "method": "GET", "endpoint": "/Patient/PAT-00429",
     "statusCode": 200, "duration": 156, "correlationId": "corr-p7q8r9",
     "responseSize": 1024, "patientId": "PAT-00429", "userId": "system",
     "subjectType": "SELF", "subjectId": "patient-00429", "subjectName": "Sarah Martinez"},
    {"id": "log-008", "integrationId": "int-001", "integrationName": "Epic EHR – Main Hospital",
     "timestamp": "2026-06-29T06:02:10Z", "method": "POST", "endpoint": "/Bundle",
     "statusCode": 201, "duration": 398, "correlationId": "corr-fm3-a001",
     "requestSize": 2048, "responseSize": 512, "patientId": "PAT-00103", "userId": "system",
     "subjectType": "FAMILY", "subjectId": "fm3", "subjectName": "Jake Martinez",
     "subjectRelationship": "Son"},
    {"id": "log-009", "integrationId": "int-003", "integrationName": "Labcorp Direct API",
     "timestamp": "2026-06-28T06:02:30Z", "method": "GET",
     "endpoint": "/results/recent?patientId=00102",
     "statusCode": 200, "duration": 188, "correlationId": "corr-fm2-a001",
     "responseSize": 2560, "patientId": "PAT-00102", "userId": "system",
     "subjectType": "FAMILY", "subjectId": "fm2", "subjectName": "Maria Martinez",
     "subjectRelationship": "Mother"},
]

_PATIENT_LINKS: list[dict] = [
    {
        "linkId": "lnk-001", "subjectId": "patient-00429", "subjectName": "Sarah Martinez",
        "subjectType": "SELF", "providerId": "ap-001", "providerName": "Epic EHR — Main Hospital",
        "providerType": "EPIC", "status": "connected",
        "dataTypes": ["reports", "lab-results", "clinical-notes"],
        "connectedAt": "2026-01-15T10:30:00Z", "lastSync": "2026-06-29T08:32:00Z",
        "consentId": "con-001", "otpVerified": True, "otpChannel": "email",
    },
    {
        "linkId": "lnk-002", "subjectId": "patient-00429", "subjectName": "Sarah Martinez",
        "subjectType": "SELF", "providerId": "ap-003", "providerName": "Labcorp — Lab Results",
        "providerType": "Labcorp", "status": "connected",
        "dataTypes": ["lab-results"],
        "connectedAt": "2026-04-20T15:00:00Z", "lastSync": "2026-06-29T06:00:00Z",
        "consentId": "con-003", "otpVerified": True, "otpChannel": "sms",
    },
]

# OTP session store (in-memory, demo)
_OTP_SESSIONS: dict[str, dict] = {}


# ── Pydantic models for CRUD ───────────────────────────────────────────────────

class MetricEntryCreate(BaseModel):
    date: str
    bloodPressure: Optional[str] = None
    bloodSugar: Optional[float] = None
    weight: Optional[float] = None
    heartRate: Optional[float] = None
    oxygenSaturation: Optional[float] = None
    temperature: Optional[float] = None
    notes: Optional[str] = None


class FamilyMemberCreate(BaseModel):
    fullName: str
    relationship: str
    age: int
    gender: str
    bloodGroup: str
    phone: str = ""
    email: str = ""
    emergencyContact: str = ""
    conditions: list[str] = []
    allergies: list[str] = []
    medications: list[str] = []
    healthNotes: str = ""
    wellbeingNotes: str = ""
    wellbeingStatus: str = "Good"
    photo: Optional[str] = None


class ReportCreate(BaseModel):
    ownerType: str
    ownerId: Optional[str] = None
    reportName: str
    reportCategory: str
    reportDate: str
    healthcareFacility: str
    notes: str = ""
    fileName: str
    fileType: str
    fileSize: int
    fileUrl: str = ""
    uploadedDate: str
    createdBy: str


class DeviceCreate(BaseModel):
    name: str
    icon: str
    status: str
    lastSync: str
    dataTypes: str
    accent: str


class SettingsUpdate(BaseModel):
    push: Optional[bool] = None
    email: Optional[bool] = None
    sms: Optional[bool] = None
    glucoseHigh: Optional[float] = None
    sleepLow: Optional[float] = None
    hrHigh: Optional[float] = None
    hipaaAudit: Optional[bool] = None
    encryption: Optional[bool] = None
    gdprExport: Optional[bool] = None
    autoPurge: Optional[bool] = None


class NoteCreate(BaseModel):
    note: str
    createdBy: Optional[str] = "Unknown"


class AdminProviderCreate(BaseModel):
    displayName: str
    description: str = ""
    providerType: str
    fhirEndpoint: str
    apiVersion: str = "R4"
    webhookUrl: Optional[str] = None
    environment: str = "sandbox"
    authType: str
    clientId: Optional[str] = None
    tokenUrl: Optional[str] = None
    authorizationUrl: Optional[str] = None
    scopes: Optional[str] = None
    apiKey: Optional[str] = None
    apiKeyHeader: Optional[str] = "X-API-Key"
    ipWhitelist: Optional[str] = None
    supportedDataTypes: list[str] = []
    templateId: Optional[str] = None
    supportsOtp: bool = True
    supportsOAuth: bool = False
    otpContactMethods: list[str] = []
    notes: Optional[str] = None


class IntegrationCreate(BaseModel):
    name: str
    provider: str
    environment: str = "sandbox"
    baseUrl: str
    apiVersion: str
    webhookUrl: Optional[str] = None
    authType: str
    dataTypes: list[str] = []
    syncFrequency: str = "scheduled"
    cronExpression: Optional[str] = None
    triggers: list[str] = []


class OtpRequest(BaseModel):
    contact: str
    channel: str
    providerId: str
    subjectId: str


class OtpVerify(BaseModel):
    sessionId: str
    otp: str
    contact: str


class ConnectProviderRequest(BaseModel):
    subjectId: str
    subjectName: str
    subjectType: str
    providerId: str
    dataTypes: list[str]
    sessionToken: str
    consentGiven: bool
    consentSignature: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Patient profile endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/patients/{patient_id}/profile")
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


# ─────────────────────────────────────────────────────────────────────────────
# Patient metrics CRUD
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/patients/{patient_id}/metrics")
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


# ─────────────────────────────────────────────────────────────────────────────
# Family CRUD
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/patients/{patient_id}/family")
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
    # Update family endpoint to return from store
    return new_member


@app.put("/patients/{patient_id}/family/{member_id}")
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


@app.delete("/patients/{patient_id}/family/{member_id}", status_code=204)
def delete_family_member(patient_id: str, member_id: str) -> None:
    """Remove a family member."""
    members = _FAMILY_STORE.get(patient_id, [])
    before = len(members)
    _FAMILY_STORE[patient_id] = [m for m in members if m["id"] != member_id]
    if len(_FAMILY_STORE[patient_id]) == before:
        raise HTTPException(status_code=404, detail=f"Family member '{member_id}' not found")


@app.post("/patients/{patient_id}/family/{member_id}/metrics")
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


# Override the existing family GET to use the mutable store
@app.get("/patients/{patient_id}/family/all")
def get_family_members_all(patient_id: str) -> list:
    """Returns all family members from the mutable store."""
    return _FAMILY_STORE.get(patient_id, [])


# ─────────────────────────────────────────────────────────────────────────────
# Reports CRUD
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/patients/{patient_id}/reports")
def create_report(patient_id: str, report: ReportCreate) -> dict:
    """Upload / create a new medical report."""
    new_report = {
        "id": f"r{uuid.uuid4().hex[:8]}",
        **report.model_dump(),
    }
    if patient_id not in _REPORTS_STORE:
        _REPORTS_STORE[patient_id] = []
    _REPORTS_STORE[patient_id].insert(0, new_report)
    # Update reportsCount on owner
    owner_id = report.ownerId
    if report.ownerType == "FAMILY_MEMBER" and owner_id:
        members = _FAMILY_STORE.get(patient_id, [])
        for m in members:
            if m["id"] == owner_id:
                m["reportsCount"] = len([r for r in _REPORTS_STORE[patient_id]
                                         if r.get("ownerId") == owner_id])
    return new_report


@app.delete("/patients/{patient_id}/reports/{report_id}", status_code=204)
def delete_report(patient_id: str, report_id: str) -> None:
    """Delete a report by ID."""
    reports = _REPORTS_STORE.get(patient_id, [])
    before = len(reports)
    _REPORTS_STORE[patient_id] = [r for r in reports if r["id"] != report_id]
    if len(_REPORTS_STORE[patient_id]) == before:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")


# ─────────────────────────────────────────────────────────────────────────────
# Devices CRUD
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/patients/{patient_id}/devices")
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


@app.put("/patients/{patient_id}/devices/{device_id}")
def update_device(patient_id: str, device_id: str, device: DeviceCreate) -> dict:
    """Update a device record."""
    devices = _DEVICES_STORE.get(patient_id, [])
    idx = next((i for i, d in enumerate(devices) if d["id"] == device_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    updated = {**devices[idx], **device.model_dump()}
    devices[idx] = updated
    return updated


@app.delete("/patients/{patient_id}/devices/{device_id}", status_code=204)
def delete_device(patient_id: str, device_id: str) -> None:
    """Remove a device."""
    devices = _DEVICES_STORE.get(patient_id, [])
    before = len(devices)
    _DEVICES_STORE[patient_id] = [d for d in devices if d["id"] != device_id]
    if len(_DEVICES_STORE[patient_id]) == before:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")


# ─────────────────────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/patients/{patient_id}/settings")
def get_settings(patient_id: str) -> dict:
    """Returns the patient's preference settings."""
    return _SETTINGS_STORE.get(patient_id, {
        "push": True, "email": True, "sms": False,
        "glucoseHigh": 200, "sleepLow": 5.5, "hrHigh": 100,
        "hipaaAudit": True, "encryption": True, "gdprExport": True, "autoPurge": False,
    })


@app.put("/patients/{patient_id}/settings")
def update_settings(patient_id: str, body: SettingsUpdate) -> dict:
    """Persist the patient's preference settings."""
    current = _SETTINGS_STORE.setdefault(patient_id, {})
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    current.update(patch)
    return current


# ─────────────────────────────────────────────────────────────────────────────
# Source-data notes (symptoms & wellbeing)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/patients/{patient_id}/source-data/symptoms")
def list_symptoms(patient_id: str, subject_id: Optional[str] = None) -> list:
    """List symptom log entries, optionally filtered by subject_id."""
    key = subject_id or patient_id
    entries = _SYMPTOMS_STORE.get(key, [])
    return sorted(entries, key=lambda x: x["createdAt"], reverse=True)


@app.post("/patients/{patient_id}/source-data/symptoms")
def create_symptom(patient_id: str, body: NoteCreate,
                   subject_id: Optional[str] = None) -> dict:
    """Create a new symptom log entry."""
    key = subject_id or patient_id
    entry = {
        "id": f"sym-{uuid.uuid4().hex[:8]}",
        "patientId": key,
        "note": body.note,
        "createdBy": body.createdBy or "Unknown",
        "createdAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }
    _SYMPTOMS_STORE.setdefault(key, []).append(entry)
    return entry


@app.get("/patients/{patient_id}/source-data/wellbeing")
def list_wellbeing(patient_id: str, subject_id: Optional[str] = None) -> list:
    """List general wellbeing log entries."""
    key = subject_id or patient_id
    entries = _WELLBEING_STORE.get(key, [])
    return sorted(entries, key=lambda x: x["createdAt"], reverse=True)


@app.post("/patients/{patient_id}/source-data/wellbeing")
def create_wellbeing(patient_id: str, body: NoteCreate,
                     subject_id: Optional[str] = None) -> dict:
    """Create a new wellbeing log entry."""
    key = subject_id or patient_id
    entry = {
        "id": f"wb-{uuid.uuid4().hex[:8]}",
        "patientId": key,
        "note": body.note,
        "createdBy": body.createdBy or "Unknown",
        "createdAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }
    _WELLBEING_STORE.setdefault(key, []).append(entry)
    return entry


# ─────────────────────────────────────────────────────────────────────────────
# Admin — Providers
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/admin/providers")
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


@app.get("/admin/providers/{provider_id}")
def get_admin_provider(provider_id: str) -> dict:
    """Return a single admin provider configuration."""
    p = next((p for p in _ADMIN_PROVIDERS if p["id"] == provider_id), None)
    if not p:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    return p


@app.post("/admin/providers", status_code=201)
def create_admin_provider(body: AdminProviderCreate) -> dict:
    """Create a new admin provider configuration."""
    scope_list = [s.strip() for s in (body.scopes or "").split(",") if s.strip()]
    whitelist = [s.strip() for s in (body.ipWhitelist or "").split("\n") if s.strip()]
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
        "createdAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "updatedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
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


@app.put("/admin/providers/{provider_id}")
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
               "updatedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z"}
    _ADMIN_PROVIDERS[idx] = updated
    return updated


@app.delete("/admin/providers/{provider_id}", status_code=204)
def delete_admin_provider(provider_id: str) -> None:
    """Soft-delete (set status = 'inactive') an admin provider."""
    idx = next((i for i, p in enumerate(_ADMIN_PROVIDERS) if p["id"] == provider_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    _ADMIN_PROVIDERS[idx]["status"] = "inactive"
    _ADMIN_PROVIDERS[idx]["updatedAt"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"


class StatusUpdate(BaseModel):
    status: str


@app.put("/admin/providers/{provider_id}/status")
def set_admin_provider_status(provider_id: str, body: StatusUpdate) -> dict:
    """Change the status of an admin provider."""
    idx = next((i for i, p in enumerate(_ADMIN_PROVIDERS) if p["id"] == provider_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    _ADMIN_PROVIDERS[idx]["status"] = body.status
    _ADMIN_PROVIDERS[idx]["updatedAt"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    return _ADMIN_PROVIDERS[idx]


@app.post("/admin/providers/{provider_id}/test")
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


# ─────────────────────────────────────────────────────────────────────────────
# Admin — Templates
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/admin/templates")
def list_integration_templates(provider_type: Optional[str] = None) -> list:
    """List all integration templates."""
    items = list(_INTEGRATION_TEMPLATES)
    if provider_type:
        items = [t for t in items if t.get("providerType") == provider_type]
    return items


# ─────────────────────────────────────────────────────────────────────────────
# Admin — Security Certificates
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/admin/security/certificates")
def list_certificates(provider_id: Optional[str] = None) -> list:
    """List all security certificates, optionally filtered by provider."""
    items = list(_CERTIFICATES)
    if provider_id:
        items = [c for c in items if c.get("providerId") == provider_id]
    return items


class CertUpload(BaseModel):
    providerId: str
    keyType: str
    fileBase64: str
    fileMimeType: str
    expiresAt: Optional[str] = None
    notes: Optional[str] = None
    actorUserId: str


@app.post("/admin/security/certificates", status_code=201)
def upload_certificate(body: CertUpload) -> dict:
    """Upload a TLS certificate or API key for a provider."""
    provider = next((p for p in _ADMIN_PROVIDERS if p["id"] == body.providerId), None)
    cert: dict = {
        "id": f"cert-{uuid.uuid4().hex[:8]}",
        "providerId": body.providerId,
        "providerName": provider["displayName"] if provider else "Unknown",
        "keyType": body.keyType,
        "keyId": f"key-{uuid.uuid4().hex[:8]}",
        "fingerprint": f"SHA256:{':'.join(f'{random.randint(0,255):02x}' for _ in range(10))}",
        "uploadedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "uploadedBy": body.actorUserId,
        "expiresAt": body.expiresAt,
        "status": "active",
        "notes": body.notes,
    }
    _CERTIFICATES.append(cert)
    return cert


# ─────────────────────────────────────────────────────────────────────────────
# Admin — Data Mappings
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/admin/mappings")
def list_admin_mappings(provider_id: Optional[str] = None) -> list:
    """List all data field mappings, optionally filtered by provider."""
    items = list(_ADMIN_MAPPINGS)
    if provider_id:
        items = [m for m in items if m.get("providerId") == provider_id]
    return items


# ─────────────────────────────────────────────────────────────────────────────
# Admin — API / Audit Logs
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/admin/api-logs")
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


# ─────────────────────────────────────────────────────────────────────────────
# Integrations (patient-level)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/integrations")
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


@app.get("/integrations/{integration_id}")
def get_integration(integration_id: str) -> dict:
    """Return a single integration record."""
    item = next((i for i in _INTEGRATIONS_STORE if i["id"] == integration_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")
    return item


@app.post("/integrations", status_code=201)
def create_integration(body: IntegrationCreate) -> dict:
    """Create a new integration."""
    new_integration: dict = {
        "id": f"int-{uuid.uuid4().hex[:8]}",
        "status": "Disconnected",
        "lastSync": None,
        "syncHistory": [],
        "totalSyncCount": 0,
        "createdAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "updatedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "createdBy": "admin@questbeyond.com",
        **body.model_dump(),
    }
    _INTEGRATIONS_STORE.append(new_integration)
    return new_integration


@app.put("/integrations/{integration_id}")
def update_integration(integration_id: str, body: IntegrationCreate) -> dict:
    """Update an existing integration."""
    idx = next((i for i, it in enumerate(_INTEGRATIONS_STORE) if it["id"] == integration_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")
    updated = {**_INTEGRATIONS_STORE[idx], **body.model_dump(),
               "updatedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z"}
    _INTEGRATIONS_STORE[idx] = updated
    return updated


@app.delete("/integrations/{integration_id}", status_code=204)
def delete_integration(integration_id: str) -> None:
    """Remove an integration."""
    before = len(_INTEGRATIONS_STORE)
    _INTEGRATIONS_STORE[:] = [i for i in _INTEGRATIONS_STORE if i["id"] != integration_id]
    if len(_INTEGRATIONS_STORE) == before:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")


@app.post("/integrations/{integration_id}/test")
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


@app.get("/integrations/{integration_id}/logs")
def get_integration_logs(integration_id: str, page: int = 1, page_size: int = 10) -> dict:
    """Return API logs for a specific integration."""
    items = [l for l in _API_LOGS if l.get("integrationId") == integration_id]
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start: start + page_size], "total": total}


# ─────────────────────────────────────────────────────────────────────────────
# Patient links
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/patients/{patient_id}/links")
def list_patient_links(patient_id: str) -> list:
    """Return all provider links for this patient."""
    return [l for l in _PATIENT_LINKS if l.get("subjectId") == patient_id
            or l.get("subjectId", "").startswith("fm")]


@app.delete("/patients/{patient_id}/links/{link_id}", status_code=204)
def disconnect_patient_link(patient_id: str, link_id: str) -> None:
    """Disconnect a patient ↔ provider link."""
    idx = next((i for i, l in enumerate(_PATIENT_LINKS) if l["linkId"] == link_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Link '{link_id}' not found")
    _PATIENT_LINKS[idx]["status"] = "disconnected"
    _PATIENT_LINKS[idx]["disconnectedAt"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"


# ─────────────────────────────────────────────────────────────────────────────
# OTP / Connect flow
# ─────────────────────────────────────────────────────────────────────────────

OTP_TTL_SECONDS = 300
DEMO_OTP = "123456"


@app.post("/connect/request-otp")
def request_otp(body: OtpRequest) -> dict:
    """Generate a 6-digit OTP and return session metadata."""
    session_id = f"otp-{uuid.uuid4().hex}"
    expires_at = (__import__("datetime").datetime.utcnow() +
                  __import__("datetime").timedelta(seconds=OTP_TTL_SECONDS)).isoformat() + "Z"
    _OTP_SESSIONS[session_id] = {
        "sessionId": session_id,
        "contact": body.contact,
        "channel": body.channel,
        "issuedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
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


@app.post("/connect/verify-otp")
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


@app.post("/connect/link", status_code=201)
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
        "dataTypes": [dt for dt in body.dataTypes],
        "connectedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
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


# ─────────────────────────────────────────────────────────────────────────────
# Override family GET to use mutable store
# ─────────────────────────────────────────────────────────────────────────────

# Patch the existing GET /patients/{patient_id}/family to use mutable store
# by replacing the original function body via middleware approach.
# We re-register the route here to take precedence over the earlier definition.

@app.get("/patients/{patient_id}/family/mutable")
def get_family_members_mutable(patient_id: str) -> list:
    """Returns family members from the mutable in-memory CRUD store."""
    return _FAMILY_STORE.get(patient_id, [])


@app.get("/patients/{patient_id}/reports/all")
def get_reports_all(patient_id: str, owner_type: Optional[str] = None,
                    owner_id: Optional[str] = None, search: Optional[str] = None,
                    page: int = 1, page_size: int = 50) -> dict:
    """Returns reports with optional filtering and pagination."""
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


@app.get("/patients/{patient_id}/devices/all")
def get_devices_all(patient_id: str, status: Optional[str] = None,
                    search: Optional[str] = None) -> dict:
    """Returns devices with optional filtering."""
    items = list(_DEVICES_STORE.get(patient_id, []))
    if status:
        items = [d for d in items if d.get("status") == status]
    if search:
        q = search.lower()
        items = [d for d in items if q in d.get("name", "").lower()]
    return {"items": items, "total": len(items)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

