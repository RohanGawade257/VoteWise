# Deployment Guide — VoteWise

## Option 1: Local Production Test

**Frontend Build:**
```bash
cd client
npm install
npm run build
```

**Backend Start:**
```bash
cd server
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```
Then open `http://localhost:8080`.

## Option 2: Docker

**Build:**
```bash
docker build -t votewise .
```

**Run:**
```bash
docker run -p 8080:8080 --env GEMINI_API_KEY=your_key --env GEMINI_MODEL=gemini-2.5-flash-lite votewise
```

Open:
`http://localhost:8080`

## Option 3: Google Cloud Run

**Prerequisites:**
- Google Cloud SDK (`gcloud`) installed.
- A Google Cloud Project.

**Commands:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/votewise
gcloud run deploy votewise \
  --image gcr.io/YOUR_PROJECT_ID/votewise \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_MODEL=gemini-2.5-flash-lite,PORT=8080,RATE_LIMIT_ENABLED=true,CHAT_RATE_LIMIT=30/minute,ENABLE_GOOGLE_SEARCH_GROUNDING=false
```

**Important Security Note:**
Do not put your real `GEMINI_API_KEY` directly in the command if avoidable. Instead:
- Set `GEMINI_API_KEY` securely through the Cloud Run console under the Environment Variables section.
- Or use Google Cloud Secret Manager.

## Post-deployment checks
- `GET /api/health`
- `POST /api/chat`
- `/random-page` (should show frontend 404 page)
- Guided flow verification
- Safety refusal check
- Mobile view responsive test
