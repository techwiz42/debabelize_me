'use client'

import ChatInterface from '@/components/ChatInterface'
import { useAuth } from '@/components/AuthProvider'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function Home() {
  const { isAuthenticated, isLoading, user, logout } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth')
    }
  }, [isAuthenticated, isLoading, router])

  const handleLogout = async () => {
    try {
      await logout()
      router.push('/auth')
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  if (isLoading) {
    return (
      <main className="app-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
        <style jsx>{`
          .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            gap: 20px;
          }
          
          .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
          }
          
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </main>
    )
  }

  if (!isAuthenticated) {
    return (
      <main className="landing-page">
        <div className="landing-container">
          <div className="landing-header">
            <div className="logo">🗣️</div>
            <h1>Debabelizer</h1>
            <p className="tagline">Universal Voice Processing Platform</p>
            <p className="subtitle">Breaking down language barriers with advanced speech-to-text and text-to-speech technology</p>
          </div>
          
          <div className="landing-actions">
            <button onClick={() => router.push('/auth')} className="cta-button">
              Get Started
            </button>
            <p className="auth-hint">
              Create an account or sign in to start using Debabelizer
            </p>
          </div>
          
          <div className="landing-footer">
            <a href="/terms" className="terms-link">Terms of Service</a>
            <span className="separator">•</span>
            <span className="entertainment-notice">For Entertainment Purposes Only</span>
          </div>
        </div>
        
        <style jsx>{`
          .landing-page {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          }
          
          .landing-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 60px 40px;
            text-align: center;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
          }
          
          .landing-header {
            margin-bottom: 40px;
          }
          
          .logo {
            font-size: 4em;
            margin-bottom: 20px;
          }
          
          h1 {
            font-size: 36px;
            font-weight: 700;
            color: #333;
            margin-bottom: 10px;
          }
          
          .tagline {
            font-size: 18px;
            color: #667eea;
            font-weight: 600;
            margin-bottom: 15px;
          }
          
          .subtitle {
            font-size: 16px;
            color: #666;
            line-height: 1.5;
          }
          
          .landing-actions {
            margin-bottom: 40px;
          }
          
          .cta-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 16px 32px;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            margin-bottom: 15px;
          }
          
          .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
          }
          
          .auth-hint {
            color: #666;
            font-size: 14px;
            margin: 0;
          }
          
          .landing-footer {
            border-top: 1px solid #eee;
            padding-top: 20px;
            font-size: 12px;
            color: #888;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
          }
          
          .terms-link {
            color: #667eea;
            text-decoration: none;
          }
          
          .terms-link:hover {
            text-decoration: underline;
          }
          
          .separator {
            color: #ccc;
          }
          
          .entertainment-notice {
            color: #d63384;
            font-weight: 500;
          }
          
          @media (max-width: 768px) {
            .landing-container {
              padding: 40px 30px;
            }
            
            h1 {
              font-size: 28px;
            }
            
            .tagline {
              font-size: 16px;
            }
            
            .subtitle {
              font-size: 14px;
            }
            
            .landing-footer {
              flex-direction: column;
              gap: 5px;
            }
            
            .separator {
              display: none;
            }
          }
        `}</style>
      </main>
    )
  }

  return (
    <main className="app-container">
      <ChatInterface />
    </main>
  )
}