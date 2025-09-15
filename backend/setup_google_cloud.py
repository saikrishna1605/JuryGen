#!/usr/bin/env python3
"""
Automated Google Cloud setup script for Legal Companion.
This script helps you set up all required Google Cloud services.
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return result.stdout.strip()
        else:
            print(f"❌ {description} - Failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return None

def check_gcloud_auth():
    """Check if gcloud is authenticated."""
    result = run_command("gcloud auth list --filter=status:ACTIVE --format='value(account)'", "Checking gcloud authentication")
    if result:
        print(f"✅ Authenticated as: {result}")
        return True
    else:
        print("❌ Not authenticated with gcloud")
        print("Run: gcloud auth login")
        return False

def get_project_id():
    """Get or set the Google Cloud project ID."""
    current_project = run_command("gcloud config get-value project", "Getting current project")
    
    if current_project and current_project != "(unset)":
        print(f"Current project: {current_project}")
        use_current = input("Use this project? (y/n): ").lower().strip()
        if use_current == 'y':
            return current_project
    
    project_id = input("Enter your Google Cloud Project ID: ").strip()
    if project_id:
        run_command(f"gcloud config set project {project_id}", f"Setting project to {project_id}")
        return project_id
    return None

def enable_apis(project_id):
    """Enable required Google Cloud APIs."""
    apis = [
        "documentai.googleapis.com",
        "storage.googleapis.com", 
        "translate.googleapis.com",
        "cloudbuild.googleapis.com"
    ]
    
    print("🔄 Enabling required APIs...")
    for api in apis:
        run_command(f"gcloud services enable {api}", f"Enabling {api}")

def create_service_account(project_id):
    """Create service account with required roles."""
    sa_name = "legal-companion-service"
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
    
    # Create service account
    run_command(
        f"gcloud iam service-accounts create {sa_name} --display-name='Legal Companion Service Account'",
        "Creating service account"
    )
    
    # Assign roles
    roles = [
        "roles/documentai.apiUser",
        "roles/storage.objectAdmin", 
        "roles/cloudtranslate.user"
    ]
    
    for role in roles:
        run_command(
            f"gcloud projects add-iam-policy-binding {project_id} --member='serviceAccount:{sa_email}' --role='{role}'",
            f"Assigning role {role}"
        )
    
    return sa_email

def create_service_account_key(sa_email, project_id):
    """Create and download service account key."""
    key_file = f"legal-companion-{project_id}-key.json"
    key_path = Path(__file__).parent / key_file
    
    result = run_command(
        f"gcloud iam service-accounts keys create {key_path} --iam-account={sa_email}",
        "Creating service account key"
    )
    
    if result is not None and key_path.exists():
        print(f"✅ Service account key saved to: {key_path}")
        return str(key_path)
    return None

def create_document_ai_processor(project_id):
    """Create Document AI processor."""
    print("🔄 Creating Document AI processor...")
    print("Please create a Document AI processor manually:")
    print("1. Go to https://console.cloud.google.com/ai/document-ai")
    print("2. Click 'Create Processor'")
    print("3. Choose 'Form Parser' or 'Document OCR'")
    print("4. Select region 'us' or 'eu'")
    print("5. Name it 'legal-document-processor'")
    
    processor_id = input("Enter the Processor ID from the console: ").strip()
    location = input("Enter the location (us/eu) [default: us]: ").strip() or "us"
    
    return processor_id, location

def create_storage_bucket(project_id):
    """Create Cloud Storage bucket."""
    bucket_name = f"{project_id}-legal-documents"
    location = "US"  # or EU
    
    # Create bucket
    result = run_command(
        f"gsutil mb -p {project_id} -c STANDARD -l {location} gs://{bucket_name}",
        f"Creating storage bucket {bucket_name}"
    )
    
    if result is not None:
        # Set bucket permissions
        run_command(
            f"gsutil uniformbucketlevelaccess set on gs://{bucket_name}",
            "Setting uniform bucket access"
        )
        
        # Set CORS policy for web uploads
        cors_config = """[
    {
      "origin": ["http://localhost:3000", "https://yourdomain.com"],
      "method": ["GET", "PUT", "POST"],
      "responseHeader": ["Content-Type"],
      "maxAgeSeconds": 3600
    }
]"""
        
        cors_file = Path(__file__).parent / "cors.json"
        with open(cors_file, 'w') as f:
            f.write(cors_config)
        
        run_command(
            f"gsutil cors set {cors_file} gs://{bucket_name}",
            "Setting CORS policy"
        )
        
        cors_file.unlink()  # Clean up
        
        return bucket_name
    
    return None

def create_env_file(project_id, key_path, processor_id, location, bucket_name):
    """Create .env file with all configuration."""
    env_content = f"""# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID={project_id}
