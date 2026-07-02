# Quest Beyond — FastAPI Backend

Self-contained FastAPI backend serving all patient health data for the Quest Beyond React UI.

## Requirements

- Python 3.11+

## Setup

```bash
# From the qb_api/ directory:
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| POST | `/auth/login` | Authenticate user |
| GET | `/patients/{id}/page-data` | Full page data (`?member_id=fm1` for family) |
| GET | `/patients/{id}/dashboard` | Dashboard metrics |
| GET | `/patients/{id}/metrics/trends` | 14-day sparkline trends |
| GET | `/patients/{id}/forecast/glucose` | 24h glucose forecast |
| GET | `/patients/{id}/timeline` | Timeline events |
| GET | `/patients/{id}/devices` | Connected devices |
| GET | `/patients/{id}/alerts` | Active alerts |
| GET | `/patients/{id}/alerts/history` | 30-day alert history |
| GET | `/patients/{id}/genie/messages` | Genie chat history |
| GET | `/patients/{id}/genie/summary` | Daily health briefing |
| POST | `/patients/{id}/genie/chat` | Chat with Genie |
| GET | `/patients/{id}/family` | Family members |
| GET | `/patients/{id}/reports` | Medical reports |

## Demo Credentials

| Email | Password | Role |
|-------|----------|------|
| sarah.martinez@questbeyond.com | Patient@2026 | PATIENT |
| james.lee@questbeyond.com | Patient@2026 | PATIENT |
| admin@questbeyond.com | Admin@2026 | ADMIN |

## React Integration

Set `VITE_API_URL=http://localhost:8000` in `qb_ui/.env` and start both servers.
