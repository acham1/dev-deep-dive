#!/bin/bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT:-dev-deep-dive}"
REGION="${GCP_REGION:-us-central1}"
TOPIC="deep-dive-trigger"
SECRET_NAME="environment-variables"

echo "Deploying to project: $PROJECT_ID, region: $REGION"

# Create Pub/Sub topic (idempotent)
gcloud pubsub topics create "$TOPIC" --project="$PROJECT_ID" 2>/dev/null || true

# Deploy generate_report function
echo "Deploying generate-report function..."
gcloud functions deploy generate-report \
    --gen2 \
    --runtime=python312 \
    --region="$REGION" \
    --source=functions/generate_report \
    --entry-point=generate_report \
    --trigger-topic="$TOPIC" \
    --timeout=900s \
    --memory=1Gi \
    --set-env-vars="GCP_PROJECT=$PROJECT_ID,SITE_URL=${SITE_URL:-https://acham1.github.io/dev-deep-dive},HOSTING_BUCKET=${HOSTING_BUCKET:-$PROJECT_ID.firebasestorage.app}" \
    --set-secrets="/etc/secrets/.env=$SECRET_NAME:latest" \
    --project="$PROJECT_ID"

# Deploy API function
echo "Deploying api function..."
gcloud functions deploy api \
    --gen2 \
    --runtime=python312 \
    --region="$REGION" \
    --source=functions/api \
    --entry-point=api \
    --trigger-http \
    --allow-unauthenticated \
    --timeout=60s \
    --memory=256Mi \
    --set-env-vars="GCP_PROJECT=$PROJECT_ID" \
    --set-secrets="/etc/secrets/.env=$SECRET_NAME:latest" \
    --project="$PROJECT_ID"

# Create/update Cloud Scheduler job
echo "Configuring Cloud Scheduler..."
gcloud scheduler jobs delete deep-dive-weekly \
    --location="$REGION" --project="$PROJECT_ID" --quiet 2>/dev/null || true
gcloud scheduler jobs create pubsub deep-dive-weekly \
    --location="$REGION" \
    --schedule="${SCHEDULE:-0 7 * * MON}" \
    --time-zone="${TIMEZONE:-America/Los_Angeles}" \
    --topic="$TOPIC" \
    --message-body='{}' \
    --project="$PROJECT_ID"

API_URL="https://$REGION-$PROJECT_ID.cloudfunctions.net/api"
echo ""
echo "Deployment complete!"
echo "API: $API_URL"
echo ""
echo "IMPORTANT: Update DEEP_DIVE_API_BASE in the frontend HTML files to: $API_URL"
