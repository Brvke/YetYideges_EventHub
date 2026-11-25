import { Link } from 'react-router-dom'
import { MapPin, Users } from 'lucide-react'
import clsx from 'clsx'
import { moneyCompact } from '../lib/format'
import type { VenueSummary } from '../lib/types'
import { Cover, Stars } from './ui'

export function VenueCard({ venue, highlighted, onHover }: { venue: VenueSummary; highlighted?: boolean; onHover?(id: number | null): void }) {
  return (
    <Link
      to={`/venues/${venue.slug}`}
      onMouseEnter={() => onHover?.(venue.id)}
      onMouseLeave={() => onHover?.(null)}
      className={clsx('card group overflow-hidden transition hover:-translate-y-0.5 hover:shadow-md', highlighted && 'ring-2 ring-brand-500')}
    >
      <div className="relative aspect-[4/3] overflow-hidden">
        <Cover
          src={venue.cover_photo}
          alt={venue.name}
          className="size-full transition duration-500 group-hover:scale-105"
          credit={venue.cover_is_illustrative ? 'Illustrative photo' : venue.source === 'google' ? 'Photo: Google Maps' : undefined}
        />
        <span className="absolute left-3 top-3 rounded-full bg-white/95 px-2.5 py-1 text-xs font-semibold shadow-sm">
          {venue.details_estimated && <span className="font-normal text-ink-500">~</span>}{moneyCompact(venue.price_per_day)} <span className="font-normal text-ink-500">/ day</span>
        </span>
      </div>
      <div className="space-y-1.5 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-sans text-base font-semibold leading-snug">{venue.name}</h3>
          {venue.rating_count > 0 && (
            <span className="flex shrink-0 items-center gap-1 text-sm">
              <Stars value={Number(venue.rating_avg)} />
              <span className="text-ink-500">({venue.rating_count})</span>
            </span>
          )}
        </div>
        <p className="flex items-center gap-1 text-sm text-ink-500">
          <MapPin className="size-3.5" /> {[venue.area, venue.city].filter(Boolean).join(', ')}
        </p>
        <p className="flex items-center gap-1 text-sm text-ink-500">
          <Users className="size-3.5" /> {venue.capacity_min}–{venue.capacity_max} guests
        </p>
        {venue.event_types.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {venue.event_types.slice(0, 3).map((t) => (
              <span key={t.slug} className="rounded-full bg-ink-100 px-2 py-0.5 text-xs text-ink-700">{t.name}</span>
            ))}
          </div>
        )}
      </div>
    </Link>
  )
}
