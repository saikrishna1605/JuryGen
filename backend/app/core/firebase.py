"""
Firebase Admin SDK configuration for server-side operations
"""

import os
import json
from typing import Optional
from firebase_admin import credentials, initialize_app, auth, firestore, storage
import firebase_admin
import structlog

logger = structlog.get_logger()


class FirebaseAdmin:
    """Firebase Admin SDK wrapper"""
    
    def __init__(self):
        self.app: Optional[firebase_admin.App] = None
        self.auth_client = None
        self.firestore_client = None
        self.storage_client = None
        
    def initialize(self) -> bool:
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if self.app is not None:
                return True
                
            # Get service account key from environment
            service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
            
            if service_account_key:
                # Parse JSON string
                service_account_info = json.loads(service_account_key)
                cred = credentials.Certificate(service_account_info)
            else:
                # Try to use default credentials (for local development)
                service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if service_account_path and os.path.exists(service_account_path):
                    cred = credentials.Certificate(service_account_path)
                else:
                    # Use default credentials (works in Google Cloud environments)
                    cred = credentials.ApplicationDefault()
            
            # Initialize the app
            self.app = initialize_app(cred, {
                'projectId': os.getenv('GOOGLE_CLOUD_PROJECT'),
                'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
            })
            
            # Initialize clients
            self.auth_client = auth
            self.firestore_client = firestore.client()
            self.storage_client = storage.bucket()
            
            logger.info("Firebase Admin SDK initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Firebase Admin", error=str(e))
            return False
    
    def verify_token(self, id_token: str) -> Optional[dict]:
        """Verify Firebase ID token"""
        try:
            if not self.auth_client:
                if not self.initialize():
                    return None
            
            decoded_token = self.auth_client.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            return None
    
    def get_user(self, uid: str) -> Optional[dict]:
        """Get user by UID"""
        try:
            if not self.auth_client:
                if not self.initialize():
                    return None
            
            user_record = self.auth_client.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'email_verified': user_record.email_verified,
                'disabled': user_record.disabled,
                'metadata': {
                    'creation_time': user_record.user_metadata.creation_timestamp,
                    'last_sign_in_time': user_record.user_metadata.last_sign_in_timestamp,
                }
            }
        except Exception as e:
            logger.error("Failed to get user", uid=uid, error=str(e))
            return None


# Global instance
firebase_admin = FirebaseAdmin()