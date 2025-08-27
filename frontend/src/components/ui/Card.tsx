// Travel Agent Pro - Card Component
// 可复用的卡片组件

import React from 'react'
import { cn } from '../../lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined'
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hover?: boolean
  children: React.ReactNode
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', padding = 'md', hover = false, children, ...props }, ref) => {
    const baseStyles = 'card'
    
    const variants = {
      default: '',
      elevated: 'shadow-lg',
      outlined: 'border-2'
    }
    
    const paddings = {
      none: '',
      sm: 'p-3',
      md: 'p-5',
      lg: 'p-6'
    }
    
    const hoverStyles = hover ? 'hover:transform hover:translate-y-[-4px] hover:shadow-lg transition-all duration-200' : ''
    
    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          paddings[padding],
          hoverStyles,
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

// 卡片头部组件
export function CardHeader({ 
  title, 
  subtitle, 
  action,
  className 
}: {
  title?: React.ReactNode
  subtitle?: React.ReactNode
  action?: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('flex justify-between items-start mb-4', className)}>
      <div>
        {title && (
          <h3 className="text-lg font-semibold text-[var(--foreground)]">
            {title}
          </h3>
        )}
        {subtitle && (
          <p className="text-[var(--muted-foreground)] mt-1">
            {subtitle}
          </p>
        )}
      </div>
      {action && (
        <div className="flex-shrink-0">
          {action}
        </div>
      )}
    </div>
  )
}

// 卡片内容组件
export function CardContent({ 
  children, 
  className 
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('', className)}>
      {children}
    </div>
  )
}

// 卡片底部组件
export function CardFooter({ 
  children, 
  className 
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('mt-4 pt-4 border-t border-[var(--border)]', className)}>
      {children}
    </div>
  )
}
