#!/bin/bash
# NavGuard — Google Cloud Run Deployment Script
# Run this once to deploy everything

PROJECT_ID="navguard"
SERVICE_NAME="navguard"
REGION="us-central1"

echo "Deploying NavGuard to Google Cloud Run..."

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY

echo "Deployment complete!"
echo "Your app is live at the URL shown above."
```

---

**File 3 — `requirements.txt` update**

Open your existing `requirements.txt` and add this one line at the bottom:
```
gunicorn
eventlet