// Firebase status checker utility
export const checkFirebaseStatus = () => {
  console.log('🔍 Firebase Environment Check:');
  console.log('================================');
  
  const envVars = {
    VITE_FIREBASE_API_KEY: import.meta.env.VITE_FIREBASE_API_KEY,
    VITE_FIREBASE_AUTH_DOMAIN: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    VITE_FIREBASE_PROJECT_ID: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    VITE_FIREBASE_STORAGE_BUCKET: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    VITE_FIREBASE_MESSAGING_SENDER_ID: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    VITE_FIREBASE_APP_ID: import.meta.env.VITE_FIREBASE_APP_ID,
    VITE_FIREBASE_MEASUREMENT_ID: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
    VITE_FIREBASE_DEMO_MODE: import.meta.env.VITE_FIREBASE_DEMO_MODE,
  };

  Object.entries(envVars).forEach(([key, value]) => {
    if (key === 'VITE_FIREBASE_API_KEY' && value) {
      console.log(`✅ ${key}: ${value.substring(0, 10)}...`);
    } else if (value) {
      console.log(`✅ ${key}: ${value}`);
    } else {
      console.log(`❌ ${key}: MISSING`);
    }
  });

  console.log('================================');
  
  // Check if all required vars are present
  const requiredVars = [
    'VITE_FIREBASE_API_KEY',
    'VITE_FIREBASE_AUTH_DOMAIN', 
    'VITE_FIREBASE_PROJECT_ID',
    'VITE_FIREBASE_STORAGE_BUCKET',
    'VITE_FIREBASE_MESSAGING_SENDER_ID',
    'VITE_FIREBASE_APP_ID'
  ];
  
  const missingVars = requiredVars.filter(varName => !envVars[varName as keyof typeof envVars]);
  
  if (missingVars.length === 0) {
    console.log('✅ All required Firebase environment variables are present');
  } else {
    console.log('❌ Missing required environment variables:', missingVars);
  }
  
  return {
    allPresent: missingVars.length === 0,
    missingVars,
    envVars
  };
};

// Test Firebase API key validity
export const testFirebaseAPIKey = async (apiKey: string) => {
  try {
    console.log('🧪 Testing Firebase API key...');
    
    const response = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ returnSecureToken: true })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      console.log('✅ API Key is valid and working!');
      return { valid: true, message: 'API key is valid' };
    } else {
      const errorMessage = data.error?.message || 'Unknown error';
      console.log(`❌ API Key test failed: ${errorMessage}`);
      
      if (errorMessage === 'CONFIGURATION_NOT_FOUND') {
        console.log('💡 Solution: Enable Firebase Authentication in Firebase Console');
        return { 
          valid: false, 
          message: 'Firebase Authentication not enabled',
          solution: 'Go to Firebase Console → Authentication → Get started'
        };
      } else if (errorMessage === 'API_KEY_INVALID') {
        console.log('💡 Solution: Check your API key in Firebase Console');
        return { 
          valid: false, 
          message: 'API key is invalid',
          solution: 'Verify API key in Firebase Console → Project Settings'
        };
      }
      
      return { valid: false, message: errorMessage };
    }
  } catch (error) {
    console.log(`❌ Network error testing API key: ${error}`);
    return { valid: false, message: `Network error: ${error}` };
  }
};