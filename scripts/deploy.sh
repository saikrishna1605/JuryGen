#!/bin/bash

# Deployment script for AI Legal Companion
# Supports multiple environments and deployment strategies

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
DEPLOYMENT_TYPE="${2:-cloud-run}"
STRATEGY="${3:-rolling}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if required tools are installed
    local tools=("gcloud" "docker" "kubectl")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check if authenticated with Google Cloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with Google Cloud. Run 'gcloud auth login'"
        exit 1
    fi
    
    # Check if project is set
    if [[ -z "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
        log_error "GOOGLE_CLOUD_PROJECT environment variable is not set"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Load environment configuration
load_config() {
    local config_file="$PROJECT_ROOT/deployment/config/$ENVIRONMENT.env"
    
    if [[ -f "$config_file" ]]; then
        log_info "Loading configuration from $config_file"
        # shellcheck source=/dev/null
        source "$config_file"
    else
        log_warning "Configuration file $config_file not found, using defaults"
    fi
    
    # Set defaults
    REGION="${REGION:-us-central1}"
    BACKEND_SERVICE_NAME="${BACKEND_SERVICE_NAME:-ai-legal-companion-backend}"
    FRONTEND_SERVICE_NAME="${FRONTEND_SERVICE_NAME:-ai-legal-companion-frontend}"
    
    if [[ "$ENVIRONMENT" != "production" ]]; then
        BACKEND_SERVICE_NAME="${BACKEND_SERVICE_NAME}-${ENVIRONMENT}"
        FRONTEND_SERVICE_NAME="${FRONTEND_SERVICE_NAME}-${ENVIRONMENT}"
    fi
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    local commit_sha
    commit_sha=$(git rev-parse --short HEAD)
    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)
    
    # Build backend image
    log_info "Building backend image..."
    docker build \
        -t "gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-backend:$commit_sha" \
        -t "gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-backend:$ENVIRONMENT-latest" \
        --target production \
        "$PROJECT_ROOT/backend"
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build \
        -t "gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-frontend:$commit_sha" \
        -t "gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-frontend:$ENVIRONMENT-latest" \
        --target production \
        --build-arg "VITE_API_URL=${BACKEND_URL:-https://api.ai-legal-companion.com}" \
        --build-arg "VITE_GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" \
        "$PROJECT_ROOT/frontend"
    
    # Push images
    log_info "Pushing images to Container Registry..."
    docker push "gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-backend:$commit_sha"
    docker push "gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-backend:$ENVIRONMENT-latest"
    docker push "gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-frontend:$commit_sha"
    docker push "gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-frontend:$ENVIRONMENT-latest"
    
    log_success "Images built and pushed successfully"
    
    # Export image tags for use in deployment
    export BACKEND_IMAGE="gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-backend:$commit_sha"
    export FRONTEND_IMAGE="gcr.io/$GOOGLE_CLOUD_PROJECT/ai-legal-companion-frontend:$commit_sha"
}

# Deploy to Cloud Run
deploy_cloud_run() {
    log_info "Deploying to Cloud Run..."
    
    # Deploy backend
    log_info "Deploying backend service..."
    gcloud run deploy "$BACKEND_SERVICE_NAME" \
        --image "$BACKEND_IMAGE" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --set-env-vars "ENVIRONMENT=$ENVIRONMENT,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" \
        --memory "${BACKEND_MEMORY:-2Gi}" \
        --cpu "${BACKEND_CPU:-2}" \
        --concurrency "${BACKEND_CONCURRENCY:-80}" \
        --min-instances "${BACKEND_MIN_INSTANCES:-1}" \
        --max-instances "${BACKEND_MAX_INSTANCES:-100}" \
        --timeout "${BACKEND_TIMEOUT:-300}" \
        --quiet
    
    # Deploy frontend
    log_info "Deploying frontend service..."
    gcloud run deploy "$FRONTEND_SERVICE_NAME" \
        --image "$FRONTEND_IMAGE" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --memory "${FRONTEND_MEMORY:-512Mi}" \
        --cpu "${FRONTEND_CPU:-1}" \
        --concurrency "${FRONTEND_CONCURRENCY:-1000}" \
        --min-instances "${FRONTEND_MIN_INSTANCES:-1}" \
        --max-instances "${FRONTEND_MAX_INSTANCES:-50}" \
        --timeout "${FRONTEND_TIMEOUT:-60}" \
        --quiet
    
    log_success "Cloud Run deployment completed"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Set kubectl context
    gcloud container clusters get-credentials "$GKE_CLUSTER_NAME" --region "$REGION"
    
    # Create namespace if it doesn't exist
    kubectl create namespace ai-legal-companion --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    log_info "Applying Kubernetes configurations..."
    
    # Substitute environment variables in YAML files
    envsubst < "$PROJECT_ROOT/deployment/k8s/backend-deployment.yaml" | kubectl apply -f -
    envsubst < "$PROJECT_ROOT/deployment/k8s/frontend-deployment.yaml" | kubectl apply -f -
    
    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment/ai-legal-companion-backend -n ai-legal-companion
    kubectl wait --for=condition=available --timeout=600s deployment/ai-legal-companion-frontend -n ai-legal-companion
    
    log_success "Kubernetes deployment completed"
}

# Canary deployment strategy
deploy_canary() {
    log_info "Performing canary deployment..."
    
    if [[ "$DEPLOYMENT_TYPE" == "cloud-run" ]]; then
        # Deploy with canary tag
        gcloud run deploy "$BACKEND_SERVICE_NAME" \
            --image "$BACKEND_IMAGE" \
            --platform managed \
            --region "$REGION" \
            --tag canary \
            --no-traffic \
            --quiet
        
        gcloud run deploy "$FRONTEND_SERVICE_NAME" \
            --image "$FRONTEND_IMAGE" \
            --platform managed \
            --region "$REGION" \
            --tag canary \
            --no-traffic \
            --quiet
        
        # Route 10% traffic to canary
        log_info "Routing 10% traffic to canary..."
        gcloud run services update-traffic "$BACKEND_SERVICE_NAME" \
            --to-tags canary=10 \
            --region "$REGION"
        
        gcloud run services update-traffic "$FRONTEND_SERVICE_NAME" \
            --to-tags canary=10 \
            --region "$REGION"
        
        # Wait for monitoring
        log_info "Waiting 5 minutes for monitoring..."
        sleep 300
        
        # Increase to 50%
        log_info "Increasing traffic to 50%..."
        gcloud run services update-traffic "$BACKEND_SERVICE_NAME" \
            --to-tags canary=50 \
            --region "$REGION"
        
        gcloud run services update-traffic "$FRONTEND_SERVICE_NAME" \
            --to-tags canary=50 \
            --region "$REGION"
        
        # Wait again
        sleep 300
        
        # Full rollout
        log_info "Completing rollout to 100%..."
        gcloud run services update-traffic "$BACKEND_SERVICE_NAME" \
            --to-tags canary=100 \
            --region "$REGION"
        
        gcloud run services update-traffic "$FRONTEND_SERVICE_NAME" \
            --to-tags canary=100 \
            --region "$REGION"
    fi
    
    log_success "Canary deployment completed"
}

# Blue-green deployment strategy
deploy_blue_green() {
    log_info "Performing blue-green deployment..."
    
    # This would implement blue-green deployment logic
    # For now, fall back to rolling deployment
    log_warning "Blue-green deployment not fully implemented, using rolling deployment"
    deploy_rolling
}

# Rolling deployment strategy
deploy_rolling() {
    log_info "Performing rolling deployment..."
    
    case "$DEPLOYMENT_TYPE" in
        "cloud-run")
            deploy_cloud_run
            ;;
        "kubernetes")
            deploy_kubernetes
            ;;
        *)
            log_error "Unknown deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Get service URLs
    if [[ "$DEPLOYMENT_TYPE" == "cloud-run" ]]; then
        local backend_url
        backend_url=$(gcloud run services describe "$BACKEND_SERVICE_NAME" --region="$REGION" --format='value(status.url)')
        local frontend_url
        frontend_url=$(gcloud run services describe "$FRONTEND_SERVICE_NAME" --region="$REGION" --format='value(status.url)')
        
        # Health check backend
        log_info "Checking backend health at $backend_url/health"
        if curl -f "$backend_url/health" > /dev/null 2>&1; then
            log_success "Backend health check passed"
        else
            log_error "Backend health check failed"
            return 1
        fi
        
        # Health check frontend
        log_info "Checking frontend health at $frontend_url/health"
        if curl -f "$frontend_url/health" > /dev/null 2>&1; then
            log_success "Frontend health check passed"
        else
            log_error "Frontend health check failed"
            return 1
        fi
    fi
    
    log_success "All health checks passed"
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    if [[ "$DEPLOYMENT_TYPE" == "cloud-run" ]]; then
        # Get previous revision
        local backend_revisions
        backend_revisions=$(gcloud run revisions list --service="$BACKEND_SERVICE_NAME" --region="$REGION" --format='value(metadata.name)' --limit=2)
        local frontend_revisions
        frontend_revisions=$(gcloud run revisions list --service="$FRONTEND_SERVICE_NAME" --region="$REGION" --format='value(metadata.name)' --limit=2)
        
        # Get second revision (previous)
        local backend_previous
        backend_previous=$(echo "$backend_revisions" | sed -n '2p')
        local frontend_previous
        frontend_previous=$(echo "$frontend_revisions" | sed -n '2p')
        
        if [[ -n "$backend_previous" && -n "$frontend_previous" ]]; then
            log_info "Rolling back to previous revision..."
            
            gcloud run services update-traffic "$BACKEND_SERVICE_NAME" \
                --to-revisions "$backend_previous=100" \
                --region "$REGION"
            
            gcloud run services update-traffic "$FRONTEND_SERVICE_NAME" \
                --to-revisions "$frontend_previous=100" \
                --region "$REGION"
            
            log_success "Rollback completed"
        else
            log_error "No previous revision found for rollback"
            return 1
        fi
    fi
}

