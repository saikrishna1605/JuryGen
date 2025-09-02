# Production Firebase Authentication Setup

## ✅ Current Configuration
- **Project ID**: kiro-hackathon23
- **API Key**: AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU
- **Demo Mode**: ❌ Disabled (Production Ready)
- **Service Account**: ✅ Configured for backend

## 🚨 Critical Steps for Production

### Step 1: Enable Firebase Authentication
**This is the most likely cause of your current issues.**

1. Go to https://console.firebase.google.com/project/kiro-hackathon23
2. Click "Authentication" in the left sidebar
3. If you see "Get started", click it to enable Authentication
4. Go to "Sign-in method" tab
5. Enable "Email/Password" provider:
   - Toggle "Enable" to ON
   - Click "Save"

### Step 2: Enable Required Google Cloud APIs
1. Go to https://console.cloud.google.com/
2. Select project "kiro-hackathon23"
3. Go to "APIs & Services" → "Library"
4. Search and enable:
   - **Identity Toolkit API** (critical for auth)
   - **Firebase Authentication API**
   - **Cloud Resource Manager API**

### Step 3: Configure API Key for Production
1. In Google Cloud Console → "APIs & Services" → "Credentials"
2. Find your API key: `AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU`
3. Click to edit it
4. **Application restrictions**:
   - For development: "None"
   - For production: Add your domains
5. **API restrictions**:
   - Select "Restrict key"
   - Enable required APIs:
     - Identity Toolkit API
     - Firebase Authentication API
     - Cloud Firestore API
6. Click "Save"

## 🧪 Testing Your Setup

### Quick API Test
Run this in your browser console:
```javascript
fetch('https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ returnSecureToken: true })
}).then(r => r.json()).then(console.log)
```

**Expected Results:**
- ✅ **Success**: Returns user data or validation error
- ❌ **"CONFIGURATION_NOT_FOUND"**: Authentication not enabled
- ❌ **"API_KEY_INVALID"**: API key issue

### Test in Your App
1. Restart your development server
2. Go to login page
3. Try signing up with a real email
4. Check browser console for errors

## 🔒 Production Security Checklist

### API Key Security
- [ ] API key restricted to your domains only
- [ ] No API key exposed in client-side code (it's in env vars)
- [ ] API key has minimal required permissions

### Authentication Rules
- [ ] Email/Password authentication enabled
- [ ] Strong password requirements (6+ characters minimum)
- [ ] Email verification enabled (optional but recommended)

### Firestore Security (if using database)
- [ ] Security rules configured
- [ ] User data access restricted to authenticated users
- [ ] No public read/write access

## 🚀 Production Deployment Checklist

### Environment Variables
- [ ] `VITE_FIREBASE_DEMO_MODE=false` in production
- [ ] All Firebase config variables set correctly
- [ ] API keys secured and not exposed

### Domain Configuration
- [ ] Production domains added to Firebase Auth
- [ ] API key restrictions updated for production domains
- [ ] CORS configured correctly

### Monitoring
- [ ] Firebase Analytics enabled (optional)
- [ ] Error reporting configured
- [ ] Authentication metrics monitored

## 🔧 Common Production Issues

### "Firebase: Error (auth/api-key-not-valid)"
**Cause**: API key is invalid or restricted
**Fix**: 
1. Verify API key in Firebase Console
2. Check API restrictions in Google Cloud Console
3. Ensure Identity Toolkit API is enabled

### "Firebase: Error (auth/configuration-not-found)"
**Cause**: Firebase Authentication not enabled
**Fix**: Enable Authentication in Firebase Console

### "Firebase: Error (auth/network-request-failed)"
**Cause**: Network/CORS issues
**Fix**: 
1. Check domain restrictions
2. Verify CORS configuration
3. Check firewall/proxy settings

## 📊 User Management Features

### Basic Authentication
- ✅ Email/Password sign up
- ✅ Email/Password sign in
- ✅ Password reset
- ✅ User profile updates

### Advanced Features (Optional)
- [ ] Google OAuth sign-in
- [ ] Email verification
- [ ] Multi-factor authentication
- [ ] Custom claims/roles

## 🎯 Next Steps After Setup

1. **Test authentication thoroughly**
2. **Set up user profiles in Firestore**
3. **Configure security rules**
4. **Add email verification**
5. **Set up monitoring and analytics**

## 🆘 If You Still Have Issues

1. **Check Firebase Console** for any warnings or errors
2. **Verify project billing** (some features require paid plan)
3. **Wait 5-10 minutes** for API changes to propagate
4. **Clear browser cache** and try again
5. **Check browser console** for detailed error messages

The most common issue is simply that Firebase Authentication hasn't been enabled yet. Start with Step 1!