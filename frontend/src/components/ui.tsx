import type { ButtonHTMLAttributes, ReactNode } from 'react'
import type { SentimentLabel } from '../api/types'

type Variant = 'primary' | 'quiet'

const variants: Record<Variant, string> = {
  primary:
    'bg-action text-white hover:bg-action-strong disabled:bg-rule disabled:text-muted px-5 py-2.5',
  quiet: 'text-muted hover:text-ink hover:bg-rule/50 px-3 py-2',
}

export function Button({
  variant = 'primary',
  busy = false,
  className = '',
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; busy?: boolean }) {
  return (
    <button
      className={`inline-flex items-center gap-2 rounded-lg text-[15px] font-medium transition-colors disabled:cursor-not-allowed ${variants[variant]} ${className}`}
      disabled={busy || props.disabled}
      aria-busy={busy}
      {...props}
    >
      {busy && <Dots />}
      {children}
    </button>
  )
}

export function Dots({ className = '' }: { className?: string }) {
  return (
    <span className={`inline-flex gap-1 ${className}`} aria-hidden>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="size-1.5 animate-pulse rounded-full bg-current"
          style={{ animationDelay: `${i * 160}ms` }}
        />
      ))}
    </span>
  )
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="flex items-start justify-between gap-4 rounded-lg border border-negative/30 bg-negative/5 px-4 py-3 text-[15px] text-negative"
    >
      <p>{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="shrink-0 font-medium underline underline-offset-2">
          Try again
        </button>
      )}
    </div>
  )
}

const sentimentColor: Record<SentimentLabel, string> = {
  positive: 'text-positive',
  neutral: 'text-neutral',
  negative: 'text-negative',
  mixed: 'text-mixed',
}

export function SentimentDot({ label }: { label: SentimentLabel }) {
  return (
    <span className={`inline-flex items-center gap-1.5 capitalize ${sentimentColor[label]}`}>
      <span className="size-2 rounded-full bg-current" aria-hidden />
      {label}
    </span>
  )
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-rule pt-6">
      <h2 className="mb-4 text-[15px] font-semibold text-ink">{title}</h2>
      {children}
    </section>
  )
}
