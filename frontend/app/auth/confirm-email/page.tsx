'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { confirmEmail } from '@/services/auth';

export default function ConfirmEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setMessage('Invalid confirmation link. No token provided.');
      return;
    }

    const handleConfirmation = async () => {
      try {
        const result = await confirmEmail(token);
        
        if (result.success) {
          setStatus('success');
          setMessage(result.message || 'Email confirmed successfully!');
          
          // Redirect to login after 3 seconds
          setTimeout(() => {
            router.push('/auth?confirmed=true');
          }, 3000);
        } else {
          setStatus('error');
          setMessage(result.message || 'Failed to confirm email.');
        }
      } catch (error) {
        setStatus('error');
        setMessage('An error occurred while confirming your email. Please try again.');
      }
    };

    handleConfirmation();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
        <div className="text-center">
          {status === 'loading' && (
            <>
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Confirming your email...</h2>
              <p className="text-gray-600">Please wait while we verify your email address.</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="text-6xl mb-4">✅</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Email Confirmed!</h2>
              <p className="text-gray-600 mb-4">{message}</p>
              <p className="text-sm text-gray-500">Redirecting to login...</p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="text-6xl mb-4">❌</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Confirmation Failed</h2>
              <p className="text-gray-600 mb-6">{message}</p>
              <button
                onClick={() => router.push('/auth')}
                className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors"
              >
                Go to Login
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}