// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";
import { checkEnvironmentVariables } from "../utils/env-check";

// Check environment variables first
const envVarsLoaded = checkEnvironmentVariables();

if (!envVarsLoaded) {
  console.error('❌ Firebase environment variables check failed');
  console.error('💡 Please restart the development server after updating .env file');
  console.error('💡 Run: npm run dev (in the frontend directory)');
}

// Firebase configuration using environment variables with fallbacks
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "kiro-hackathon23.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "kiro-hackathon23",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "kiro-hackathon23.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "1020803101475",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:1020803101475:web:224afc3159e5941e719296",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-VPZDRW0NGN",
};

// Warn if using fallback values
if (!envVarsLoaded) {
  console.warn('⚠️ Using hardcoded Firebase config as fallback');
  console.warn('⚠️ This should only happen during development server startup issues');
}

// Debug: Log the configuration (safely)
console.log('Firebase Config:', {
  projectId: firebaseConfig.projectId,
  authDomain: firebaseConfig.authDomain,
  apiKey: firebaseConfig.apiKey ? `${firebaseConfig.apiKey.substring(0, 10)}...` : 'missing'
});

// Initialize Firebase
let app: any = null;
let auth: any = null;
let db: any = null;
let storage: any = null;

try {
  console.log('🔥 Initializing Firebase...');

  // Initialize Firebase app
  app = initializeApp(firebaseConfig);

  // Initialize Firebase services
  auth = getAuth(app);
  db = getFirestore(app);
  storage = getStorage(app);

  console.log('✅ Firebase initialized successfully');
  console.log('🔥 Project:', firebaseConfig.projectId);
} catch (error: any) {
  console.error('❌ Firebase initialization failed:', error);
  
  if (error?.message?.includes('auth')) {
    console.error('🚨 Firebase Authentication may not be enabled in Firebase Console');
    console.error('💡 Go to Firebase Console → Authentication → Get started');
  }
  
  throw error;
}

export { auth, db, storage };
export default app;