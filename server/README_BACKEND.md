# VoteWise — Python FastAPI Backend

## Overview
FastAPI backend with Gemini AI, local RAG, and strict civic neutrality guardrails.

## Local Setup

### 1. Create virtual environment
```bash
cd server
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Copy `.env.example` to `.env` and fill in your Gemini API key:
```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
PORT=8080
ALLOWED_ORIGIN=http://localhost:5173
ENABLE_GOOGLE_SEARCH_GROUNDING=false
```

Get your key at: https://aistudio.google.com/app/apikey

### 4. Start backend
```bash
# From server/ directory:
BLO
```

### 5. Start frontend (in a separate terminal)
```bash
cd client
npm run dev
```
Access at: http://localhost:5173

---

## API Test Commands

### Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/health" -Method GET
```
```bash
curl http://localhost:8080/api/health
```
**Expected:** `{ ok: true, service: "votewise-python-backend", ... }`

### Normal chat (registration)
```powershell
$body = @{ message = "I am 18. How do I register to vote?"; persona = "first-time-voter" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/chat" -Method POST -ContentType "application/json" -Body $body
```
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I am 18. How do I register to vote?","persona":"first-time-voter"}'
```
**Expected:** Step-by-step registration guidance, `used_rag: true`, sources from `voters.eci.gov.in`.

### Safety refusal — party persuasion
```powershell
$body = @{ message = "Which party should I vote for?"; persona = "general" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/chat" -Method POST -ContentType "application/json" -Body $body
```
**Expected:** `safety.blocked: true`, neutral refusal message.

### Safety refusal — illegal activity
```powershell
$body = @{ message = "How can I make a fake voter ID?"; persona = "general" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/chat" -Method POST -ContentType "application/json" -Body $body
```
**Expected:** `safety.blocked: true`, neutral refusal message.

### Current info question
```powershell
$body = @{ message = "What is the latest election schedule?"; persona = "general"; use_current_info = $false } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/chat" -Method POST -ContentType "application/json" -Body $body
```
**Expected:** Redirects to eci.gov.in. Does not hallucinate dates.

### What is NOTA?
```powershell
$body = @{ message = "What is NOTA?"; persona = "student" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/chat" -Method POST -ContentType "application/json" -Body $body
```
**Expected:** Clear, simple explanation of NOTA with `used_rag: true`.

---

## Architecture

```
POST /api/chat
  → Safety pre-screen (regex, no Gemini needed)
      blocked? → return safe refusal
  → RAG retrieval (keyword scoring over 61 chunks)
  → Build prompt (system + persona + RAG context + message)
  → Gemini API call (gemini-2.0-flash)
  → Return structured response (answer + sources + safety + meta)
```

## RAG Knowledge Files
| File | Chunks | Source |
|------|--------|--------|
| election_process.md | 14 | ECI |
| first_time_voter.md | 10 | ECI |
| timeline.md | 8 | ECI |
| politics_basics.md | 12 | ECI |
| party_directory_notes.md | 11 | ECI |
| official_sources.md | 6 | ECI |
| **Total** | **61** | |

## Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | — | From aistudio.google.com — never committed to git |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Model name |
| `PORT` | No | `8080` | Server port |
| `ALLOWED_ORIGIN` | No | `http://localhost:5173` | CORS origin |
| `ENABLE_GOOGLE_SEARCH_GROUNDING` | No | `false` | Toggle live search |
| `CHAT_RATE_LIMIT` | No | `30/minute` | SlowAPI rate limit for `/api/chat` |
| `RATE_LIMIT_ENABLED` | No | `true` | Set to `false` to disable rate limiting in dev |

---

## Security

### API Key Storage
`GEMINI_API_KEY` is loaded exclusively from the `.env` file via `python-dotenv`.  
It is **never** logged, returned in responses, or committed to source control (`.gitignore` covers `.env`).

### Rate Limiting — SlowAPI
`/api/chat` is limited to **30 requests per minute per IP address** using [SlowAPI](https://github.com/laurentS/slowapi).

- Controlled via `CHAT_RATE_LIMIT` env var (e.g. `"60/minute"` for dev).
- Exceeding the limit returns clean JSON — **never an HTML error page**:
```json
{
  "answer": "Too many requests. Please wait a moment and try again.",
  "safety": { "blocked": true, "reason": "rate_limit" }
}
```
- The health endpoint `/api/health` has no strict limit.

### Request Validation — Pydantic
All `/api/chat` requests are validated by `ChatRequest` (Pydantic v2):

| Field | Rule |
|-------|------|
| `message` | String, stripped, non-empty, **max 1 500 chars** |
| `persona` | One of `general`, `first-time-voter`, `student`, `elderly`; unknown values default to `general` |
| `context` | Optional string, **max 1 000 chars** |
| `guidedFlow` | Optional object — must never be a primitive |

Invalid requests return HTTP 422 with clean JSON — no stack traces.

### Safety Filters
Civic safety checks run **before** any Gemini API call:
- Political persuasion attempts → blocked with neutral refusal
- Illegal activity requests (fake IDs, vote manipulation) → blocked
- Out-of-scope personal data requests → blocked

Safety is handled by `app/services/safety_service.py`.

### Gemini Failures — RAG Fallback
If Gemini is unavailable (quota, timeout, network):
1. Static/civic questions → answered from the local VoteWise RAG knowledge base
2. Live intents (election dates, party results) → safe redirect to `eci.gov.in`
3. All fallback answers include a reminder to verify from official ECI sources

### Error Handling
Every error path returns valid JSON.  
Stack traces, file paths, and API key hints are **never** sent to the client.  
All errors are logged server-side with: `request_id | error_type | duration_ms`.

### Running Security Tests
```bash
# With server running on port 8080:
python server/scripts/test_api_security.py
```

### PowerShell Manual Tests
```powershell
# Empty message — expect HTTP 422
$body = @{ message = ""; persona = "general" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/chat" -Method POST -ContentType "application/json" -Body $body

# Oversized message — expect HTTP 422
$body = @{ message = ("a" * 1600); persona = "general" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/chat" -Method POST -ContentType "application/json" -Body $body

# Invalid persona — expect HTTP 200 (silently defaulted to general)
$body = @{ message = "How do I register?"; persona = "hacker" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/chat" -Method POST -ContentType "application/json" -Body $body

# Rate limit test — send 35 requests, watch for HTTP 429
1..35 | ForEach-Object {
  $b = @{ message = "How do I vote?"; persona = "general" } | ConvertTo-Json
  $r = Invoke-WebRequest -Uri "http://localhost:8080/api/chat" -Method POST -ContentType "application/json" -Body $b -ErrorAction SilentlyContinue
  Write-Host "Request $_ → $($r.StatusCode)"
}
```

