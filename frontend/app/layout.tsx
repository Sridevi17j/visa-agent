import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Veazy - AI Visa Assistant',
  description: 'Get help with your visa application from our AI assistant',
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}