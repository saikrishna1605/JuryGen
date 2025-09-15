"""
Database models and operations for Legal Companion.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class DocumentDatabase:
    """Simple SQLite database for document storage."""
    
    def __init__(self, db_path: str = "legal_companion.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                storage_url TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                status TEXT DEFAULT 'uploaded',
                user_id TEXT,
                analysis_complete BOOLEAN DEFAULT FALSE,
                risk_level TEXT,
                summary TEXT,
                extracted_text TEXT,
                clauses TEXT,
                processing_time REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # QA Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_sessions (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                confidence REAL NOT NULL,
                sources TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        # Translation history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                id TEXT PRIMARY KEY,
                source_text TEXT NOT NULL,
                target_language TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                confidence REAL,
                timestamp TEXT NOT NULL,
                user_id TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_document(self, document_data: Dict[str, Any]) -> bool:
        """Add a new document to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO documents (
                    id, filename, content_type, file_size, storage_url,
                    upload_date, status, user_id, analysis_complete,
                    risk_level, summary, extracted_text, clauses, processing_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_data.get('id'),
                document_data.get('filename'),
                document_data.get('content_type'),
                document_data.get('file_size'),
                document_data.get('storage_url'),
                document_data.get('upload_date'),
                document_data.get('status', 'uploaded'),
                document_data.get('user_id'),
                document_data.get('analysis_complete', False),
                document_data.get('risk_level'),
                document_data.get('summary'),
                document_data.get('extracted_text'),
                json.dumps(document_data.get('clauses', [])),
                document_data.get('processing_time')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
    
    def get_documents(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get documents from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute("""
                    SELECT * FROM documents WHERE user_id = ? 
                    ORDER BY upload_date DESC LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM documents 
                    ORDER BY upload_date DESC LIMIT ?
                """, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            documents = []
            
            for row in cursor.fetchall():
                doc = dict(zip(columns, row))
                if doc['clauses']:
                    try:
                        doc['clauses'] = json.loads(doc['clauses'])
                    except:
                        doc['clauses'] = []
                documents.append(doc)
            
            conn.close()
            return documents
        except Exception as e:
            print(f"Error getting documents: {e}")
            return []
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                doc = dict(zip(columns, row))
                if doc['clauses']:
                    try:
                        doc['clauses'] = json.loads(doc['clauses'])
                    except:
                        doc['clauses'] = []
                conn.close()
                return doc
            
            conn.close()
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
    
    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query dynamically
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == 'clauses' and isinstance(value, (list, dict)):
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(document_id)
            
            query = f"UPDATE documents SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False
    
    def add_qa_session(self, qa_data: Dict[str, Any]) -> bool:
        """Add a QA session to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO qa_sessions (
                    id, document_id, session_id, question, answer,
                    confidence, sources, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                qa_data.get('id'),
                qa_data.get('document_id'),
                qa_data.get('session_id'),
                qa_data.get('question'),
                qa_data.get('answer'),
                qa_data.get('confidence'),
                json.dumps(qa_data.get('sources', [])),
                qa_data.get('timestamp')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding QA session: {e}")
            return False
    
    def get_qa_history(self, document_id: str, session_id: str = "default") -> List[Dict[str, Any]]:
        """Get QA history for a document and session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM qa_sessions 
                WHERE document_id = ? AND session_id = ?
                ORDER BY timestamp ASC
            """, (document_id, session_id))
            
            columns = [desc[0] for desc in cursor.description]
            history = []
            
            for row in cursor.fetchall():
                qa = dict(zip(columns, row))
                if qa['sources']:
                    try:
                        qa['sources'] = json.loads(qa['sources'])
                    except:
                        qa['sources'] = []
                history.append(qa)
            
            conn.close()
            return history
        except Exception as e:
            print(f"Error getting QA history: {e}")
            return []

# Global database instance
db = DocumentDatabase()