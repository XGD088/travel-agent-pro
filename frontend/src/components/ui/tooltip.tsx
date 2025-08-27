"use client"

import * as React from "react"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"

export const TooltipProvider = TooltipPrimitive.Provider

export function Tooltip({ children }: { children: React.ReactNode }) {
  return <TooltipPrimitive.Root delayDuration={150}>{children}</TooltipPrimitive.Root>
}

export const TooltipTrigger = TooltipPrimitive.Trigger

export function TooltipContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        sideOffset={6}
        className={
          "z-50 overflow-hidden rounded-md border border-gray-200 bg-white px-3 py-2 text-xs text-gray-800 shadow-md " +
          (className || "")
        }
      >
        {children}
      </TooltipPrimitive.Content>
    </TooltipPrimitive.Portal>
  )
}


