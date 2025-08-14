# API Documentation

This document describes the REST API endpoints for the Legal Companion backend service.

## Base URL

- Development: `http://localhost:8000/v1`
- Production: `https://your-cloud-run-url/v1`

## Authentication

All API endpoints require authentication using Firebase ID tokens.

### Headers

```
Authorization: Bearer <firebase-id-token>
Content-Type: application/json
```

### Error Responses

All endpoints may return these common error responses:

```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "request_id": "uuid-request-id"
}
```

Common error codes:
- `unauthorized`: Invalid or missing authentication token
- `forbidden`: Insufficient permissions
- `rate_limit_exceeded`: Too many requests
- `validation_error`: Invalid request data
- `internal_server_error`: Unexpected server error

## Endpoints

### Health Check

#### GET /health

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": 1699123456.789
}
```

### Document Upload

#### POST /v1/upload

Upload a legal document for analysis.

**Request:**
```json
{
  "filename": "rental-agreement.pdf",
  "content_type": "application/pdf",
  "size_bytes": 1048576,
  "jurisdiction": "california",
  "user_role": "tenant"
}
```

**Response:**
```json
{
  "job_id": "job-uuid",
  "upload_url": "https://storage.googleapis.com/signed-url",
  "expires_at": "2023-11-05T10:30:00Z"
}
```

### Job Management

#### GET /v1/jobs/{job_id}/status

Get current job processing status.

**Response:**
```json
{
  "job_id": "job-uuid",
  "status": "processing",
  "current_stage": "analysis",
  "progress_percentage": 45,
  "created_at": "2023-11-05T10:00:00Z",
  "started_at": "2023-11-05T10:01:00Z",
  "estimated_completion": "2023-11-05T10:05:00Z",
  "error_message": null
}
```

**Status Values:**
- `queued`: Job is waiting to be processed
- `processing`: Job is currently being processed
- `completed`: Job completed successfully
- `failed`: Job failed with error

**Processing Stages:**
- `upload`: Document upload
- `ocr`: Optical character recognition
- `analysis`: Clause analysis and classification
- `summarization`: Plain language summarization
- `risk_assessment`: Risk analysis and safer alternatives
- `translation`: Multi-language translation
- `audio_generation`: Text-to-speech synthesis
- `export_generation`: Export file creation

#### GET /v1/jobs/{job_id}/stream

Server-Sent Events stream for real-time job progress updates.

**Response Stream:**
```
data: {"status": "processing", "stage": "ocr", "progress": 20}

data: {"status": "processing", "stage": "analysis", "progress": 40}