# Main deployment function
main() {
    log_info "Starting deployment to $ENVIRONMENT using $DEPLOYMENT_TYPE with $STRATEGY strategy"
    
    check_prerequisites
    load_config
    build_and_push_images
    
    case "$STRATEGY" in
        "rolling")
            deploy_rolling
            ;;
        "canary")
            deploy_canary
            ;;
        "blue-green")
            deploy_blue_green
            ;;
        *)
            log_error "Unknown deployment strategy: $STRATEGY"
            exit 1
            ;;
    esac
    
    # Run health checks
    if ! run_health_checks; then
        log_error "Health checks failed, consider rolling back"
        if [[ "${AUTO_ROLLBACK:-false}" == "true" ]]; then
            rollback
        fi
        exit 1
    fi
    
    log_success "Deployment completed successfully!"
    
    # Print service URLs
    if [[ "$DEPLOYMENT_TYPE" == "cloud-run" ]]; then
        local backend_url
        backend_url=$(gcloud run services describe "$BACKEND_SERVICE_NAME" --region="$REGION" --format='value(status.url)')
        local frontend_url
        frontend_url=$(gcloud run services describe "$FRONTEND_SERVICE_NAME" --region="$REGION" --format='value(status.url)')
        
        log_info "Service URLs:"
        log_info "  Backend:  $backend_url"
        log_info "  Frontend: $frontend_url"
    fi
}

# Handle script arguments
case "${1:-}" in
    "rollback")
        check_prerequisites
        load_config
        rollback
        ;;
    "health-check")
        check_prerequisites
        load_config
        run_health_checks
        ;;
    *)
        main
        ;;
esac