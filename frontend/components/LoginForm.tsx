'use client';

import React, { useState } from 'react';
import { useAuth } from './AuthProvider';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, onSwitchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form">
      <div className="auth-header">
        <div className="logo">🗣️</div>
        <h1>Welcome Back</h1>
        <p className="subtitle">Sign in to your Debabelizer account</p>
      </div>

      {error && (
        <div className="message error">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="email">Email Address</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>

        <button type="submit" className="btn-primary" disabled={isLoading}>
          {isLoading ? 'Signing In...' : 'Sign In'}
        </button>
      </form>

      {onSwitchToRegister && (
        <div className="auth-links">
          <button type="button" onClick={onSwitchToRegister} className="link-button">
            Don't have an account? Sign up
          </button>
        </div>
      )}

      <style jsx>{`
        .auth-form {
          background: white;
          border-radius: 16px;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
          padding: 40px;
          width: 100%;
          max-width: 400px;
          text-align: center;
        }

        .auth-header {
          margin-bottom: 30px;
        }

        .logo {
          font-size: 2.5em;
          margin-bottom: 10px;
        }

        h1 {
          color: #333;
          margin-bottom: 8px;
          font-size: 24px;
          font-weight: 600;
        }

        .subtitle {
          color: #666;
          font-size: 14px;
        }

        .form-group {
          margin-bottom: 20px;
          text-align: left;
        }

        label {
          display: block;
          margin-bottom: 5px;
          color: #333;
          font-weight: 500;
          font-size: 14px;
        }

        input[type="email"], input[type="password"] {
          width: 100%;
          padding: 12px 16px;
          border: 2px solid #e1e5e9;
          border-radius: 8px;
          font-size: 16px;
          transition: border-color 0.3s;
          font-family: inherit;
        }

        input[type="email"]:focus, input[type="password"]:focus {
          outline: none;
          border-color: #667eea;
        }

        input:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-primary {
          width: 100%;
          padding: 12px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
          margin-bottom: 20px;
          font-family: inherit;
        }

        .btn-primary:hover:not(:disabled) {
          transform: translateY(-2px);
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .auth-links {
          text-align: center;
          margin-top: 20px;
        }

        .link-button {
          background: none;
          border: none;
          color: #667eea;
          text-decoration: none;
          font-size: 14px;
          cursor: pointer;
          font-family: inherit;
        }

        .link-button:hover {
          text-decoration: underline;
        }

        .message {
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          font-size: 14px;
        }

        .message.error {
          background-color: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }
      `}</style>
    </div>
  );
};