// Travel Agent Pro - Modal Component
// 可复用的模态框组件

import React, { useEffect } from 'react'
import { X } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  description?: string
  children: React.ReactNode
  className?: string
  closeOnOverlayClick?: boolean
}

export function Modal({ 
  isOpen, 
  onClose, 
  title, 
  description, 
  children, 
  className,
  closeOnOverlayClick = true 
}: ModalProps) {
  
  // 处理 ESC 键关闭
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div 
      className={cn(
        'modal-overlay',
        isOpen ? 'active' : ''
      )}
      onClick={(e) => {
        if (closeOnOverlayClick && e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div className={cn('modal-content', className)}>
        {/* 头部 */}
        {(title || description) && (
          <div className="flex justify-between items-start mb-6">
            <div>
              {title && (
                <h2 className="text-2xl font-bold text-[var(--foreground)]">
                  {title}
                </h2>
              )}
              {description && (
                <p className="text-[var(--muted-foreground)] mt-2">
                  {description}
                </p>
              )}
            </div>
            <button 
              onClick={onClose}
              className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        )}
        
        {/* 内容 */}
        {children}
      </div>
    </div>
  )
}

// 模态框头部组件
export function ModalHeader({ 
  title, 
  description, 
  onClose 
}: {
  title: string
  description?: string
  onClose: () => void
}) {
  return (
    <div className="flex justify-between items-start mb-6">
      <div>
        <h2 className="text-2xl font-bold text-[var(--foreground)]">
          {title}
        </h2>
        {description && (
          <p className="text-[var(--muted-foreground)] mt-2">
            {description}
          </p>
        )}
      </div>
      <button 
        onClick={onClose}
        className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
      >
        <X className="w-6 h-6" />
      </button>
    </div>
  )
}

// 模态框底部组件
export function ModalFooter({ 
  children, 
  className 
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('mt-8 flex justify-end gap-4', className)}>
      {children}
    </div>
  )
}

