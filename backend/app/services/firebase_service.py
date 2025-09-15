"""
Firebase Firestore service for real-time document storage and management.
"""

import os
import uuid
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import firebase_admin
from firebase_admin import credentials, firestore as admin_firestore

class FirebaseService:
    """Service class for Firebase Firestore operations."""
    
    def __init__(self):
        """Initialize Firebase service."""
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Use service account key for initialization
                cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./service-account-key.json")
                
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app