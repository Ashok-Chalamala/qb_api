# Google Health API Integration — Developer Guide

**Service:** Quest Beyond API  
**Module:** `app/routers/google_health.py`  
**Base path:** `/google-health`  
**Auth model:** OAuth 2.0 (Google Identity, Authorization Code flow with offline access)  
**Underlying API:** Google Fit REST API (Fitness v1)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Google Cloud Console Setup](#3-google-cloud-console-setup)
4. [Environment Variables](#4-environment-variables)
5. [OAuth Flow — Step by Step](#5-oauth-flow--step-by-step)
6. [API Reference](#6-api-reference)
7. [Request & Response Examples](#7-request--response-examples)
8. [Error Reference](#8-error-reference)
9. [Token Lifecycle & Refresh](#9-token-lifecycle--refresh)
10. [Scopes Reference](#10-scopes-reference)
11. [Limitations & Production Notes](#11-limitations--production-notes)

---

## 1. Architecture Overview

```
Frontend / Browser
      │
      │  1. GET /google-health/auth?patient_id=patient-00429
      ▼
Quest Beyond API  ──────────────────────────────────────────▶  Google OAuth
      │                                                          (accounts.google.com)
      │  2. Redirect → Google consent screen
      │
      │  3. User grants consent → Google calls back
      │
      ◀──────────────────────────────────────────────────────  GET /google-health/callback
      │                                                          ?code=...&state=...
      │  4. Token exchanged & stored in memory
      │     _TOKEN_STORE["patient-00429"] = { credentials }
      │
      │  5. Frontend calls data endpoints
      │     GET /google-health/steps?patient_id=patient-00429
      ▼
  Google Fit REST API  (fitness.googleapis.com)
```

Tokens are stored **in memory** — they reset on server restart. See [Limitations](#11-limitations--production-notes) for persistence options.

---

## 2. Prerequisites

### Python packages (already in `requirements.txt`)

```
requests>=2.32.0
google-auth>=2.30.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
```

Install:
```powershell
python -m pip install -r requirements.txt
```

### Required files

| File | Location | Purpose |
|------|----------|---------|
| `client_secret_*.json` | `docs/` (already present) | OAuth client credentials from Google Cloud Console |

---

## 3. Google Cloud Console Setup

### 3.1 Enable the Fitness API

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select project **questbeyond**
3. Navigate to **APIs & Services → Library**
4. Search for **"Fitness API"** → Enable it

### 3.2 Add the callback redirect URI

The current client secret only has `http://questbeyond.com` registered.  
You **must** add the local callback URL:

1. **APIs & Services → Credentials**
2. Click your OAuth 2.0 Client ID (Web application)
3. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8001/google-health/callback
   ```
4. Save. (For production, add your production domain too.)

### 3.3 OAuth consent screen

1. **APIs & Services → OAuth consent screen**
2. If in **Testing** mode, add test user emails that will grant consent
3. Scopes to add (under "Add or remove scopes"):
   - `https://www.googleapis.com/auth/fitness.activity.read`
   - `https://www.googleapis.com/auth/fitness.sleep.read`
   - `https://www.googleapis.com/auth/fitness.heart_rate.read`

---

## 4. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_CLIENT_SECRETS` | `docs/client_secret_*.json` | Path to OAuth client secret JSON file |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8001/google-health/callback` | Callback URL — must match Google Console |

Set in PowerShell before starting the server:
```powershell
$env:GOOGLE_REDIRECT_URI = "http://localhost:8001/google-health/callback"
python -m uvicorn main:app --reload --port 8001
```

---

## 5. OAuth Flow — Step by Step

### Step 1 — Initiate consent

Open in a browser (or redirect from your frontend):
```
GET http://localhost:8001/google-health/auth?patient_id=patient-00429
```

The server builds a Google OAuth URL and **302 redirects** the browser to Google's consent page.

### Step 2 — User grants consent

The user signs in with their Google account and approves the three fitness scopes.

### Step 3 — Callback

Google redirects back to:
```
GET http://localhost:8001/google-health/callback?code=4/0A...&state=patient-00429
```

The server:
- Exchanges the `code` for an access token + refresh token
- Stores credentials in `_TOKEN_STORE["patient-00429"]`
- Returns JSON confirmation

### Step 4 — Query data

```
GET http://localhost:8001/google-health/steps?patient_id=patient-00429&start_date=2026-07-01&end_date=2026-07-07
```

---

## 6. API Reference

### Auth Endpoints

#### `GET /google-health/auth`
Start the OAuth consent flow for a patient.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `patient_id` | string | ✅ | Patient ID to link to this Google account |

**Response:** `302 Redirect` → Google consent screen

---

#### `GET /google-health/callback`
Handled automatically by Google after consent. Do not call directly.

| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| `code` | string | Google | OAuth authorization code |
| `state` | string | Google | Echoed back `patient_id` |

**Response `200`:**
```json
{
  "status": "authenticated",
  "patient_id": "patient-00429",
  "message": "Google Health connected successfully. You can now call /steps, /heart-rate, /sleep."
}
```

---

#### `GET /google-health/status`
Check whether a patient has an active Google token.

| Parameter | Type | Required |
|-----------|------|----------|
| `patient_id` | string | ✅ |

**Response `200`:**
```json
{
  "patient_id": "patient-00429",
  "authenticated": true,
  "expired": false,
  "scopes": [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read"
  ]
}
```

---

#### `DELETE /google-health/disconnect`
Revoke the Google token and remove all stored credentials for a patient.

| Parameter | Type | Required |
|-----------|------|----------|
| `patient_id` | string | ✅ |

**Response `200`:**
```json
{ "status": "disconnected", "patient_id": "patient-00429" }
```

---

### Data Endpoints

All data endpoints require the patient to have completed the OAuth flow first.  
All date parameters use `YYYY-MM-DD` format in UTC.

---

#### `GET /google-health/steps`
Daily step counts from Google Fit.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `patient_id` | string | — | ✅ Required |
| `start_date` | string | `2026-07-01` | Start date (inclusive) |
| `end_date` | string | `2026-07-07` | End date (inclusive) |

**Google Fit data type:** `com.google.step_count.delta`

**Response `200`:**
```json
{
  "patient_id": "patient-00429",
  "steps": [
    { "date": "2026-07-01", "steps": 8214 },
    { "date": "2026-07-02", "steps": 6033 },
    { "date": "2026-07-03", "steps": 10421 }
  ]
}
```

---

#### `GET /google-health/heart-rate`
Daily average heart rate from Google Fit.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `patient_id` | string | — | ✅ Required |
| `start_date` | string | `2026-07-01` | Start date (inclusive) |
| `end_date` | string | `2026-07-07` | End date (inclusive) |

**Google Fit data type:** `com.google.heart_rate.bpm`

**Response `200`:**
```json
{
  "patient_id": "patient-00429",
  "heart_rate": [
    { "date": "2026-07-01", "avg_bpm": 72.4, "samples": 1240 },
    { "date": "2026-07-02", "avg_bpm": 75.1, "samples": 988 }
  ]
}
```

`avg_bpm` is `null` if no samples were recorded that day.

---

#### `GET /google-health/sleep`
Sleep sessions from Google Fit.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `patient_id` | string | — | ✅ Required |
| `start_date` | string | `2026-07-01` | Start date (inclusive) |
| `end_date` | string | `2026-07-07` | End date (inclusive) |

**Google Fit activity type filter:** `72` (sleeping)

**Response `200`:**
```json
{
  "patient_id": "patient-00429",
  "sleep_sessions": [
    {
      "name": "Sleep",
      "start": "2026-07-01T22:30:00+00:00",
      "end": "2026-07-02T06:15:00+00:00",
      "duration_minutes": 465
    }
  ]
}
```

---

## 7. Request & Response Examples

### Full integration walkthrough (curl)

```bash
# 1. Open auth URL in browser — cannot be done via curl (requires browser redirect)
# Navigate to: http://localhost:8001/google-health/auth?patient_id=patient-00429

# 2. After consent, check status
curl "http://localhost:8001/google-health/status?patient_id=patient-00429"

# 3. Fetch steps for last 7 days
curl "http://localhost:8001/google-health/steps?patient_id=patient-00429&start_date=2026-07-01&end_date=2026-07-07"

# 4. Fetch heart rate
curl "http://localhost:8001/google-health/heart-rate?patient_id=patient-00429&start_date=2026-07-01&end_date=2026-07-07"

# 5. Fetch sleep sessions
curl "http://localhost:8001/google-health/sleep?patient_id=patient-00429&start_date=2026-07-01&end_date=2026-07-07"

# 6. Disconnect
curl -X DELETE "http://localhost:8001/google-health/disconnect?patient_id=patient-00429"
```

---

## 8. Error Reference

| HTTP Status | Cause | Resolution |
|-------------|-------|------------|
| `401` | Patient has no token — OAuth not completed | Call `/google-health/auth?patient_id=<id>` first |
| `403` | Token lacks required scope | Re-authenticate; user must re-grant scopes |
| `404` | No token found for disconnect | Patient was never authenticated |
| `503` | Google Fit API returned an error | Check `detail` field; may be a quota or scope issue |

---

## 9. Token Lifecycle & Refresh

- **Access tokens** expire after ~1 hour. The server refreshes them automatically using the stored `refresh_token` before each API call.
- **Refresh tokens** are long-lived but can be revoked by the user in their Google Account settings.
- If a refresh fails (revoked token), the next data call returns `401`. The patient must re-authenticate.
- Tokens survive server restarts only if you add persistence (see below).

---

## 10. Scopes Reference

| Scope | Data accessible |
|-------|----------------|
| `fitness.activity.read` | Steps, distance, calories, active minutes |
| `fitness.sleep.read` | Sleep sessions and duration |
| `fitness.heart_rate.read` | Heart rate samples (BPM) |

To add more data types (e.g. blood pressure, weight), add the corresponding scope to the `SCOPES` list in `app/routers/google_health.py` and re-authenticate all patients.

---

## 11. Limitations & Production Notes

| Concern | Current behaviour | Production recommendation |
|---------|-------------------|--------------------------|
| **Token storage** | In-memory dict — lost on restart | Store encrypted in database (e.g. PostgreSQL with AES encryption) |
| **Multi-instance** | Tokens not shared across server instances | Use shared cache (Redis) or database |
| **REDIRECT_URI** | Hardcoded to `localhost:8001` | Set `GOOGLE_REDIRECT_URI` env var to your production domain |
| **Client secret file** | Stored in `docs/` folder | Move to secret manager (GCP Secret Manager / Azure Key Vault) in production |
| **Consent screen** | In "Testing" mode — limited to 100 test users | Submit for Google verification before public launch |
| **Rate limits** | Google Fit API: 1000 requests/day/user | Cache responses; do not call on every page load |
