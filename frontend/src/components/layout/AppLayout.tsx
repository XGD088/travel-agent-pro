// Travel Agent Pro - App Layout Component
// 应用主布局组件

import React from 'react'

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen">
      {children}
    </div>
  )
}

