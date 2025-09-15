#!/usr/bin/env python3
"""
Setup Document AI processor manually and update configuration.
"""

import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

def create_processor_via_gcloud():
    """Create Document AI processor using gcloud CLI."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    location = "us"
    
    print("🔧 Creating Document AI processor via gcloud CLI...")
    
    try:
        # Create processor using gcloud
        cmd = [
            "gcloud", "ai", "document-ai", "processors", "create",
            "--location", location,
            "--display-name", "legal-document-processor",
            "--type", "FORM_PARSER_PROCESSOR",
            "--project", project_id,
            "--format", "value(name)"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            processor_name = result.stdout.strip()
            processor_id = processor_name.split("/")[-1]
            
            print(f"✅ Document AI processor created!")
            print(f"Processor ID: {processor_id}")
            
            # Update .env file
            update_env_file("DOCUMENT_AI_PROCESSOR_ID", processor_id)
            
            return processor_id
        else:
            print(f"❌ Failed to create processor: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def update_env_file(key, value):
    """Update a value in the .env file."""
    env_file = ".env"
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update existing key or add new one
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"{key}={value}\n")
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Updated {key} in .env file")

if __name__ == "__main__":
    processor_id = create_processor_via_gcloud()
    if processor_id:
        print(f"\n🎉 Setup complete! Processor ID: {processor_id}")
        print("You can now start the server with full OCR functionality.")
    else:
        print("\n⚠️  Manual setup required:")
        print("1. Go to: https://console.cloud.google.com/ai/document-ai/processors")
        print("2. Click 'CREATE PROCESSOR'")
        print("3. Select 'Form Parser'")
        print("4. Region: 'us'")
        print("5. Name: 'legal-document-processor'")
        print("6. Copy the processor ID and update .env file")