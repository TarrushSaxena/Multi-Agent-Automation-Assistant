"use client";

import { useId } from "react";

/**
 * Gradient "assistant" mark — a stylized person/head figure filled with the aurora gradient.
 * useId keeps the gradient id stable across server and client render (no hydration mismatch).
 */
export function BrandLogo({ className }: { className?: string }) {
  const id = `brand-grad-${useId()}`;
  return (
    <svg viewBox="0 0 48 48" className={className} role="img" aria-label="Assistant logo" fill="none">
      <defs>
        <linearGradient id={id} x1="8" y1="4" x2="40" y2="44" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="var(--aurora-1)" />
          <stop offset="0.5" stopColor="var(--aurora-2)" />
          <stop offset="1" stopColor="var(--aurora-3)" />
        </linearGradient>
      </defs>
      {/* Head */}
      <circle cx="24" cy="15" r="8" fill={`url(#${id})`} />
      {/* Shoulders / body */}
      <path
        d="M8 44c0-8.837 7.163-16 16-16s16 7.163 16 16a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2Z"
        fill={`url(#${id})`}
      />
      {/* Spark accent — signals AI */}
      <path
        d="M37 6.5c.2 2.4.9 3.1 3.3 3.3-2.4.2-3.1.9-3.3 3.3-.2-2.4-.9-3.1-3.3-3.3 2.4-.2 3.1-.9 3.3-3.3Z"
        fill="var(--aurora-3)"
      />
    </svg>
  );
}
