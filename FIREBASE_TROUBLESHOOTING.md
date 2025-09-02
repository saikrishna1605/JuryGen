# Firebase API Key Troubleshooting Guide

## Current Issue
The Firebase API key `AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU` is being rejected with error: `auth/api-key-not-valid`

## Possible Causes & Solutions

### 1. API Key Regenerated
**Problem**: The API key might have been regenerated in Firebase Console
**Solution**: 
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project `kiro-hackathon23`
3. Go to Project Settings (gear icon)
4. Scroll down to "Your apps" section
5. Find your web app and copy the new `apiKey` value
6. Update `VITE_FIREBASE_API_KEY` in `frontend/.env`

### 2. API Key Restrictions
**Problem**: The API key might have domain/IP restrictions
**Solution**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project `kiro-hackathon23`
3. Go to "APIs & Services" > "Credentials"
4. Find your API key and click on it
5. Check "Application restrictions":
   - Should be "None" for development
   - Or add `localhost:*` and `127.0.0.1:*` to allowed domains
6. Check "API restrictions":
   - Should include "Firebase Authentication API"
   - Should include "Identity Toolkit API"

### 3. Firebase Project Issues
**Problem**: Project might be suspended or have billing issues
**Solution**:
1. Check Firebase Console for any warnings/notifications
2. Verify project is active (not suspended)
3. Check billing status if using paid features

### 4. Authentication Service Not Enabled
**Problem**: Firebase Authentication might not be enabled
**Solution**:
1. Go to Firebase Console > Authentication
2. Click "Get started" if not already enabled
3. Go to "Sign-in method" tab
4. Enable "Email/Password" provider

## Quick Test Steps

### Step 1: Verify Project Access
1. Go to https://console.firebase.google.com/
2. Can you access the `kiro-hackathon23` project?
3. Are there any error messages or warnings?

### Step 2: Get Fresh API Key
1. In Firebase Console > Project Settings
2. Scroll to "Your apps" section
3. Copy the current `apiKey` value
4. Compare with the one in your `.env` file

### Step 3: Test API Key Manually
Open browser console and run:
```javascript
fetch('https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ returnSecureToken: true })
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

If this returns an error about invalid API key, the key is definitely wrong.

## Temporary Workaround
I've enabled demo mode (`VITE_FIREBASE_DEMO_MODE=true`) so the app will work without Firebase while you fix the API key.

## Next Steps
1. Follow the troubleshooting steps above
2. Get the correct API key from Firebase Console
3. Update the `.env` file with the correct key
4. Set `VITE_FIREBASE_DEMO_MODE=false`
5. Restart the development server

## Common API Key Formats
- Valid: `AIzaSy...` (39 characters)
- Your current: `AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU` (39 characters) ✓

The format looks correct, so the issue is likely with restrictions or the key being regenerated.