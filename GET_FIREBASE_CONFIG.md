# How to Get Fresh Firebase Configuration

## Step 1: Access Firebase Console
1. Go to https://console.firebase.google.com/
2. Sign in with your Google account
3. Look for project `kiro-hackathon23`

## Step 2: If Project Exists
1. Click on the project
2. Click the gear icon (⚙️) in the left sidebar
3. Select "Project settings"
4. Scroll down to "Your apps" section
5. Look for your web app (should show a `</>` icon)
6. Click on the web app or "Config" if visible

## Step 3: Copy the Configuration
You should see something like this:
```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef",
  measurementId: "G-XXXXXXXXXX"
};
```

## Step 4: Update Your .env File
Replace the values in `frontend/.env`:
```
VITE_FIREBASE_API_KEY=<new_api_key>
VITE_FIREBASE_AUTH_DOMAIN=<new_auth_domain>
VITE_FIREBASE_PROJECT_ID=<new_project_id>
VITE_FIREBASE_STORAGE_BUCKET=<new_storage_bucket>
VITE_FIREBASE_MESSAGING_SENDER_ID=<new_messaging_sender_id>
VITE_FIREBASE_APP_ID=<new_app_id>
VITE_FIREBASE_MEASUREMENT_ID=<new_measurement_id>
```

## Step 5: If Project Doesn't Exist
If you can't find the project `kiro-hackathon23`, you'll need to:

1. **Create a new Firebase project**:
   - Click "Create a project"
   - Name it (can be anything, like "legal-companion")
   - Follow the setup wizard

2. **Add a web app**:
   - In project overview, click the `</>` icon
   - Register your app with a nickname
   - Copy the configuration

3. **Enable Authentication**:
   - Go to "Authentication" in the left sidebar
   - Click "Get started"
   - Go to "Sign-in method" tab
   - Enable "Email/Password"

## Step 6: Test the New Configuration
1. Update your `.env` file with the new values
2. Set `VITE_FIREBASE_DEMO_MODE=false`
3. Restart your development server
4. Test the login functionality

## Alternative: Use Demo Mode
If you want to continue development without Firebase for now:
1. Keep `VITE_FIREBASE_DEMO_MODE=true` in your `.env`
2. The app will work with mock authentication
3. Fix Firebase configuration later