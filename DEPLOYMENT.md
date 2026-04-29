# VoteWise Deployment Guide

This guide details how to deploy VoteWise using Google Cloud Run. 
Our repository includes a multi-stage `Dockerfile` which perfectly packages the React frontend and Node.js backend into a single, highly performant container.

## Prerequisites
1. [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed locally.
2. A Google Cloud Project with Billing enabled.
3. Cloud Run and Cloud Build APIs enabled in your Google Cloud Project.

## Deployment Steps (Google Cloud Run)

### 1. Authenticate with Google Cloud
Open your terminal and run:
```bash
gcloud auth login
```

### 2. Set your Project ID
Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID:
```bash
gcloud config set project YOUR_PROJECT_ID
```

### 3. Build and Submit the Docker Image to Container Registry
This command pushes your local code to Cloud Build, creates the Docker image, and stores it in your Google Container Registry.
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/votewise
```

### 4. Deploy to Cloud Run
Deploy the image to Cloud Run. Make sure to replace `YOUR_KEY` with your actual Gemini API key.
```bash
gcloud run deploy votewise \
  --image gcr.io/YOUR_PROJECT_ID/votewise \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars NODE_ENV=production,GEMINI_API_KEY=YOUR_KEY
```

> **Security Note:** Passing secrets via `--set-env-vars` works but is visible in the Cloud Console logs. For absolute security, it is highly recommended to use **Google Cloud Secret Manager** instead.
> 
> *Safer option:* 
> Store your key in Secret Manager as `GEMINI_API_KEY`.
> Then deploy using:
> `--set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest`

## 5. View your Application
After the deployment finishes, the terminal will output a URL (e.g., `https://votewise-xxxxxx-as.a.run.app`). Click the link to view your live application!
