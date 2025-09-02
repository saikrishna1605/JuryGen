# Firebase Authentication Fix Guide

## Current Status
❌ Firebase API key is invalid: `auth/api-key-not-valid`
✅ Demo mode enabled - authentication works with mock data
🔧 Need to fix Firebase configuration for production

## Quick Fix (Already Applied)
I've enabled demo mode so your app works immediately:
- Login/signup works with any email/password (6+ characters)
- User sessions are maintained
- All features work except real Firebase services

## Step-by-Step Firebase Fix

### Step 1: Check Firebase Console
1. Go to https://console.firebase.google.com/
2. Open project `kiro-hackathon23`
3. Check if there are any warnings or errors
4. Verify project is active (not suspended)

### Step 2: Enable Firebase Authentication
1. In Firebase Console, click "Authentication" in sidebar
2. If you see "Get started", click it
3. Go to "Sign-in method" tab
4. Enable "Email/Password" provider:
   - Toggle "Enable" to ON
   - Click "Save"

### Step 3: Get Fresh API Configuration
1. In Firebase Console, click gear icon (⚙️) → "Project settings"
2. Scroll to "Your apps" section
3. Find your web app (should show `</>` icon)
4. Copy the entire configuration object

### Step 4: Enable Required Google Cloud APIs
1. Go to https://console.cloud.google.com/
2. Select project `kiro-hackathon23`
3. Go to "APIs & Services" → "Library"
4. Search and enable these APIs:
   - **Identity Toolkit API** (most important)
   - **Firebase Authentication API**
   - **Cloud Resource Manager API**

### Step 5: Configure API Key Restrictions
1. In Google Cloud Console, go to "APIs & Services" → "Credentials"
2. Find API key `AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU`
3. Click on it to edit
4. Under "Application restrictions":
   - For development: Select "None"
   - For production: Add your domains
5. Under "API restrictions":
   - Select "Restrict key"
   - Enable these APIs:
     - Identity Toolkit API
     - Firebase Authentication API
     - Cloud Firestore API
6. Click "Save"

### Step 6: Update Your Configuration
If you got a new API key from Step 3, update `frontend/.env`:
```env
VITE_FIREBASE_API_KEY=<new_api_key_from_console>
VITE_FIREBASE_AUTH_DOMAIN=kiro-hackathon23.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=kiro-hackathon23
VITE_FIREBASE_STORAGE_BUCKET=kiro-hackathon23.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=1020803101475
VITE_FIREBASE_APP_ID=<new_app_id_from_console>
VITE_FIREBASE_MEASUREMENT_ID=G-VPZDRW0NGN
```

### Step 7: Test Firebase Configuration
1. Set `VITE_FIREBASE_DEMO_MODE=false` in `.env`
2. Restart your development server
3. Try to sign up/login
4. Check browser console for errors

### Step 8: If Still Not Working
Run this test in browser console:
```javascript
fetch('https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ returnSecureToken: true })
}).then(r => r.json()).then(console.log)
```

Expected results:
- ✅ Should return user data or validation error
- ❌ If returns `API_KEY_INVALID` → API key is wrong
- ❌ If returns `CONFIGURATION_NOT_FOUND` → Project/Auth not set up

## Common Issues & Solutions

### "No Web API Key for this project"
- This is normal - the key exists but might need configuration
- Follow Step 5 to configure API restrictions

### "Identity Toolkit API has not been used"
- Go to Google Cloud Console → APIs & Services → Library
- Search "Identity Toolkit API" and enable it
- Wait 5-10 minutes for propagation

### "API key not valid"
- Key might be restricted to specific domains
- Set restrictions to "None" for development
- Or add `localhost:*` to allowed domains

### "Project suspended"
- Check Firebase Console for billing issues
- Verify project is in good standing
- Contact Firebase support if needed

## Testing Your Fix

### Test 1: Environment Variables
Check browser console for:
```
Firebase Config: {
  apiKey: "AIzaSyABU8...",
  authDomain: "kiro-hackathon23.firebaseapp.com",
  projectId: "kiro-hackathon23"
}
```

### Test 2: Firebase Initialization
Should see:
```
✅ Firebase initialized successfully
```

### Test 3: Authentication
Try signing up with:
- Email: test@example.com
- Password: test123

Should work without errors.

## Rollback to Demo Mode
If Firebase still doesn't work:
1. Set `VITE_FIREBASE_DEMO_MODE=true`
2. Continue development with mock authentication
3. Fix Firebase configuration later

## Current Demo Mode Features
✅ Email/password login/signup
✅ User sessions
✅ Profile management
✅ All UI components work
❌ No real Firebase services (Firestore, Storage)
❌ No Google OAuth
❌ No password reset emails

The app is fully functional in demo mode for development and testing!