GOOGLE_APPLICATION_CREDENTIALS={key_path}

# Document AI Configuration
DOCUMENT_AI_LOCATION={location}
DOCUMENT_AI_PROCESSOR_ID={processor_id}

# Cloud Storage Configuration
STORAGE_BUCKET_NAME={bucket_name}

# Translation API Configuration
TRANSLATION_LOCATION=global

# Database Configuration
DATABASE_URL=sqlite:///./legal_companion.db

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=true

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Firebase Configuration (add your Firebase config)
# FIREBASE_PROJECT_ID=your-firebase-project
# FIREBASE_PRIVATE_KEY_ID=your-key-id
# FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nyour-key\\n-----END PRIVATE KEY-----\\n"
# FIREBASE_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com
# FIREBASE_CLIENT_ID=your-client-id
"""

    env_path = Path(__file__).parent / ".env"
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created .env file at: {env_path}")

def install_dependencies():
    """Install required Python packages."""
    packages = [
        "google-cloud-documentai>=2.20.1",
        "google-cloud-storage>=2.10.0", 
        "google-cloud-translate>=3.12.1",
        "python-dotenv>=1.0.0",
        "sqlalchemy>=2.0.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0"
    ]
    
    print("🔄 Installing Python dependencies...")
    for package in packages:
        result = run_command(f"pip install {package}", f"Installing {package}")
        if result is None:
            print(f"⚠️  Failed to install {package}")

def main():
    """Main setup function."""
    print("🚀 Legal Companion - Full Google Cloud Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_gcloud_auth():
        print("\n❌ Please authenticate with gcloud first:")
        print("gcloud auth login")
        print("gcloud auth application-default login")
        return
    
    # Get project ID
    project_id = get_project_id()
    if not project_id:
        print("❌ Project ID is required")
        return
    
    print(f"\n🔧 Setting up project: {project_id}")
    
    # Enable APIs
    enable_apis(project_id)
    
    # Create service account
    sa_email = create_service_account(project_id)
    
    # Create service account key
    key_path = create_service_account_key(sa_email, project_id)
    if not key_path:
        print("❌ Failed to create service account key")
        return
    
    # Create Document AI processor
    processor_id, location = create_document_ai_processor(project_id)
    if not processor_id:
        print("❌ Document AI processor ID is required")
        return
    
    # Create storage bucket
    bucket_name = create_storage_bucket(project_id)
    if not bucket_name:
        print("❌ Failed to create storage bucket")
        return
    
    # Create .env file
    create_env_file(project_id, key_path, processor_id, location, bucket_name)
    
    # Install dependencies
    install_dependencies()
    
    print("\n" + "=" * 50)
    print("🎉 SETUP COMPLETE!")
    print("=" * 50)
    print(f"✅ Project: {project_id}")
    print(f"✅ Service Account: {sa_email}")
    print(f"✅ Key File: {key_path}")
    print(f"✅ Document AI Processor: {processor_id}")
    print(f"✅ Storage Bucket: {bucket_name}")
    print(f"✅ Environment file: .env")
    
    print("\n📋 Next Steps:")
    print("1. Test your setup: python test_setup.py")
    print("2. Start the server: uvicorn main:app --reload")
    print("3. Visit http://localhost:8000/docs to test APIs")
    
    print("\n⚠️  Important:")
    print("- Keep your service account key file secure")
    print("- Add Firebase configuration to .env for authentication")
    print("- Update CORS origins in storage bucket for production")

if __name__ == "__main__":
    main()