data: {"status": "completed", "stage": "export_generation", "progress": 100}
```

#### POST /v1/jobs/{job_id}/analyze

Manually trigger job analysis (if not auto-triggered).

**Request:**
```json
{
  "priority": "normal",
  "options": {
    "enable_translation": true,
    "enable_audio": true,
    "target_languages": ["es", "fr"]
  }
}
```

**Response:**
```json
{
  "job_id": "job-uuid",
  "status": "queued",
  "message": "Analysis started"
}
```

### Results and Analysis

#### GET /v1/jobs/{job_id}/results

Get complete analysis results for a completed job.

**Response:**
```json
{
  "job_id": "job-uuid",
  "document": {
    "id": "doc-uuid",
    "filename": "rental-agreement.pdf",
    "pages": 5,
    "word_count": 2500
  },
  "summary": {
    "plain_language": "This rental agreement...",
    "key_points": [
      "Monthly rent is $2,000",
      "Security deposit is $4,000",
      "Lease term is 12 months"
    ],
    "reading_level": "8th grade"
  },
  "clauses": [
    {
      "id": "clause-1",
      "text": "Tenant shall pay rent...",
      "clause_number": "3.1",
      "classification": "beneficial",
      "risk_score": 0.2,
      "impact_score": 30,
      "likelihood_score": 10,
      "role_analysis": {
        "tenant": {
          "classification": "beneficial",
          "rationale": "Standard rent payment clause"
        }
      },
      "safer_alternatives": [],
      "legal_citations": [
        {
          "statute": "CA Civil Code § 1946",
          "description": "Rent payment requirements",
          "url": "https://leginfo.legislature.ca.gov/..."
        }
      ]
    }
  ],
  "risk_assessment": {
    "overall_risk": "medium",
    "high_risk_clauses": 2,
    "recommendations": [
      "Consider negotiating clause 5.2 regarding fee increases",
      "Request clarification on maintenance responsibilities"
    ]
  },
  "exports": {
    "highlighted_pdf": "https://storage.googleapis.com/signed-url-pdf",
    "summary_docx": "https://storage.googleapis.com/signed-url-docx",
    "clauses_csv": "https://storage.googleapis.com/signed-url-csv",
    "audio_narration": "https://storage.googleapis.com/signed-url-mp3",
    "transcript_srt": "https://storage.googleapis.com/signed-url-srt"
  },
  "translations": {
    "es": {
      "summary": "Este contrato de alquiler...",
      "audio_url": "https://storage.googleapis.com/signed-url-es-mp3"
    }
  }
}
```

### Voice Q&A

#### POST /v1/qa

Ask questions about analyzed documents using text or voice.

**Request (Text):**
```json
{
  "job_id": "job-uuid",
  "query": "What are the main risks in this contract?",
  "role": "tenant",
  "jurisdiction": "california",
  "locale": "en-US",
  "response_format": "text"
}
```

**Request (Voice):**
```json
{
  "job_id": "job-uuid",
  "audio_url": "https://storage.googleapis.com/signed-url-audio",
  "role": "tenant",
  "jurisdiction": "california",
  "locale": "en-US",
  "response_format": "audio"
}
```

**Response:**
```json
{
  "question": "What are the main risks in this contract?",
  "answer": "Based on my analysis, there are three main risks...",
  "confidence": 0.92,
  "sources": [
    {
      "clause_id": "clause-5",
      "clause_text": "Landlord may increase fees...",
      "relevance": 0.95
    }
  ],
  "audio_response": {
    "url": "https://storage.googleapis.com/signed-url-response-audio",
    "duration_seconds": 45,
    "transcript": "Based on my analysis, there are three main risks..."
  },
  "related_questions": [
    "How can I negotiate these risky clauses?",
    "What are my rights as a tenant?"
  ]
}
```

### Export Management

#### GET /v1/exports/{export_id}

Download generated export files.

**Response:**
- Redirects to signed Cloud Storage URL
- Or returns file content directly for small files

#### POST /v1/exports/{job_id}/generate

Generate additional export formats.

**Request:**
```json
{
  "formats": ["pdf", "docx", "csv"],
  "options": {
    "include_annotations": true,
    "highlight_risks": true,
    "language": "en"
  }
}
```

**Response:**
```json
{
  "export_id": "export-uuid",
  "status": "generating",
  "estimated_completion": "2023-11-05T10:02:00Z"
}
```

## Rate Limits

- **Upload**: 10 requests per minute per user
- **Analysis**: 5 requests per minute per user
- **Q&A**: 30 requests per minute per user
- **Export**: 20 requests per minute per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1699123456
```

## Webhooks

### Job Completion Webhook

Configure webhook URL to receive job completion notifications.

**Payload:**
```json
{
  "event": "job.completed",
  "job_id": "job-uuid",
  "status": "completed",
  "timestamp": "2023-11-05T10:05:00Z",
  "results_url": "https://api.legalcompanion.com/v1/jobs/job-uuid/results"
}
```

## SDKs and Libraries

### JavaScript/TypeScript

```typescript
import { LegalCompanionClient } from '@legal-companion/sdk';

const client = new LegalCompanionClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.legalcompanion.com/v1'
});

// Upload document
const job = await client.uploadDocument({
  file: documentFile,
  jurisdiction: 'california',
  userRole: 'tenant'
});

// Get results
const results = await client.getResults(job.jobId);
```

### Python

```python
from legal_companion import LegalCompanionClient

client = LegalCompanionClient(
    api_key='your-api-key',
    base_url='https://api.legalcompanion.com/v1'
)

# Upload document
job = client.upload_document(
    file_path='rental-agreement.pdf',
    jurisdiction='california',
    user_role='tenant'
)

# Get results
results = client.get_results(job.job_id)
```

## Error Handling

### Retry Logic

Implement exponential backoff for transient errors:

```javascript
async function retryRequest(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      if (error.status >= 500 || error.status === 429) {
        await new Promise(resolve => 
          setTimeout(resolve, Math.pow(2, i) * 1000)
        );
      } else {
        throw error;
      }
    }
  }
}
```

### Error Categories

1. **Client Errors (4xx)**:
   - Fix request format or authentication
   - Do not retry automatically

2. **Server Errors (5xx)**:
   - Temporary issues
   - Safe to retry with backoff

3. **Rate Limit (429)**:
   - Respect rate limit headers
   - Retry after specified delay

## Testing

### Test Environment

Use the test environment for development:
- Base URL: `https://api-test.legalcompanion.com/v1`
- Test documents and sample responses available
- No charges for AI service usage

### Sample Requests

See the `/examples` directory for complete request/response examples for each endpoint.