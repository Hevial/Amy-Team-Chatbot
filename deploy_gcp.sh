#!/usr/bin/env bash
# Deploy Amy Team Chatbot to Google Cloud Run

set -e # Exit immediately if a command exits with a non-zero status

# Configuration variables
REGION="europe-west1"
SERVICE_NAME="amy-chatbot"

echo "==========================================================="
echo "Deploying $SERVICE_NAME to Google Cloud Run"
echo "==========================================================="

# Verify project configuration
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "Error: No Google Cloud Project configured."
    echo "Please run 'gcloud config set project YOUR_PROJECT_ID' first."
    exit 1
fi
echo "Target Project: $PROJECT_ID"

echo -e "\n[1/2] Triggering Cloud Build & Deploying to Cloud Run (Serverless)..."
echo "This process compiles the React frontend and Python backend into a single unified container."

# We use --source . to let GCP handle the build-to-deploy pipeline automatically
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="ENABLE_GOOGLE_SEARCH=true" \
  --update-secrets="GOOGLE_API_KEY=google_api_key:latest"

echo -e "\n==========================================================="
echo "Deployment Complete! 🚀"
echo "Amy is now live, serving the React UI and FastAPI backend from a single serverless container."
