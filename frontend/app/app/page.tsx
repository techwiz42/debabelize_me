'use client'

import ChatInterface from '@/components/ChatInterface'
import { useAuth } from '@/components/AuthProvider'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function AppPage() {
  const { isAuthenticated, isLoading, user, logout } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/')
    }
  }, [isAuthenticated, isLoading, router])

  const handleLogout = async () => {
    try {
      await logout()
      router.push('/')
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
    return null // Will redirect to landing page
  }

  return (
    <main className="app-container">
      <div className="app-header">
        <div className="app-title">
          <span>🗣️ Debabelize Me</span>
        </div>
        <div className="app-controls">
          <span className="user-info">Welcome, {user?.email}</span>
          <button onClick={() => router.push('/')} className="home-button">
            Home
          </button>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </div>
      <ChatInterface />
      <style jsx>{`
        .app-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px 20px;
          background: rgba(255, 255, 255, 0.95);
          border-bottom: 1px solid #eee;
          backdrop-filter: blur(10px);
        }

        .app-title {
          font-size: 18px;
          font-weight: 600;
          color: #333;
        }

        .app-controls {
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .user-info {
          font-size: 14px;
          color: #666;
        }

        .home-button, .logout-button {
          background: none;
          border: 1px solid #667eea;
          color: #667eea;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .home-button:hover {
          background: #667eea;
          color: white;
        }

        .logout-button {
          border-color: #dc3545;
          color: #dc3545;
        }

        .logout-button:hover {
          background: #dc3545;
          color: white;
        }

        @media (max-width: 768px) {
          .app-header {
            flex-direction: column;
            gap: 10px;
            padding: 15px;
          }

          .app-controls {
            flex-wrap: wrap;
            justify-content: center;
          }

          .user-info {
            width: 100%;
            text-align: center;
            margin-bottom: 5px;
          }
        }
      `}</style>
    </main>
  )
}