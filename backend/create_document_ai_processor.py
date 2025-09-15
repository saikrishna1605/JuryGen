#!/usr/bin/env python3
"""
Script to create a Document AI processor for the Legal Companion app.
"""

import os
from dotenv import load_dotenv
from google.cloud import documentai

# Load environment variables
load_dotenv()

def create_processor():
    """Create a Document AI processor."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    location = os.getenv("DOCUMENT_AI_LOCATION", "us")
    
    print(f"🔧 Creating Document AI processor...")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    
    try:
        # Initialize the client
        client = documentai.DocumentProcessorServiceClient()
        
        # The full resource name of the location
        parent = f"projects/{project_id}/locations/{location}"
        
        # Create the processor
        processor = documentai.Processor(
            display_name="legal-document-processor",
            type_="FORM_PARSER_PROCESSOR"
        )
        
        # Make the request
        result = client.create_processor(
            parent=parent,
            processor=processor
        )
        
        print("⏳ Processor created!")
        
        # Extract processor ID from the name
        processor_id = result.name.split("/")[-1]
        
        print(f"✅ Document AI processor created successfully!")
        print(f"Processor ID: {processor_id}")
        print(f"Full name: {result.name}")
        print(f"Display name: {result.display_name}")
        print(f"Type: {result.type_}")
        
        # Update .env file
        update_env_file("DOCUMENT_AI_PROCESSOR_ID", processor_id)
        
        return processor_id
        
    except Exception as e:
        print(f"❌ Failed to create processor: {e}")
        print("You can create it manually at: https://console.cloud.google.com/ai/document-ai/processors")
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
    create_processor()