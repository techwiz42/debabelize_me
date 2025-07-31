import './globals.css'
import { AuthProvider } from '../components/AuthProvider'

export const metadata = {
  title: 'Debabelizer - Universal Voice Processing',
  description: 'Breaking down language barriers with advanced speech-to-text and text-to-speech technology',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}