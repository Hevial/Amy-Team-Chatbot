import * as React from "react"
import { cn } from "@/lib/utils"

export function AmyLogo({ className, ...props }: React.ComponentProps<"svg">) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="none"
      className={cn("text-chart-4", className)}
      {...props}
    >
      {/* Main Large Spark */}
      <path 
        d="M11 1 Q11 10 20 10 Q11 10 11 19 Q11 10 2 10 Q11 10 11 1 Z" 
        fill="currentColor" 
      />
      
      {/* Secondary Smaller Spark */}
      <path 
        d="M18 13 Q18 18 23 18 Q18 18 18 23 Q18 18 13 18 Q18 18 18 13 Z" 
        fill="currentColor" 
        opacity="0.6" 
      />
    </svg>
  )
}
