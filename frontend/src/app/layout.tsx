import React from 'react'
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Travel Agent Pro',
  description: '🏃🏻 AI-Powered Weekend Trip Planner (Beijing ver.)',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" style={{ backgroundColor: 'oklch(0.17 0.02 240)', colorScheme: 'dark' }}>
      <head>
        {/* 阻止白色闪烁的立即执行脚本 */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  // 立即设置暗色背景，在任何渲染之前
                  document.documentElement.style.backgroundColor = 'oklch(0.17 0.02 240)';
                  document.documentElement.style.colorScheme = 'dark';
                  if (document.body) {
                    document.body.style.backgroundColor = 'oklch(0.17 0.02 240)';
                    document.body.style.color = 'oklch(0.95 0.01 240)';
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link 
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" 
          rel="stylesheet" 
        />
        {/* 预加载主题CSS */}
        <link rel="preload" href="/theme_travelpro_dark_1.css" as="style" />
        <link rel="stylesheet" href="/theme_travelpro_dark_1.css" />
      </head>
      <body className="antialiased" style={{ backgroundColor: 'oklch(0.17 0.02 240)', color: 'oklch(0.95 0.01 240)' }}>
        {children}
      </body>
    </html>
  )
} 