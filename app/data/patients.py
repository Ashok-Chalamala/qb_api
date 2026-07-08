from typing import Any

from app.helpers import _generate_forecast, _alert_history

# ── Auth users ─────────────────────────────────────────────────────────────────

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

# ── Sarah Martinez page data ───────────────────────────────────────────────────

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

# ── Carlos Martinez page data ──────────────────────────────────────────────────

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

# ── Maria Martinez page data ───────────────────────────────────────────────────

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

# ── Jake Martinez page data ────────────────────────────────────────────────────

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

# ── Member data map ────────────────────────────────────────────────────────────

_MEMBER_DATA_MAP: dict[str, dict] = {
    "primary": _SARAH_PAGE_DATA,
    "fm1": _CARLOS_PAGE_DATA,
    "fm2": _MARIA_PAGE_DATA,
    "fm3": _JAKE_PAGE_DATA,
}

# ── Genie daily summary ────────────────────────────────────────────────────────

_GENIE_SUMMARY: dict = {
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

# ── Patient metrics seed data ──────────────────────────────────────────────────

PATIENT_METRICS_SEED: dict[str, list[dict]] = {
    "patient-00429": [
        {"id": "pm1", "date": "Jun 20, 2026", "bloodPressure": "128/82", "bloodSugar": 142,
         "heartRate": 76, "weight": 155, "oxygenSaturation": 98, "temperature": 98.2, "notes": "Morning reading"},
        {"id": "pm2", "date": "Jun 19, 2026", "bloodPressure": "130/84", "bloodSugar": 138,
         "heartRate": 78, "weight": 155, "oxygenSaturation": 98, "temperature": 98.1},
        {"id": "pm3", "date": "Jun 18, 2026", "bloodPressure": "125/80", "bloodSugar": 145,
         "heartRate": 75, "weight": 154, "oxygenSaturation": 99, "temperature": 98.3},
    ],
}
