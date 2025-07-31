'use client';

import React, { useState } from 'react';
import { LoginForm } from '../../components/LoginForm';
import { RegisterForm } from '../../components/RegisterForm';
import { useRouter } from 'next/navigation';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const router = useRouter();

  const handleAuthSuccess = () => {
    // Redirect to main app after successful authentication
    router.push('/');
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        {isLogin ? (
          <LoginForm
            onSuccess={handleAuthSuccess}
            onSwitchToRegister={() => setIsLogin(false)}
          />
        ) : (
          <RegisterForm
            onSuccess={() => {
              // After registration, show success message but don't auto-login
              // User needs to confirm email first
            }}
            onSwitchToLogin={() => setIsLogin(true)}
          />
        )}
      </div>

      <style jsx>{`
        .auth-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .auth-container {
          width: 100%;
          max-width: 400px;
        }
      `}</style>
    </div>
  );
}