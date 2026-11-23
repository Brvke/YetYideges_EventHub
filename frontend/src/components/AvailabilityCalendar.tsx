import { useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import clsx from 'clsx'
import { isoDate } from '../lib/format'

interface Props {
  unavailable: Set<string>
  selected?: string
  onSelect?(iso: string): void
  /** owner mode: past days are still clickable-disabled, but booked/blocked can be toggled */
  mode?: 'book' | 'manage'
  blocked?: Set<string>
}

const WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']

export function AvailabilityCalendar({ unavailable, selected, onSelect, mode = 'book', blocked }: Props) {
  const today = useMemo(() => isoDate(new Date()), [])
  const [cursor, setCursor] = useState(() => {
    const d = new Date()
    return new Date(d.getFullYear(), d.getMonth(), 1)
  })

  const days = useMemo(() => {
    const first = new Date(cursor)
    const offset = (first.getDay() + 6) % 7 // Monday-first
    const count = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0).getDate()
    return [
      ...Array.from({ length: offset }, () => null),
      ...Array.from({ length: count }, (_, i) => isoDate(new Date(cursor.getFullYear(), cursor.getMonth(), i + 1))),
    ]
  }, [cursor])

  const thisMonth = new Date().getFullYear() * 12 + new Date().getMonth()
  const cursorMonth = cursor.getFullYear() * 12 + cursor.getMonth()

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <button
          type="button"
          className="btn-ghost px-2"
          disabled={cursorMonth <= thisMonth}
          onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1))}
          aria-label="Previous month"
        >
          <ChevronLeft className="size-4" />
        </button>
        <p className="text-sm font-semibold">{cursor.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}</p>
        <button
          type="button"
          className="btn-ghost px-2"
          disabled={cursorMonth >= thisMonth + 11}
          onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1))}
          aria-label="Next month"
        >
          <ChevronRight className="size-4" />
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs">
        {WEEKDAYS.map((w) => <div key={w} className="py-1 font-medium text-ink-500">{w}</div>)}
        {days.map((iso, i) => {
          if (!iso) return <div key={`b${i}`} />
          const past = iso <= today
          const isBlocked = blocked?.has(iso)
          const taken = unavailable.has(iso)
          const disabled = past || (mode === 'book' && taken) || (mode === 'manage' && taken && !isBlocked)
          return (
            <button
              key={iso}
              type="button"
              disabled={disabled}
              onClick={() => onSelect?.(iso)}
              title={taken ? (isBlocked ? 'Blocked by you' : 'Booked') : undefined}
              className={clsx(
                'aspect-square rounded-lg text-sm transition',
                selected === iso && 'bg-brand-600 font-semibold text-white',
                selected !== iso && !disabled && !taken && 'hover:bg-brand-50',
                past && 'text-ink-300',
                !past && taken && !isBlocked && 'bg-ink-100 text-ink-500 line-through',
                !past && isBlocked && 'bg-amber-100 text-amber-800',
              )}
            >
              {Number(iso.slice(8))}
            </button>
          )
        })}
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-ink-500">
        <span className="flex items-center gap-1"><span className="size-3 rounded bg-ink-100" /> Booked</span>
        {mode === 'manage' && <span className="flex items-center gap-1"><span className="size-3 rounded bg-amber-100" /> Blocked</span>}
        {mode === 'book' && <span className="flex items-center gap-1"><span className="size-3 rounded bg-brand-600" /> Your date</span>}
      </div>
    </div>
  )
}
