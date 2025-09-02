# Enable Firebase Authentication - Step by Step

## Current Status
✅ Firebase project exists: `kiro-hackathon23`
✅ Web API key exists: `AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU`
✅ Service account configured in backend
❌ Firebase Authentication likely not enabled
🔧 Demo mode disabled - testing real Firebase

## Step 1: Enable Firebase Authentication

### 1.1 Go to Firebase Console
1. Open https://console.firebase.google.com/project/kiro-hackathon23
2. Click on "Authentication" in the left sidebar
3. If you see "Get started", click it
4. This will enable Firebase Authentication for your project

### 1.2 Enable Email/Password Sign-in
1. Go to the "Sign-in method" tab
2. Click on "Email/Password"
3. Toggle "Enable" to ON
4. Click "Save"

## Step 2: Enable Required Google Cloud APIs

### 2.1 Go to Google Cloud Console
1. Open https://console.cloud.google.com/
2. Select project "kiro-hackathon23"
3. Go to "APIs & Services" → "Library"

### 2.2 Enable These APIs
Search for and enable each of these:
- **Identity Toolkit API** (most important for auth)
- **Firebase Authentication API**
- **Cloud Resource Manager API**

## Step 3: Configure API Key (if needed)

### 3.1 Check API Key Restrictions
1. In Google Cloud Console, go to "APIs & Services" → "Credentials"
2. Find your API key: `AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU`
3. Click on it to edit

### 3.2 Set Application Restrictions
- For development: Select "None"
- For production: Add your domains (localhost:*, 127.0.0.1:*)

### 3.3 Set API Restrictions
- Select "Restrict key"
- Enable these APIs:
  - Identity Toolkit API
  - Firebase Authentication API
  - Cloud Firestore API (if using database)
- Click "Save"

## Step 4: Test the Configuration

### 4.1 Use the Test File
1. Open `test-firebase-auth.html` in your browser
2. Click "Test API Key" to check if the key works
3. Try "Test Sign Up" with a test email

### 4.2 Expected Results
✅ **If working**: "API Key is valid and working!"
❌ **If not enabled**: "Firebase Authentication is not enabled for this project"
❌ **If key invalid**: "API Key is invalid or expired"

## Step 5: Test in Your App

### 5.1 Restart Development Server
```bash
# In frontend directory
npm run dev
```

### 5.2 Try Authentication
1. Go to your app's login page
2. Try to sign up with a test email
3. Check browser console for any errors

## Step 6: If Still Not Working

### 6.1 Wait for Propagation
- API changes can take 5-10 minutes to propagate
- Clear browser cache and try again

### 6.2 Check Project Status
1. Verify project is not suspended
2. Check billing status (if using paid features)
3. Ensure you have owner/editor permissions

### 6.3 Regenerate API Key (last resort)
1. In Firebase Console → Project Settings
2. Scroll to "Your apps" section
3. Click on your web app
4. Copy the new configuration
5. Update your `.env` file

## Common Error Messages

### "CONFIGURATION_NOT_FOUND"
- **Cause**: Firebase Authentication not enabled
- **Fix**: Follow Step 1 above

### "API_KEY_INVALID"
- **Cause**: API key is wrong or restricted
- **Fix**: Follow Step 3 above

### "Identity Toolkit API has not been used"
- **Cause**: Required API not enabled
- **Fix**: Follow Step 2 above

## Quick Test Commands

### Test API Key in Browser Console:
```javascript
fetch('https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ returnSecureToken: true })
}).then(r => r.json()).then(console.log)
```

### Expected Response:
- ✅ Success: Returns user data or validation error
- ❌ Error: Returns specific error message

## Rollback to Demo Mode
If Firebase still doesn't work, you can always go back to demo mode:
```env
VITE_FIREBASE_DEMO_MODE=true
```

Your app will work perfectly with mock authentication while you fix Firebase.

## Next Steps After Enabling
1. Test sign up/login in your app
2. Verify user sessions persist
3. Test password reset functionality
4. Enable additional sign-in methods (Google, etc.)

The most likely issue is that Firebase Authentication simply isn't enabled yet. Follow Step 1 first!