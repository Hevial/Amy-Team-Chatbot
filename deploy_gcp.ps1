# Deploy Amy Team Chatbot to Google Cloud Run
$ErrorActionPreference = "Stop"

# Set variables
$ProjectId = gcloud config get-value project
$Region = "europe-west1"
$ServiceName = "amy-chatbot"
$Image = "gcr.io/$ProjectId/$ServiceName"

Write-Host "Building Docker image..." -ForegroundColor Cyan
gcloud builds submit --tag $Image

Write-Host "Deploying to Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $ServiceName `
  --image $Image `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --set-env-vars="LLM_MODEL=gemini-2.0-flash,EMBEDDING_MODEL=text-embedding-004,ENABLE_GOOGLE_SEARCH=true" `
  --update-secrets="GOOGLE_API_KEY=google_api_key:latest"

Write-Host "Deployment complete!" -ForegroundColor Green
