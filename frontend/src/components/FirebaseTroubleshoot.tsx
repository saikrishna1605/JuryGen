import React, { useState } from 'react';
import { auth } from '../config/firebase';
import { signInAnonymously } from 'firebase/auth';

const FirebaseTroubleshoot: React.FC = () => {
  const [status, setStatus] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testFirebaseConnection = async () => {
    setLoading(true);
    setStatus('Testing Firebase connection...');

    try {
      // Test anonymous sign-in to verify Firebase is working
      const userCredential = await signInAnonymously(auth);
      setStatus(`✅ Firebase connection successful! User: ${userCredential.user.uid}`);
    } catch (error: any) {
      setStatus(`❌ Firebase connection failed: ${error.message}`);
      
      // Provide specific troubleshooting advice
      if (error.code === 'auth/configuration-not-found') {
        setStatus(prev => prev + '\n💡 Solution: Enable Firebase Authentication in Firebase Console');
      } else if (error.code === 'auth/api-key-not-valid') {
        setStatus(prev => prev + '\n💡 Solution: Check your API key in Firebase Console');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Firebase Troubleshoot</h2>
      
      <button
        onClick={testFirebaseConnection}
        disabled={loading}
        className="mb-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
      >
        {loading ? 'Testing...' : 'Test Firebase Connection'}
      </button>

      {status && (
        <div className="p-4 bg-gray-100 rounded">
          <pre className="whitespace-pre-wrap text-sm">{status}</pre>
        </div>
      )}
    </div>
  );
};

export default FirebaseTroubleshoot;