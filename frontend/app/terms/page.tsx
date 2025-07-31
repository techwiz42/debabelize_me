'use client';

import React from 'react';
import Link from 'next/link';

export default function TermsOfService() {
  return (
    <div className="terms-page">
      <div className="terms-container">
        <div className="terms-header">
          <Link href="/" className="back-link">
            ← Back to Home
          </Link>
          <div className="logo">🗣️</div>
          <h1>Terms of Service</h1>
          <p className="last-updated">Last Updated: January 31, 2025</p>
        </div>

        <div className="terms-content">
          <div className="important-notice">
            <h2>⚠️ IMPORTANT NOTICE</h2>
            <p><strong>Debabelizer is provided for ENTERTAINMENT PURPOSES ONLY. This service comes with NO WARRANTIES of any kind and is NOT intended for any critical, professional, or production use.</strong></p>
          </div>

          <section>
            <h2>1. Acceptance of Terms</h2>
            <p>
              By accessing or using Debabelizer ("the Service"), you agree to be bound by these Terms of Service ("Terms"). 
              If you do not agree to these Terms, you may not use the Service.
            </p>
          </section>

          <section>
            <h2>2. Entertainment Use Only</h2>
            <p>
              <strong>Debabelizer is designed and intended solely for entertainment, experimentation, and educational purposes.</strong> 
              The Service is NOT suitable for:
            </p>
            <ul>
              <li>Medical, legal, or professional advice</li>
              <li>Emergency communications</li>
              <li>Business-critical applications</li>
              <li>Safety-critical systems</li>
              <li>Financial transactions or advice</li>
              <li>Any situation where accuracy is essential</li>
            </ul>
          </section>

          <section>
            <h2>3. No Warranties</h2>
            <p>
              <strong>THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED.</strong> 
              We specifically disclaim all warranties, including but not limited to:
            </p>
            <ul>
              <li><strong>Fitness for a particular purpose</strong></li>
              <li><strong>Merchantability</strong></li>
              <li><strong>Accuracy or reliability</strong></li>
              <li><strong>Continuous availability</strong></li>
              <li><strong>Error-free operation</strong></li>
              <li><strong>Security of data</strong></li>
            </ul>
          </section>

          <section>
            <h2>4. Speech Recognition and Synthesis Limitations</h2>
            <p>
              Our speech-to-text and text-to-speech services may:
            </p>
            <ul>
              <li>Produce inaccurate transcriptions</li>
              <li>Misinterpret spoken content</li>
              <li>Generate inappropriate or unexpected audio</li>
              <li>Fail to work with certain accents or languages</li>
              <li>Experience technical failures or interruptions</li>
            </ul>
            <p>
              <strong>You acknowledge that voice processing technology is inherently imperfect and should not be relied upon for important communications.</strong>
            </p>
          </section>

          <section>
            <h2>5. User Responsibilities</h2>
            <p>You agree to:</p>
            <ul>
              <li>Use the Service only for lawful, entertainment purposes</li>
              <li>Not rely on the Service for any critical applications</li>
              <li>Not use the Service to create, transmit, or store illegal content</li>
              <li>Not attempt to hack, disrupt, or reverse engineer the Service</li>
              <li>Respect the intellectual property rights of others</li>
              <li>Not use the Service for spam or unauthorized commercial purposes</li>
            </ul>
          </section>

          <section>
            <h2>6. Privacy and Data</h2>
            <p>
              By using the Service, you acknowledge that:
            </p>
            <ul>
              <li>Audio data may be processed by third-party services</li>
              <li>Conversations may be temporarily stored for processing</li>
              <li>We make no guarantees about data privacy or security</li>
              <li>You should not share sensitive or personal information</li>
            </ul>
          </section>

          <section>
            <h2>7. Limitation of Liability</h2>
            <p>
              <strong>TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE SHALL NOT BE LIABLE FOR ANY DAMAGES OF ANY KIND</strong> 
              arising from your use of the Service, including but not limited to:
            </p>
            <ul>
              <li>Direct, indirect, incidental, or consequential damages</li>
              <li>Loss of data, profits, or business opportunities</li>
              <li>Costs of substitute services</li>
              <li>Personal injury or property damage</li>
              <li>Emotional distress or mental anguish</li>
            </ul>
            <p>
              This limitation applies even if we have been advised of the possibility of such damages.
            </p>
          </section>

          <section>
            <h2>8. Indemnification</h2>
            <p>
              You agree to indemnify and hold harmless Debabelizer, its operators, and affiliates from any claims, 
              damages, or expenses arising from your use of the Service or violation of these Terms.
            </p>
          </section>

          <section>
            <h2>9. Service Availability</h2>
            <p>
              We make no guarantees about Service availability, uptime, or performance. The Service may be:
            </p>
            <ul>
              <li>Temporarily or permanently unavailable</li>
              <li>Modified or discontinued without notice</li>
              <li>Subject to maintenance downtime</li>
              <li>Limited by third-party service dependencies</li>
            </ul>
          </section>

          <section>
            <h2>10. Age Restrictions</h2>
            <p>
              The Service is intended for users 13 years of age or older. Users under 18 should obtain parental 
              consent before using the Service.
            </p>
          </section>

          <section>
            <h2>11. Termination</h2>
            <p>
              We reserve the right to terminate or suspend your access to the Service at any time, for any reason, 
              without notice. You may discontinue use of the Service at any time.
            </p>
          </section>

          <section>
            <h2>12. Changes to Terms</h2>
            <p>
              We may modify these Terms at any time. Continued use of the Service after changes constitutes 
              acceptance of the modified Terms. We encourage you to review these Terms periodically.
            </p>
          </section>

          <section>
            <h2>13. Governing Law</h2>
            <p>
              These Terms shall be governed by and construed in accordance with the laws of the jurisdiction 
              where the Service is operated, without regard to conflict of law principles.
            </p>
          </section>

          <section>
            <h2>14. Entire Agreement</h2>
            <p>
              These Terms constitute the entire agreement between you and Debabelizer regarding the Service 
              and supersede all prior agreements and understandings.
            </p>
          </section>

          <div className="contact-section">
            <h2>Contact Information</h2>
            <p>
              If you have questions about these Terms of Service, please contact us at: 
              <a href="mailto:support@debabelizer.com">support@debabelizer.com</a>
            </p>
          </div>

          <div className="final-reminder">
            <h2>🎭 Final Reminder</h2>
            <p>
              <strong>Debabelizer is a fun, experimental voice processing tool for entertainment purposes only. 
              Please use it responsibly and don't rely on it for anything important!</strong>
            </p>
          </div>
        </div>
      </div>

      <style jsx>{`
        .terms-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .terms-container {
          max-width: 800px;
          margin: 0 auto;
          background: white;
          border-radius: 16px;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
          overflow: hidden;
        }

        .terms-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 40px;
          text-align: center;
          position: relative;
        }

        .back-link {
          position: absolute;
          top: 20px;
          left: 20px;
          color: white;
          text-decoration: none;
          font-size: 14px;
          opacity: 0.9;
          transition: opacity 0.2s;
        }

        .back-link:hover {
          opacity: 1;
          text-decoration: underline;
        }

        .logo {
          font-size: 3em;
          margin-bottom: 15px;
        }

        .terms-header h1 {
          margin: 0;
          font-size: 32px;
          font-weight: 600;
        }

        .last-updated {
          margin: 10px 0 0 0;
          opacity: 0.9;
          font-size: 14px;
        }

        .terms-content {
          padding: 40px;
          line-height: 1.6;
          color: #333;
        }

        .important-notice {
          background: #fff3cd;
          border: 2px solid #ffc107;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 30px;
        }

        .important-notice h2 {
          color: #856404;
          margin-top: 0;
          font-size: 18px;
        }

        .important-notice p {
          color: #856404;
          margin-bottom: 0;
          font-weight: 500;
        }

        section {
          margin-bottom: 30px;
        }

        h2 {
          color: #333;
          font-size: 20px;
          font-weight: 600;
          margin-bottom: 15px;
          border-bottom: 2px solid #667eea;
          padding-bottom: 5px;
        }

        p {
          margin-bottom: 15px;
          font-size: 15px;
        }

        ul {
          margin-bottom: 15px;
          padding-left: 20px;
        }

        li {
          margin-bottom: 8px;
          font-size: 15px;
        }

        strong {
          color: #d63384;
          font-weight: 600;
        }

        .contact-section {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 30px;
        }

        .contact-section a {
          color: #667eea;
          text-decoration: none;
        }

        .contact-section a:hover {
          text-decoration: underline;
        }

        .final-reminder {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 25px;
          border-radius: 8px;
          text-align: center;
        }

        .final-reminder h2 {
          color: white;
          border-bottom: none;
          margin-bottom: 15px;
        }

        .final-reminder p {
          margin-bottom: 0;
          font-size: 16px;
        }

        .final-reminder strong {
          color: #fff;
        }

        @media (max-width: 768px) {
          .terms-page {
            padding: 10px;
          }

          .terms-header {
            padding: 30px 20px;
          }

          .terms-header h1 {
            font-size: 24px;
          }

          .terms-content {
            padding: 30px 20px;
          }

          .back-link {
            position: static;
            display: block;
            margin-bottom: 20px;
          }
        }
      `}</style>
    </div>
  );
}