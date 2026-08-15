#!/usr/bin/env bash
# Deploy Amy Team Chatbot to Google Cloud Run

# Set variables
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west1"
SERVICE_NAME="amy-chatbot"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Building Docker image..."
gcloud builds submit --tag $IMAGE

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="LLM_MODEL=gemini-2.0-flash,EMBEDDING_MODEL=text-embedding-004,ENABLE_GOOGLE_SEARCH=true" \
  --update-secrets="GOOGLE_API_KEY=google_api_key:latest"

echo "Deployment complete!"
