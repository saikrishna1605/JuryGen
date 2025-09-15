# Google Cloud Setup for Legal Companion

This guide explains how to set up Google Cloud services for the Legal Companion application, including Document AI for OCR processing, Cloud Storage for file management, and Translation API for multi-language support.

## Prerequisites

1. Google Cloud Platform account
2. A Google Cloud project
3. Billing enabled on your project
4. Google Cloud SDK installed (optional but recommended)

## Services Required

### 1. Document AI (for OCR processing)
- **Purpose**: Extract text from PDF, DOCX, and image files
- **API**: Document AI API
- **Processor Type**: Form Parser or OCR Processor

### 2. Cloud Storage (for file storage)
- **Purpose**: Store uploaded documents and processed files
- **API**: Cloud Storage API
- **Bucket**: Private bucket with signed URL access

### 3. Translation API (for multi-language support)
- **Purpose**: Translate document content and summaries
- **API**: Cloud Translation API
- **Features**: Language detection and translation

## Step-by-Step Setup

### Step 1: Enable APIs

Enable the required APIs in your Google Cloud project:

```bash
# Enable Document AI API
gcloud services enable documentai.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage.googleapis.com

# Enable Translation API
gcloud services enable translate.googleapis.com
```

Or enable them through the Google Cloud Console:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to "APIs & Services" > "Library"
3. Search for and enable each API

### Step 2: Create a Service Account

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Name: `legal-companion-service`
4. Description: `Service account for Legal Companion application`
5. Click "Create and Continue"

### Step 3: Assign Roles

Assign the following roles to your service account:

- **Document AI User** (`roles/documentai.apiUser`)
- **Storage Object Admin** (`roles/storage.objectAdmin`)
- **Cloud Translation API User** (`roles/cloudtranslate.user`)

```bash
# Replace PROJECT_ID and SERVICE_ACCOUNT_EMAIL with your values
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/documentai.apiUser"

gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudtranslate.user"
```

### Step 4: Create and Download Service Account Key

1. In the Service Accounts page, click on your service account
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON" format
5. Download the key file and save it securely

### Step 5: Create Document AI Processor

1. Go to [Document AI Console](https://console.cloud.google.com/ai/document-ai)
2. Click "Create Processor"
3. Choose "Form Parser" or "Document OCR"
4. Select region (e.g., "us" or "eu")
5. Name your processor (e.g., "legal-document-processor")
6. Note the Processor ID from the processor details

### Step 6: Create Cloud Storage Bucket

```bash
# Create bucket (replace BUCKET_NAME with your chosen name)
gsutil mb gs://BUCKET_NAME

# Set bucket to private
gsutil iam ch allUsers:legacyObjectReader gs://BUCKET_NAME
gsutil iam ch -d allUsers:legacyObjectReader gs://BUCKET_NAME

# Enable uniform bucket-level access
gsutil uniformbucketlevelaccess set on gs://BUCKET_NAME
```

Or create through the Console:
1. Go to Cloud Storage > Buckets
2. Click "Create Bucket"
3. Choose a unique name
4. Select region
5. Choose "Uniform" access control
6. Create the bucket

### Step 7: Configure Environment Variables

Create a `.env` file in your backend directory with the following variables:

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Document AI Configuration
DOCUMENT_AI_LOCATION=us
DOCUMENT_AI_PROCESSOR_ID=your-processor-id

# Cloud Storage Configuration
STORAGE_BUCKET_NAME=your-bucket-name

# Translation API Configuration
TRANSLATION_LOCATION=global
```

### Step 8: Install Python Dependencies

Install the required Google Cloud libraries:

```bash
pip install google-cloud-documentai
pip install google-cloud-storage
pip install google-cloud-translate
```

Or add to your `requirements.txt`:

```txt
google-cloud-documentai>=2.20.1
google-cloud-storage>=2.10.0
google-cloud-translate>=3.12.1
```

## Testing the Setup

### Test Document AI

```python
from google.cloud import documentai

# Initialize client
client = documentai.DocumentProcessorServiceClient()

# Test processor access
processor_name = "projects/PROJECT_ID/locations/LOCATION/processors/PROCESSOR_ID"
try:
    processor = client.get_processor(name=processor_name)
    print(f"✅ Document AI processor accessible: {processor.display_name}")
except Exception as e:
    print(f"❌ Document AI error: {e}")
```

### Test Cloud Storage

```python
from google.cloud import storage

# Initialize client
client = storage.Client()

# Test bucket access
try:
    bucket = client.bucket("your-bucket-name")
    bucket.reload()
    print(f"✅ Cloud Storage bucket accessible: {bucket.name}")
except Exception as e:
    print(f"❌ Cloud Storage error: {e}")
```

### Test Translation API

```python
from google.cloud import translate_v2 as translate

# Initialize client
client = translate.Client()

# Test translation
try:
    result = client.translate("Hello", target_language="es")
    print(f"✅ Translation API working: {result['translatedText']}")
except Exception as e:
    print(f"❌ Translation API error: {e}")
```

## API Usage Examples

### Document Processing with OCR

```python
from backend.app.services.ocr_service import OCRService

# Initialize service
ocr_service = OCRService()

# Process document
with open("document.pdf", "rb") as f:
    file_content = f.read()

result = await ocr_service.process_document(
    file_content=file_content,
    content_type="application/pdf"
)

print(f"Extracted text: {result.text}")
print(f"Confidence: {result.confidence}")
```

### File Upload to Cloud Storage

```python
from backend.app.services.storage_service import StorageService

# Initialize service
storage_service = StorageService()

# Generate signed upload URL
upload_url, expires_at = await storage_service.generate_signed_upload_url(
    blob_name="documents/user123/doc456/contract.pdf",
    content_type="application/pdf"
)

print(f"Upload URL: {upload_url}")
```

### Document Translation

```python
from backend.app.services.translation_service import TranslationService

# Initialize service
translation_service = TranslationService()

# Translate text
result = await translation_service.translate_text(
    text="This is a legal contract",
    target_language="es",
    source_language="en"
)

print(f"Translated: {result.translated_text}")
```

## Security Best Practices

1. **Service Account Keys**: Store securely, never commit to version control
2. **Bucket Permissions**: Use signed URLs instead of public access
3. **API Quotas**: Set up monitoring and alerts for API usage
4. **Network Security**: Consider VPC and firewall rules for production
5. **Data Encryption**: Enable encryption at rest and in transit

## Cost Optimization

1. **Document AI**: Charges per page processed
2. **Cloud Storage**: Charges for storage and operations
3. **Translation API**: Charges per character translated
4. **Monitoring**: Set up billing alerts and quotas

## Troubleshooting

### Common Issues

1. **Authentication Error**: Check service account key path and permissions
2. **Processor Not Found**: Verify processor ID and region
3. **Bucket Access Denied**: Check service account roles
4. **API Not Enabled**: Ensure all required APIs are enabled

### Debug Mode

Set environment variable for detailed logging:

```bash
export GOOGLE_CLOUD_LOG_LEVEL=DEBUG
```

### Support Resources

- [Document AI Documentation](https://cloud.google.com/document-ai/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Translation API Documentation](https://cloud.google.com/translate/docs)
- [Google Cloud Support](https://cloud.google.com/support)

## Production Considerations

1. **High Availability**: Use multiple regions
2. **Scaling**: Configure auto-scaling for processing
3. **Monitoring**: Set up Cloud Monitoring and alerting
4. **Backup**: Implement backup strategies for stored documents
5. **Compliance**: Ensure GDPR/CCPA compliance for document storage

This setup provides a robust foundation for document processing, storage, and analysis using Google Cloud services.