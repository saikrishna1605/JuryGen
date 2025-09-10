import React, { useEffect, useState } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

interface FirebaseTestResult {
  step: string;
  status: 'success' | 'error' | 'pending';
  message: string;
  details?: any;
}

const FirebaseTest: React.FC = () => {
  const [results, setResults] = useState<FirebaseTestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const addResult = (result: FirebaseTestResult) => {
    setResults(prev => [...prev, result]);
  };

  const testFirebaseConfig = async () => {
    setIsRunning(true);
    setResults([]);

    // Step 1: Check environment variables
    addResult({
      step: 'Environment Variables',
      status: 'pending',
      message: 'Checking environment variables...'
    });

    const envVars = {
      apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
      authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
      projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
      storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
      messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
      appId: import.meta.env.VITE_FIREBASE_APP_ID,
    };

    const missingVars = Object.entries(envVars).filter(([, value]) => !value);
    
    if (missingVars.length > 0) {
      addResult({
        step: 'Environment Variables',
        status: 'error',
        message: `Missing environment variables: ${missingVars.map(([key]) => key).join(', ')}`,
        details: envVars
      });
      setIsRunning(false);
      return;
    }

    addResult({
      step: 'Environment Variables',
      status: 'success',
      message: 'All environment variables are present',
      details: {
        apiKey: envVars.apiKey ? `${envVars.apiKey.substring(0, 10)}...` : 'missing',
        authDomain: envVars.authDomain,
        projectId: envVars.projectId,
        storageBucket: envVars.storageBucket,
        messagingSenderId: envVars.messagingSenderId,
        appId: envVars.appId ? `${envVars.appId.substring(0, 20)}...` : 'missing',
      }
    });

    // Step 2: Initialize Firebase App
    addResult({
      step: 'Firebase App',
      status: 'pending',
      message: 'Initializing Firebase app...'
    });

    try {
      const firebaseConfig = {
        apiKey: envVars.apiKey,
        authDomain: envVars.authDomain,
        projectId: envVars.projectId,
        storageBucket: envVars.storageBucket,
        messagingSenderId: envVars.messagingSenderId,
        appId: envVars.appId,
        measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
      };

      const app = initializeApp(firebaseConfig);
      
      addResult({
        step: 'Firebase App',
        status: 'success',
        message: 'Firebase app initialized successfully',
        details: { appName: app.name, options: app.options }
      });

      // Step 3: Initialize Auth
      addResult({
        step: 'Firebase Auth',
        status: 'pending',
        message: 'Initializing Firebase Auth...'
      });

      const auth = getAuth(app);
      
      addResult({
        step: 'Firebase Auth',
        status: 'success',
        message: 'Firebase Auth initialized successfully',
        details: { 
          currentUser: auth.currentUser,
          config: auth.config
        }
      });

      // Step 4: Test API Key validity by making a simple request
      addResult({
        step: 'API Key Validation',
        status: 'pending',
        message: 'Testing API key validity...'
      });

      // This will trigger an API call to Firebase and reveal if the key is valid
      try {
        await new Promise((resolve, reject) => {
          const unsubscribe = auth.onAuthStateChanged(
            (user) => {
              unsubscribe();
              resolve(user);
            },
            (error) => {
              unsubscribe();
              reject(error);
            }
          );
        });

        addResult({
          step: 'API Key Validation',
          status: 'success',
          message: 'API key is valid and working',
        });

      } catch (authError: any) {
        addResult({
          step: 'API Key Validation',
          status: 'error',
          message: `API key validation failed: ${authError.message}`,
          details: authError
        });
      }

    } catch (error: any) {
      addResult({
        step: 'Firebase App',
        status: 'error',
        message: `Firebase initialization failed: ${error.message}`,
        details: error
      });
    }

    setIsRunning(false);
  };

  useEffect(() => {
    testFirebaseConfig();
  }, []);

  const getStatusIcon = (status: FirebaseTestResult['status']) => {
    switch (status) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'pending': return '⏳';
      default: return '❓';
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Firebase Configuration Test</h2>
      
      <button
        onClick={testFirebaseConfig}
        disabled={isRunning}
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {isRunning ? 'Testing...' : 'Run Test Again'}
      </button>

      <div className="space-y-4">
        {results.map((result, index) => (
          <div key={index} className="border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{getStatusIcon(result.status)}</span>
              <h3 className="font-semibold">{result.step}</h3>
            </div>
            
            <p className={`mb-2 ${
              result.status === 'error' ? 'text-red-600' : 
              result.status === 'success' ? 'text-green-600' : 
              'text-yellow-600'
            }`}>
              {result.message}
            </p>
            
            {result.details && (
              <details className="mt-2">
                <summary className="cursor-pointer text-sm text-gray-600">
                  Show Details
                </summary>
                <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
                  {JSON.stringify(result.details, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
      </div>

      {results.length === 0 && !isRunning && (
        <p className="text-gray-500">Click "Run Test Again" to start testing Firebase configuration.</p>
      )}
    </div>
  );
};

export default FirebaseTest;