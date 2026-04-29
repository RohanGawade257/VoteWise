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
venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
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
| `GEMINI_API_KEY` | ✅ Yes | — | From aistudio.google.com |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Model name |
| `PORT` | No | `8080` | Server port |
| `ALLOWED_ORIGIN` | No | `http://localhost:5173` | CORS origin |
| `ENABLE_GOOGLE_SEARCH_GROUNDING` | No | `false` | Toggle live search |
