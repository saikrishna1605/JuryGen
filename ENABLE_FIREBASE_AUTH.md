# Enable Firebase Authentication - Step by Step

## Current Status
✅ Firebase project exists: `kiro-hackathon23`
✅ API key exists: `AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU`
❌ Getting `CONFIGURATION_NOT_FOUND` error
⚠️  "No Web API Key for this project" message in console

## Step 1: Enable Firebase Authentication
1. Go to https://console.firebase.google.com/project/kiro-hackathon23
2. Click "Authentication" in the left sidebar
3. If you see "Get started", click it
4. Go to the "Sign-in method" tab
5. Click on "Email/Password"
6. Toggle "Enable" to ON
7. Click "Save"

## Step 2: Check Google Cloud Console API Settings
1. Go to https://console.cloud.google.com/
2. Select project "kiro-hackathon23" (or "Kiro-Hackathon")
3. Go to "APIs & Services" > "Credentials"
4. Look for your API key `AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU`
5. Click on the API key to edit it
6. Under "API restrictions":
   - Select "Restrict key"
   - Enable these APIs:
     - Identity Toolkit API
     - Firebase Authentication API
     - Cloud Firestore API (if using Firestore)
7. Under "Application restrictions":
   - For development: Select "None"
   - For production: Add your domains
8. Click "Save"

## Step 3: Enable Required APIs
1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for and enable these APIs:
   - **Identity Toolkit API** (most important for auth)
   - **Firebase Authentication API**
   - **Cloud Resource Manager API**
3. Click "Enable" for each

## Step 4: Test the Configuration
1. Update your `.env` file to disable demo mode:
   ```
   VITE_FIREBASE_DEMO_MODE=false
   ```
2. Restart your development server
3. Try to access the login page
4. Check browser console for any remaining errors

## Step 5: If Still Not Working
If you still get `CONFIGURATION_NOT_FOUND`:

1. **Wait 5-10 minutes** - API changes can take time to propagate
2. **Clear browser cache** - Old cached responses might interfere
3. **Try incognito/private browsing** - Eliminates cache issues
4. **Check Firebase project status** - Make sure it's not suspended

## Common Issues and Solutions

### "No Web API Key for this project"
- This is normal if you haven't configured API restrictions yet
- Follow Step 2 above to configure the API key properly

### "Identity Toolkit API has not been used"
- Go to Google Cloud Console > APIs & Services > Library
- Search for "Identity Toolkit API"
- Click "Enable"

### "API key not valid"
- The key might be restricted to specific domains
- In Google Cloud Console > Credentials, set restrictions to "None" for development

## Quick Test Command
Run this in your browser console to test the API key:
```javascript
fetch('https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ returnSecureToken: true })
}).then(r => r.json()).then(console.log)
```

Expected result: Should NOT return `CONFIGURATION_NOT_FOUND`