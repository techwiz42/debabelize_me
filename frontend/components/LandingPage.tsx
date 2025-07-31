'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/AuthProvider'

export default function LandingPage() {
  const router = useRouter()
  const { isAuthenticated, user, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  return (
    <div className="landing-page">
      <div className="landing-container">
        <header className="landing-header">
          <div className="nav-section">
            {isAuthenticated ? (
              <div className="auth-links authenticated">
                <span className="welcome-text">Welcome, {user?.email}</span>
                <button onClick={handleLogout} className="auth-link logout">
                  Logout
                </button>
                <button 
                  onClick={() => router.push('/app')} 
                  className="app-link"
                >
                  Open App
                </button>
              </div>
            ) : (
              <div className="auth-links">
                <button 
                  onClick={() => router.push('/auth')} 
                  className="auth-link login"
                >
                  Login
                </button>
                <button 
                  onClick={() => router.push('/auth')} 
                  className="auth-link register"
                >
                  Register
                </button>
              </div>
            )}
          </div>
          
          <div className="logo-section">
            <div className="logo">🗣️</div>
            <h1>Debabelize Me</h1>
            <p className="tagline">Test platform for voice processing experiments</p>
          </div>
        </header>

        <main className="landing-main">
          <section className="description-section">
            <p className="description">
              This is a test environment for exploring the functionality of the debabelizer module. 
              The platform provides speech-to-text and text-to-speech capabilities through various providers.
            </p>
          </section>

          <section className="links-section">
            <div className="external-links">
              <a 
                href="https://github.com/techwiz42/debabelizer" 
                target="_blank" 
                rel="noopener noreferrer"
                className="external-link github"
              >
                <span className="link-icon">📦</span>
                Debabelizer on GitHub
              </a>
              <a 
                href="https://www.linkedin.com/in/psisk/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="external-link linkedin"
              >
                <span className="link-icon">💼</span>
                LinkedIn Profile
              </a>
            </div>
          </section>
        </main>

        <footer className="landing-footer">
          <button 
            onClick={() => router.push('/terms')} 
            className="footer-link"
          >
            Terms of Service
          </button>
          <span className="separator">•</span>
          <span className="notice">For testing purposes only</span>
        </footer>
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
          padding: 40px;
          max-width: 600px;
          width: 100%;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .landing-header {
          text-align: center;
          margin-bottom: 40px;
        }

        .nav-section {
          margin-bottom: 30px;
          display: flex;
          justify-content: center;
        }

        .auth-links {
          display: flex;
          gap: 15px;
          align-items: center;
        }

        .auth-links.authenticated {
          flex-direction: column;
          gap: 10px;
        }

        .welcome-text {
          font-size: 14px;
          color: #666;
          margin-bottom: 5px;
        }

        .auth-link {
          background: none;
          border: 2px solid #667eea;
          color: #667eea;
          padding: 8px 16px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          text-decoration: none;
          display: inline-block;
        }

        .auth-link:hover {
          background: #667eea;
          color: white;
        }

        .auth-link.register {
          background: #667eea;
          color: white;
        }

        .auth-link.register:hover {
          background: #5a6fd8;
        }

        .auth-link.logout {
          border-color: #dc3545;
          color: #dc3545;
        }

        .auth-link.logout:hover {
          background: #dc3545;
          color: white;
        }

        .app-link {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }

        .app-link:hover {
          transform: translateY(-1px);
        }

        .logo-section {
          border-bottom: 1px solid #eee;
          padding-bottom: 30px;
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
          font-size: 16px;
          color: #666;
          margin: 0;
        }

        .landing-main {
          margin-bottom: 40px;
        }

        .description-section {
          margin-bottom: 30px;
        }

        .description {
          font-size: 16px;
          color: #555;
          line-height: 1.6;
          text-align: center;
          margin: 0;
        }

        .links-section {
          text-align: center;
        }

        .external-links {
          display: flex;
          gap: 20px;
          justify-content: center;
          flex-wrap: wrap;
        }

        .external-link {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
          background: #f8f9fa;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          text-decoration: none;
          color: #495057;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.2s;
        }

        .external-link:hover {
          background: #e9ecef;
          transform: translateY(-1px);
        }

        .external-link.github:hover {
          border-color: #24292e;
          background: #24292e;
          color: white;
        }

        .external-link.linkedin:hover {
          border-color: #0077b5;
          background: #0077b5;
          color: white;
        }

        .link-icon {
          font-size: 16px;
        }

        .landing-footer {
          border-top: 1px solid #eee;
          padding-top: 20px;
          text-align: center;
          font-size: 14px;
          color: #666;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
        }

        .footer-link {
          background: none;
          border: none;
          color: #667eea;
          cursor: pointer;
          text-decoration: underline;
          font-size: 14px;
        }

        .footer-link:hover {
          color: #5a6fd8;
        }

        .separator {
          color: #ccc;
        }

        .notice {
          color: #888;
          font-style: italic;
        }

        @media (max-width: 768px) {
          .landing-container {
            padding: 30px 20px;
          }

          h1 {
            font-size: 28px;
          }

          .external-links {
            flex-direction: column;
            align-items: center;
          }

          .external-link {
            width: 200px;
            justify-content: center;
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
    </div>
  )
}