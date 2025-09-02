// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";
import { getAnalytics } from "firebase/analytics";

// Firebase configuration - using production values directly

// Your web app's Firebase configuration - hardcoded for now to resolve env loading issues
const firebaseConfig = {
  apiKey: "AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU",
  authDomain: "kiro-hackathon23.firebaseapp.com",
  projectId: "kiro-hackathon23",
  storageBucket: "kiro-hackathon23.firebasestorage.app",
  messagingSenderId: "1020803101475",
  appId: "1:1020803101475:web:224afc3159e5941e719296",
  measurementId: "G-VPZDRW0NGN",
};

// Debug: Log the configuration
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
let analytics: any = null;

// Initialize Firebase with real authentication
try {
  console.log('🔥 Initializing Firebase with production config...');

  // Initialize Firebase app
  app = initializeApp(firebaseConfig);

  // Initialize Firebase services
  auth = getAuth(app);
  db = getFirestore(app);
  storage = getStorage(app);

  // Initialize Analytics (optional) - disabled for now
  // if (typeof window !== 'undefined') {
  //   try {
  //     analytics = getAnalytics(app);
  //   } catch (error) {
  //     console.log('Analytics not available:', error);
  //   }
  // }

  console.log('✅ Firebase initialized successfully');
  console.log('🔥 Using real Firebase authentication for project:', firebaseConfig.projectId);
} catch (error) {
  console.error('❌ Firebase initialization failed:', error);
  
  // This likely means Firebase Authentication isn't enabled
  if (error.message.includes('auth')) {
    console.error('🚨 Firebase Authentication may not be enabled in Firebase Console');
    console.error('💡 Go to https://console.firebase.google.com/project/kiro-hackathon23/authentication');
    console.error('💡 Click "Get started" and enable Email/Password authentication');
  }
  
  throw error; // Let the error bubble up so it's visible
}

// Export Firebase services for real authentication only

export { auth, db, storage, analytics };
export default app;