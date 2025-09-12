// Environment variable checker
export const checkEnvironmentVariables = () => {
  const requiredVars = [
    'VITE_FIREBASE_API_KEY',
    'VITE_FIREBASE_AUTH_DOMAIN', 
    'VITE_FIREBASE_PROJECT_ID',
    'VITE_FIREBASE_STORAGE_BUCKET',
    'VITE_FIREBASE_MESSAGING_SENDER_ID',
    'VITE_FIREBASE_APP_ID'
  ];

  console.log('🔍 Checking environment variables...');
  console.log('🔍 Available env keys:', Object.keys(import.meta.env));
  
  const envVars: Record<string, string | undefined> = {};
  const missingVars: string[] = [];

  requiredVars.forEach(varName => {
    const value = import.meta.env[varName];
    envVars[varName] = value;
    
    if (!value) {
      missingVars.push(varName);
      console.log(`❌ ${varName}: undefined`);
    } else {
      console.log(`✅ ${varName}: ${value.substring(0, 10)}...`);
    }
  });

  if (missingVars.length > 0) {
    console.error('❌ Missing environment variables:', missingVars);
    console.error('💡 This usually means the development server needs to be restarted');
    console.error('💡 Try: npm run dev (in the frontend directory)');
    return false;
  }

  console.log('✅ All Firebase environment variables are present');
  return true;
};