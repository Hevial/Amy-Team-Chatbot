<#
.SYNOPSIS
Deploys the Amy Team Chatbot to Google Cloud Run.

.DESCRIPTION
This script automates the deployment of the unified React+FastAPI container to Google Cloud Run.
It uses the modern '--source .' flag, which automatically triggers Cloud Build using our multi-stage Dockerfile
and deploys the resulting image to a serverless Cloud Run instance, skipping the need to manually manage Artifact Registry.

.PREREQUISITES
1. Authenticated with GCP: `gcloud auth login`
2. Default project set: `gcloud config set project YOUR_PROJECT_ID`
3. APIs enabled: `gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com`
4. A Secret named 'google_api_key' must exist in Secret Manager.
#>

$ErrorActionPreference = "Stop"

# Configuration variables
$Region = "europe-west1"
$ServiceName = "amy-chatbot"

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "Deploying $ServiceName to Google Cloud Run" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

# Verify project configuration
$ProjectId = gcloud config get-value project 2>$null
if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    Write-Host "Error: No Google Cloud Project configured." -ForegroundColor Red
    Write-Host "Please run 'gcloud config set project YOUR_PROJECT_ID' first." -ForegroundColor Yellow
    exit 1
}
Write-Host "Target Project: $ProjectId" -ForegroundColor Green

Write-Host "`n[1/2] Triggering Cloud Build & Deploying to Cloud Run (Serverless)..." -ForegroundColor Cyan
Write-Host "This process compiles the React frontend and Python backend into a single unified container." -ForegroundColor DarkGray

# We use --source . to let GCP handle the build-to-deploy pipeline automatically
gcloud run deploy $ServiceName `
  --source . `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --set-env-vars="ENABLE_GOOGLE_SEARCH=true" `
  --update-secrets="GOOGLE_API_KEY=google_api_key:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nDeployment Failed. Please check the Google Cloud Console for Cloud Build logs." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n===========================================================" -ForegroundColor Cyan
Write-Host "Deployment Complete! 🚀" -ForegroundColor Green
Write-Host "Amy is now live, serving the React UI and FastAPI backend from a single serverless container." -ForegroundColor Green
