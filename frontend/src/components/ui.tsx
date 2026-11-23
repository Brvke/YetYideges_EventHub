import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ImageIcon, Loader2, Star } from 'lucide-react'
import clsx from 'clsx'
import type { BookingStatus } from '../lib/types'

export function Stars({ value, size = 'sm' }: { value: number; size?: 'sm' | 'lg' }) {
  const cls = size === 'lg' ? 'size-5' : 'size-3.5'
  return (
    <span className="inline-flex" aria-label={`${value.toFixed(1)} out of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={clsx(cls, i <= Math.round(value) ? 'fill-saffron-400 text-saffron-400' : 'fill-ink-100 text-ink-300')}
        />
      ))}
    </span>
  )
}

export function StarInput({ value, onChange }: { value: number; onChange(v: number): void }) {
  return (
    <div className="flex gap-1" role="radiogroup" aria-label="Rating">
      {[1, 2, 3, 4, 5].map((i) => (
        <button
          key={i}
          type="button"
          role="radio"
          aria-checked={value === i}
          aria-label={`${i} star${i > 1 ? 's' : ''}`}
          onClick={() => onChange(i)}
          className="rounded p-0.5 transition hover:scale-110"
        >
          <Star className={clsx('size-7', i <= value ? 'fill-saffron-400 text-saffron-400' : 'text-ink-300')} />
        </button>
      ))}
    </div>
  )
}

/** Photo with a warm gradient placeholder when a venue has no photos yet. */
export function Cover({ src, alt, className }: { src: string | null | undefined; alt: string; className?: string }) {
  if (src) return <img src={src} alt={alt} loading="lazy" className={clsx('object-cover', className)} />
  const hue = [...alt].reduce((a, c) => a + c.charCodeAt(0), 0) % 40
  return (
    <div
      className={clsx('grid place-items-center text-white/80', className)}
      style={{ background: `linear-gradient(135deg, hsl(${10 + hue} 62% 48%), hsl(${35 + hue} 80% 58%))` }}
    >
      <ImageIcon className="size-8" />
    </div>
  )
}

const STATUS: Record<BookingStatus, string> = {
  pending: 'bg-saffron-400/20 text-amber-800',
  accepted: 'bg-emerald-100 text-emerald-800',
  declined: 'bg-red-100 text-red-700',
  cancelled: 'bg-ink-100 text-ink-500',
}
const STATUS_LABEL: Record<BookingStatus, string> = {
  pending: 'Awaiting reply', accepted: 'Confirmed', declined: 'Declined', cancelled: 'Cancelled',
}

export function StatusBadge({ status }: { status: BookingStatus }) {
  return <span className={clsx('rounded-full px-2.5 py-1 text-xs font-semibold', STATUS[status])}>{STATUS_LABEL[status]}</span>
}

export function Spinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-ink-500">
      <Loader2 className="size-5 animate-spin" /> {label}
    </div>
  )
}

export function Empty({ title, children, action }: { title: string; children?: ReactNode; action?: { to: string; label: string } }) {
  return (
    <div className="card px-6 py-14 text-center">
      <p className="font-display text-xl">{title}</p>
      {children && <div className="mx-auto mt-2 max-w-md text-sm text-ink-500">{children}</div>}
      {action && <Link to={action.to} className="btn-primary mt-5">{action.label}</Link>}
    </div>
  )
}

export function FieldError({ msg }: { msg?: string }) {
  return msg ? <p className="mt-1 text-xs text-red-600">{msg}</p> : null
}

export function Alert({ children, tone = 'error' }: { children: ReactNode; tone?: 'error' | 'success' | 'info' }) {
  const cls = { error: 'border-red-200 bg-red-50 text-red-800', success: 'border-emerald-200 bg-emerald-50 text-emerald-800', info: 'border-ink-100 bg-ink-50 text-ink-700' }[tone]
  return <div role={tone === 'error' ? 'alert' : 'status'} className={clsx('rounded-xl border px-4 py-3 text-sm', cls)}>{children}</div>
}
