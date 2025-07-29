import './globals.css'

export const metadata = {
  title: 'Debabelize',
  description: 'Provider-agnostic STT/TTS wrapper',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}