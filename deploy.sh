#!/bin/bash
set -e

# =============================================================================
# Tendly Agent Chat - Manual Deploy Script
# Deploys to Google Cloud Run (service)
# =============================================================================

# Configuration
GCP_PROJECT_ID="scenic-impact-476918-n6"
GCP_REGION="europe-north1"
REPOSITORY="tendly-agent-chat"
IMAGE_NAME="tendly-agent-chat"

# Parse arguments
ENVIRONMENT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./deploy.sh --environment <dev|staging|prod>"
            exit 1
            ;;
    esac
done

if [ -z "$ENVIRONMENT" ]; then
    echo "Error: --environment is required"
    echo "Usage: ./deploy.sh --environment <dev|staging|prod>"
    exit 1
fi

# Validate environment
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "prod" ]]; then
    echo "Error: environment must be one of: dev, staging, prod"
    exit 1
fi

# Set service name and secret env based on environment
case "$ENVIRONMENT" in
    prod)
        SERVICE_NAME="tendly-agent-chat"
        CLOUD_SQL_INSTANCE_NAME="tendly-prod"
        DB_NAME="tendly_prod"
        SECRET_ENV="prod"
        MAX_INSTANCES=3
        ;;
    staging)
        SERVICE_NAME="tendly-agent-chat-staging"
        CLOUD_SQL_INSTANCE_NAME="tendly-dev"
        DB_NAME="tendly_dev"
        SECRET_ENV="dev"
        MAX_INSTANCES=2
        ;;
    dev)
        SERVICE_NAME="tendly-agent-chat-dev"
        CLOUD_SQL_INSTANCE_NAME="tendly-dev"
        DB_NAME="tendly_dev"
        SECRET_ENV="dev"
        MAX_INSTANCES=2
        ;;
esac

CLOUD_SQL_INSTANCE="${GCP_PROJECT_ID}:${GCP_REGION}:${CLOUD_SQL_INSTANCE_NAME}"

echo "============================================"
echo "  Tendly Agent Chat - Deploy"
echo "============================================"
echo "Environment:  $ENVIRONMENT"
echo "Service:      $SERVICE_NAME"
echo "Region:       $GCP_REGION"
echo "Database:     $DB_NAME on $CLOUD_SQL_INSTANCE_NAME"
echo "Secrets:      tendly-${SECRET_ENV}-* (from Secret Manager)"
echo "============================================"
echo ""

# Step 1: Check gcloud auth
echo "Checking gcloud authentication..."
if ! gcloud auth print-identity-token &>/dev/null; then
    echo "Error: Not authenticated with gcloud. Run 'gcloud auth login' first."
    exit 1
fi

# Ensure correct project
gcloud config set project $GCP_PROJECT_ID --quiet

echo "Authenticated with project: $GCP_PROJECT_ID"

# Step 2: Configure Docker for Artifact Registry
echo ""
echo "Configuring Docker for Artifact Registry..."
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev --quiet

# Step 3: Create Artifact Registry repository if not exists
echo ""
echo "Ensuring Artifact Registry repository exists..."
gcloud artifacts repositories describe $REPOSITORY \
    --location=$GCP_REGION \
    --project=$GCP_PROJECT_ID 2>/dev/null || \
gcloud artifacts repositories create $REPOSITORY \
    --repository-format=docker \
    --location=$GCP_REGION \
    --project=$GCP_PROJECT_ID \
    --description="Tendly Agent Chat Docker images"

# Step 4: Build and push Docker image
SHORT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
TIMESTAMP=$(date +%Y%m%d%H%M%S)
IMAGE_TAG="${SHORT_SHA}-${TIMESTAMP}"
IMAGE_URI="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"
IMAGE_URI_LATEST="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest"

echo ""
echo "Building Docker image..."
echo "  Tag: $IMAGE_TAG"
docker build -t $IMAGE_URI -t $IMAGE_URI_LATEST .

echo ""
echo "Pushing Docker image..."
docker push $IMAGE_URI
docker push $IMAGE_URI_LATEST

# Step 5: Deploy Cloud Run service
echo ""
echo "Deploying Cloud Run service: $SERVICE_NAME"
echo "  Secrets from Secret Manager: tendly-${SECRET_ENV}-*"

gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_URI \
    --region=$GCP_REGION \
    --platform=managed \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=$MAX_INSTANCES \
    --concurrency=80 \
    --timeout=300 \
    --port=8080 \
    --allow-unauthenticated \
    --add-cloudsql-instances=$CLOUD_SQL_INSTANCE \
    --set-env-vars="USE_GCP_CLOUD_SQL=true,CLOUD_SQL_INSTANCE=$CLOUD_SQL_INSTANCE,DB_NAME=$DB_NAME,DB_USER=tendly_admin,ENVIRONMENT=$ENVIRONMENT" \
    --set-secrets="DB_PASSWORD=tendly-${SECRET_ENV}-db-password:latest,GEMINI_API_KEY=tendly-${SECRET_ENV}-gemini-api-key:latest" \
    --labels="environment=$ENVIRONMENT"

# Step 6: Show deployed URL
echo ""
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$GCP_REGION \
    --format='value(status.url)')

echo "============================================"
echo "  DEPLOYMENT COMPLETE!"
echo "============================================"
echo "Environment:  $ENVIRONMENT"
echo "Service:      $SERVICE_NAME"
echo "Image:        $IMAGE_TAG"
echo "URL:          $SERVICE_URL"
echo "============================================"
