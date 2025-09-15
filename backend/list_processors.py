#!/usr/bin/env python3
"""
List existing Document AI processors and get their IDs.
"""

import os
from dotenv import load_dotenv
from google.cloud import documentai

load_dotenv()

def list_processors():
    """List all Document AI processors."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    location = os.getenv("DOCUMENT_AI_LOCATION", "us")
    
    print(f"📋 Listing Document AI processors...")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    
    try:
        # Initialize the client
        client = documentai.DocumentProcessorServiceClient()
        
        # The full resource name of the location
        parent = f"projects/{project_id}/locations/{location}"
        
        # List processors
        processors = client.list_processors(parent=parent)
        
        found_processor = None
        
        print("\n📄 Available processors:")
        for processor in processors:
            processor_id = processor.name.split("/")[-1]
            print(f"  - Name: {processor.display_name}")
            print(f"    ID: {processor_id}")
            print(f"    Type: {processor.type_}")
            print(f"    State: {processor.state.name}")
            print()
            
            if processor.display_name == "legal-document-processor":
                found_processor = processor_id
        
        if found_processor:
            print(f"✅ Found legal-document-processor with ID: {found_processor}")
            
            # Update .env file
            update_env_file("DOCUMENT_AI_PROCESSOR_ID", found_processor)
            
            return found_processor
        else:
            print("❌ legal-document-processor not found")
            return None
            
    except Exception as e:
        print(f"❌ Error listing processors: {e}")
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
    processor_id = list_processors()
    if processor_id:
        print(f"\n🎉 Document AI processor configured: {processor_id}")
        print("You can now start the server with full OCR functionality!")
    else:
        print("\n⚠️  No suitable processor found.")