# Deployment Guide

This guide covers deploying the Legal Companion application to Google Cloud Platform.

## Prerequisites

- Google Cloud Platform account with billing enabled
- `gcloud` CLI installed and configured
- Terraform installed (>= 1.0)
- Node.js 18+ and npm
- Python 3.11+
- Firebase CLI installed

## Infrastructure Setup

### 1. Enable APIs and Set Up Project

```bash
# Set your project ID
export PROJECT_ID="your-legal-companion-project"
export REGION="us-central1"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs (this may take a few minutes)
gcloud services enable \
  aiplatform.googleapis.com \
  documentai.googleapis.com \
  translate.googleapis.com \
  texttospeech.googleapis.com \
  speech.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com \
  dlp.googleapis.com \
  workflows.googleapis.com \
  cloudtasks.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  errorreporting.googleapis.com
```

### 2. Deploy Infrastructure with Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION"

# Apply the infrastructure
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION"
```

### 3. Set Up Firebase

```bash
# Install Firebase CLI if not already installed
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in the frontend directory
cd frontend
firebase init

# Select:
# - Hosting
# - Use existing project (select your GCP project)
# - Set public directory to 'dist'
# - Configure as single-page app: Yes
# - Set up automatic builds with GitHub: Optional
```

## Application Deployment

### 1. Backend Deployment

```bash
# Build and deploy backend to Cloud Run
cd backend

# Build Docker image
docker build -t gcr.io/$PROJECT_ID/legal-companion-backend .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/legal-companion-backend

# Deploy to Cloud Run
gcloud run deploy legal-companion-backend \
  --image gcr.io/$PROJECT_ID/legal-companion-backend \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 100 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10
```

### 2. Frontend Deployment

```bash
cd frontend

# Install dependencies
npm install

# Build the application
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting
```

## Environment Configuration

### 1. Backend Environment Variables

Create secrets in Secret Manager:

```bash
# Create secrets for sensitive configuration
gcloud secrets create firebase-private-key --data-file=path/to/firebase-private-key.json
gcloud secrets create gemini-api-key --data-file=path/to/gemini-api-key.txt

# Update Cloud Run service with environment variables
gcloud run services update legal-companion-backend \
  --region $REGION \
  --set-env-vars ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --set-secrets FIREBASE_PRIVATE_KEY=firebase-private-key:latest,GEMINI_API_KEY=gemini-api-key:latest
```

### 2. Frontend Environment Variables

Update Firebase Hosting configuration:

```bash
# Set environment variables for frontend
firebase functions:config:set \
  firebase.api_key="your-firebase-api-key" \
  firebase.auth_domain="$PROJECT_ID.firebaseapp.com" \
  firebase.project_id="$PROJECT_ID"
```

## AI Services Setup

### 1. Document AI Processor

```bash
# Create Document AI processor
gcloud documentai processors create \
  --location=us \
  --display-name="Legal Document Processor" \
  --type=FORM_PARSER_PROCESSOR
```

### 2. Vertex AI Vector Search

```bash
# Create Vector Search index (requires data preparation)
gcloud ai indexes create \
  --region=$REGION \
  --display-name="Legal Clauses Index" \
  --description="Vector index for legal clause similarity search"
```

## Monitoring and Logging

### 1. Set Up Monitoring

```bash
# Create monitoring dashboard
gcloud monitoring dashboards create --config-from-file=monitoring/dashboard.json
```

### 2. Configure Alerting

```bash
# Create alerting policies
gcloud alpha monitoring policies create --policy-from-file=monitoring/alerts.yaml
```

## Security Configuration

### 1. Set Up Cloud Armor

```bash
# Create security policy
gcloud compute security-policies create legal-companion-policy \
  --description "Security policy for Legal Companion"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy legal-companion-policy \
  --expression "true" \
  --action "rate-based-ban" \
  --rate-limit-threshold-count 100 \
  --rate-limit-threshold-interval-sec 60 \
  --ban-duration-sec 600
```

### 2. Configure VPC Service Controls (Optional)

```bash
# Create service perimeter for additional security
gcloud access-context-manager perimeters create legal-companion-perimeter \
  --policy=your-access-policy-id \
  --title="Legal Companion Perimeter" \
  --resources=projects/$PROJECT_ID \
  --restricted-services=aiplatform.googleapis.com,storage.googleapis.com
```

## Testing Deployment

### 1. Health Checks

```bash
# Test backend health
curl https://legal-companion-backend-[hash]-uc.a.run.app/health

# Test frontend
curl https://your-project-id.web.app
```

### 2. End-to-End Testing

```bash
# Run E2E tests against deployed environment
cd frontend
npm run test:e2e -- --baseUrl=https://your-project-id.web.app
```

## Scaling and Performance

### 1. Auto-scaling Configuration

The Cloud Run service is configured with:
- Min instances: 0 (cost-effective)
- Max instances: 10 (adjust based on expected load)
- Concurrency: 100 requests per instance
- Memory: 2Gi per instance
- CPU: 2 vCPUs per instance

### 2. Performance Optimization

- Enable CDN for static assets
- Configure appropriate caching headers
- Use Cloud Storage for large file uploads
- Implement request batching for AI services

## Cost Optimization

### 1. Resource Management

- Use Gemini 1.5 Flash for classification tasks
- Reserve Gemini 1.5 Pro for complex analysis
- Implement caching for repeated analyses
- Set up lifecycle policies for storage buckets

### 2. Monitoring Costs

```bash
# Set up budget alerts
gcloud billing budgets create \
  --billing-account=your-billing-account-id \
  --display-name="Legal Companion Budget" \
  --budget-amount=100USD \
  --threshold-rules-percent=0.5,0.9 \
  --threshold-rules-spend-basis=CURRENT_SPEND
```

## Troubleshooting

### Common Issues

1. **Cloud Run deployment fails**: Check service account permissions
2. **Firebase deployment fails**: Verify Firebase project configuration
3. **AI services timeout**: Increase Cloud Run timeout settings
4. **Storage access denied**: Check bucket IAM permissions

### Logs and Debugging

```bash
# View Cloud Run logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# View Cloud Build logs
gcloud builds list --limit=10

# View Firestore operations
gcloud logging read "resource.type=gce_instance" --limit=50
```

## Maintenance

### 1. Regular Updates

- Update dependencies monthly
- Monitor security advisories
- Update AI model versions
- Review and rotate secrets

### 2. Backup and Recovery

- Firestore automatic backups are enabled
- Cloud Storage versioning is configured
- Export critical configuration regularly

### 3. Performance Monitoring

- Monitor response times and error rates
- Review AI service usage and costs
- Analyze user behavior and optimize UX

## Support

For deployment issues:
1. Check the troubleshooting section above
2. Review Google Cloud documentation
3. Check application logs in Cloud Logging
4. Contact support team with specific error messages