# Legal Companion Infrastructure
# Google Cloud Platform resources for the AI Legal Companion

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "documentai.googleapis.com",
    "translate.googleapis.com",
    "texttospeech.googleapis.com",
    "speech.googleapis.com",
    "storage.googleapis.com",
    "firestore.googleapis.com",
    "dlp.googleapis.com",
    "workflows.googleapis.com",
    "cloudtasks.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "errorreporting.googleapis.com",
  ])

  service = each.value
  project = var.project_id

  disable_dependent_services = true
}

# Cloud Storage buckets
resource "google_storage_bucket" "uploads" {
  name     = "${var.project_id}-legal-companion-uploads-${var.environment}"
  location = var.region

  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket" "outputs" {
  name     = "${var.project_id}-legal-companion-outputs-${var.environment}"
  location = var.region

  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }

  depends_on = [google_project_service.apis]
}

# KMS for encryption
resource "google_kms_key_ring" "legal_companion" {
  name     = "legal-companion-${var.environment}"
  location = var.region

  depends_on = [google_project_service.apis]
}

resource "google_kms_crypto_key" "storage_key" {
  name     = "storage-key"
  key_ring = google_kms_key_ring.legal_companion.id

  rotation_period = "7776000s" # 90 days

  depends_on = [google_project_service.apis]
}

# Firestore database
resource "google_firestore_database" "legal_companion" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.apis]
}

# Pub/Sub topics
resource "google_pubsub_topic" "job_events" {
  name = "legal-companion-job-events-${var.environment}"

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "dlq" {
  name = "legal-companion-dlq-${var.environment}"

  depends_on = [google_project_service.apis]
}

# Cloud Tasks queue
resource "google_cloud_tasks_queue" "processing_queue" {
  name     = "legal-companion-processing-${var.environment}"
  location = var.region

  rate_limits {
    max_concurrent_dispatches = 10
    max_dispatches_per_second = 5
  }

  retry_config {
    max_attempts = 3
    max_retry_duration = "300s"
    max_backoff = "60s"
    min_backoff = "5s"
    max_doublings = 3
  }

  depends_on = [google_project_service.apis]
}

# Service accounts
resource "google_service_account" "backend_sa" {
  account_id   = "legal-companion-backend-${var.environment}"
  display_name = "Legal Companion Backend Service Account"
  description  = "Service account for Legal Companion backend application"

  depends_on = [google_project_service.apis]
}

# IAM bindings for service account
resource "google_project_iam_member" "backend_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/documentai.apiUser",
    "roles/cloudtranslate.user",
    "roles/cloudtts.user",
    "roles/speech.client",
    "roles/storage.objectAdmin",
    "roles/datastore.user",
    "roles/dlp.user",
    "roles/workflows.invoker",
    "roles/cloudtasks.enqueuer",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/secretmanager.secretAccessor",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
    "roles/errorreporting.writer",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.backend_sa.email}"

  depends_on = [google_project_service.apis]
}

# Outputs
output "project_id" {
  value = var.project_id
}

output "uploads_bucket" {
  value = google_storage_bucket.uploads.name
}

output "outputs_bucket" {
  value = google_storage_bucket.outputs.name
}

output "backend_service_account" {
  value = google_service_account.backend_sa.email
}

output "processing_queue" {
  value = google_cloud_tasks_queue.processing_queue.name
}