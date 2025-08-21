# 🚨 EMERGENCY: API Key Revocation Required

## ⚠️ COMPROMISED API KEY DETECTED
GitHub has detected the following API key in your repository history:
**`AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU`**

## 🔥 IMMEDIATE ACTIONS REQUIRED (Do this NOW!)

### 1. Revoke the Firebase API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Find the API key: `AIzaSyABU80Orp7q6rALHdorrWmXjZrFdRO7XKU`
4. Click on it and select **DELETE** or **DISABLE**
5. Confirm the deletion

### 2. Create a New API Key
1. In the same **Credentials** page, click **+ CREATE CREDENTIALS**
2. Select **API Key**
3. Copy the new API key immediately
4. Click **RESTRICT KEY** and configure:
   - **Application restrictions**: HTTP referrers (web sites)
   - **API restrictions**: Select only the APIs you need:
     - Firebase Authentication API
     - Cloud Firestore API
     - Firebase Storage API
     - Any other APIs your app uses

### 3. Update Your Local Configuration
```bash
# Update your local frontend/.env file with the NEW key
VITE_FIREBASE_API_KEY=your_new_api_key_here
```

### 4. Check for Unauthorized Usage
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Quotas**
3. Check for any unusual API usage patterns
4. Review **IAM & Admin** → **Audit Logs** for suspicious activity

### 5. Secure Your Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `kiro-hackathon23`
3. Go to **Project Settings** → **General**
4. Under **Your apps**, regenerate any app-specific configs
5. Update **Authentication** → **Sign-in method** restrictions if needed

## 🔍 Security Audit Checklist

- [ ] Old API key revoked/deleted
- [ ] New API key created with proper restrictions
- [ ] Local environment updated with new key
- [ ] No unusual API usage detected
- [ ] Firebase project security reviewed
- [ ] All team members notified of key change
- [ ] Documentation updated with new setup process

## 🛡️ Prevention for Future

### Git History Cleanup (Advanced)
If you want to completely remove the key from Git history:
```bash
# WARNING: This rewrites Git history - coordinate with team first
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch frontend/.env' \
  --prune-empty --tag-name-filter cat -- --all

# Force push to update remote history
git push origin --force --all
```

### Better Security Practices
1. **Never commit .env files** - Always use .env.example templates
2. **Use environment variables** in production
3. **Implement API key rotation** regularly
4. **Monitor API usage** for anomalies
5. **Use least-privilege access** for API keys

## 📞 Emergency Contacts

If you suspect unauthorized access:
1. **Google Cloud Support**: https://cloud.google.com/support
2. **Firebase Support**: https://firebase.google.com/support
3. **GitHub Security**: security@github.com

## ✅ After Remediation

Once you've completed all steps:
1. Close the GitHub security alert as "Revoked"
2. Update your team about the new API key
3. Test your application with the new key
4. Monitor for any issues in the next 24-48 hours

**Time is critical - the longer the key remains active, the higher the risk!**