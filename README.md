# VoteWise

VoteWise is a neutral civic education assistant that helps Indian citizens understand voter registration, election timelines, polling-day steps, and democracy basics through guided flows and AI assistance.

## Chosen Vertical
Civic Education / First-Time Voter Assistance

## Problem Statement
Many Indian citizens, especially first-time voters, struggle to understand voter registration, election timelines, polling-day requirements, and basic civic concepts. Existing information is often scattered across official portals, PDFs, and long documents.

## Solution
VoteWise provides a simple, neutral, guided assistant that explains the Indian election process through:
- guided first-time voter flow
- election timeline
- election process map
- AI-powered chat
- RAG-backed fallback knowledge base
- contextual follow-up handling
- persona-based explanation modes

## Approach and Logic
VoteWise adopts an LLM-first intent routing architecture to provide accurate, context-aware civic guidance. Rather than relying on rigid keyword matching, the system uses an LLM classifier to determine the user's precise civic intent (e.g., definitional, procedural, or live civic). Based on this classification, the system dynamically routes the query to the most reliable response mechanism:
- A registry of verified direct answers for precise definitions to prevent hallucination.
- A local RAG system for retrieving static, foundational knowledge.
- A grounded Gemini generation pipeline for nuanced, context-aware responses.
A strict safety layer pre-screens all inputs to ensure absolute political neutrality before processing.

## Key Features
- Guided first-time voter assistant
- Context-aware follow-up answers
- Election timeline
- Election process map
- First-time voter guide
- Political basics
- National parties directory
- Local help / BLO-related guidance
- Gemini-powered assistant
- RAG fallback from local VoteWise knowledge base
- Persona modes:
  - General
  - First-Time Voter
  - School Student
  - Elderly
- Safety guardrails:
  - no party recommendations
  - no propaganda
  - no illegal voting help
  - official-source redirects
- Accessibility:
  - text size
  - high contrast
  - keyboard-friendly controls
- Responsive UI
- Custom 404 page
- Rate limiting and input validation

## Google Services Used
- Gemini API — AI-powered civic explanations
- Google Cloud Run — deployment target

## Architecture
**Frontend:**
- React
- Vite
- Tailwind/CSS
- React Router

**Backend:**
- FastAPI
- Gemini service
- LLM Classifier service
- Direct Answer Registry
- RAG service
- Answer Verifier
- Guided flow service
- Tone service
- Safety service
- Conversation context service
- SlowAPI rate limiter
- Pydantic validation

## Folder Structure
```text
VoteWise/
├── client/              # React frontend
│   ├── public/          # Static assets
│   └── src/             # React source (components, hooks, pages)
└── server/              # FastAPI backend
    ├── app/             # Application code (routes, services, models)
    ├── scripts/         # Testing and utility scripts
    └── requirements.txt # Python dependencies
```

## How It Works
1. User asks question or starts guided flow.
2. Safety filter runs first to block harmful or partisan content.
3. LLM Classifier detects the specific civic intent of the query.
4. Direct Answer Registry handles precise definitional queries immediately to prevent hallucination.
5. Guided/context flow checks whether it is a voter journey follow-up.
6. RAG retrieves relevant civic knowledge for grounding.
7. Gemini generates the final answer, utilizing grounded context and verifying the response.
8. Current/dynamic election data redirects to official ECI sources.

## Setup Instructions

### Prerequisites
- Node.js
- Python 3.11+
- Gemini API key
- Google Cloud SDK (optional for deployment)

### Frontend
```bash
cd client
npm install
npm run dev
```

### Backend
```bash
cd server
python -m venv venv
venv\Scripts\activate   # On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # On Mac/Linux: cp .env.example .env
# add GEMINI_API_KEY to .env
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

### Production Build
```bash
cd client
npm run build
```

## Environment Variables
- `GEMINI_API_KEY`: API key for Google Gemini model.
- `GEMINI_MODEL`: Model version to use (e.g., `gemini-2.5-flash-lite`).
- `PORT`: Port for FastAPI backend.
- `ALLOWED_ORIGIN`: CORS allowed origin.
- `ENABLE_GOOGLE_SEARCH_GROUNDING`: Whether to use Google Search grounding.
- `APP_TIMEZONE`: Timezone for temporal intent classification.
- `CHAT_RATE_LIMIT`: SlowAPI rate limit for chat API.
- `RATE_LIMIT_ENABLED`: Global rate limiting switch.

## API Endpoints
- `GET /api/health`: Health check endpoint.
- `POST /api/chat`: Chat interaction endpoint.

## Testing Checklist
- Home loads
- All routes load
- 404 route works
- Chat works
- Guided first-time voter flow works
- Context follow-up works:
  - What is Form 6?
  - What should I do next?
  - What ID do I carry?
  - What is BLO?
- Safety blocks:
  - Which party should I vote for?
  - How to make fake voter ID?
- Input validation:
  - empty message
  - long message
- Rate limiting
- Mobile responsive at 320px/375px/768px/1366px
- Accessibility controls
- No console errors

## Security
- API key stored in env only
- `.env` ignored
- rate limiting
- input validation
- safe error responses
- no sensitive personal data collection
- safety filter before Gemini

## Official Sources
- https://eci.gov.in
- https://voters.eci.gov.in
- https://electoralsearch.eci.gov.in
- official party websites only for party directory

## Assumptions
- **Geographic & Civic Scope:** The platform is specifically tailored to the Indian democratic system and electoral process.
- **Language:** The current version assumes interactions are primarily in English.
- **Knowledge Stability:** We assume foundational civic concepts remain static and can be reliably served via our local RAG knowledge base, while live or dynamic election data is best handled by redirecting to official ECI sources.
- **Safety Precedence:** We assume that maintaining strict political neutrality is paramount. The system is designed to conservatively block ambiguous, highly subjective, or sensitive queries rather than risk generating biased or propagandist content.

## Limitations
- educational only
- not official ECI service
- cannot verify actual voter registration
- cannot provide legal guarantees
- current dates/deadlines must be verified from official sources
- does not endorse or oppose parties

## Deployment
See [DEPLOYMENT.md](./DEPLOYMENT.md).

## Live Demo
Coming soon.

## GitHub Repository
[Insert Repo URL Here]