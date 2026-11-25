import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { List, Map as MapIcon, SlidersHorizontal, X } from 'lucide-react'
import clsx from 'clsx'
import { api } from '../lib/api'
import type { Named, Paginated, VenueSummary } from '../lib/types'
import { VenueCard } from '../components/VenueCard'
import { VenueMap } from '../components/VenueMap'
import { Empty, Spinner } from '../components/ui'

const FILTER_KEYS = ['q', 'event_type', 'city', 'guests', 'max_price', 'available_on', 'amenities', 'min_rating', 'ordering', 'page'] as const

const SORTS = [
  { value: '', label: 'Best match' },
  { value: '-rating_avg', label: 'Top rated' },
  { value: 'price_per_day', label: 'Price: low to high' },
  { value: '-price_per_day', label: 'Price: high to low' },
  { value: '-capacity_max', label: 'Largest capacity' },
]

/** Debounce text inputs so we don't refetch on every keystroke. */
function useDebounced<T>(value: T, ms = 350) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

export function Venues() {
  const [params, setParams] = useSearchParams()
  const filters = Object.fromEntries(FILTER_KEYS.map((k) => [k, params.get(k) ?? ''])) as Record<(typeof FILTER_KEYS)[number], string>
  const [q, setQ] = useState(filters.q)
  const debouncedQ = useDebounced(q)
  const [showFilters, setShowFilters] = useState(false)
  const [view, setView] = useState<'list' | 'map'>('list')
  const [hovered, setHovered] = useState<number | null>(null)

  const set = (patch: Partial<typeof filters>) => {
    const next = new URLSearchParams(params)
    for (const [k, v] of Object.entries(patch)) (v ? next.set(k, v) : next.delete(k))
    if (!('page' in patch)) next.delete('page')
    setParams(next, { replace: true })
  }

  useEffect(() => {
    if (debouncedQ !== filters.q) set({ q: debouncedQ })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ])

  const { data: eventTypes } = useQuery({ queryKey: ['event-types'], queryFn: () => api<Named[]>('/event-types/') })
  const { data: amenities } = useQuery({ queryKey: ['amenities'], queryFn: () => api<Named[]>('/amenities/') })
  const { data: cities } = useQuery({ queryKey: ['cities'], queryFn: () => api<{ city: string; venue_count: number }[]>('/cities/') })
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['venues', filters],
    queryFn: () => api<Paginated<VenueSummary>>('/venues/', { query: filters }),
    placeholderData: keepPreviousData,
  })

  const selectedAmenities = new Set(filters.amenities.split(',').filter(Boolean))
  const toggleAmenity = (slug: string) => {
    const next = new Set(selectedAmenities)
    if (next.has(slug)) next.delete(slug)
    else next.add(slug)
    set({ amenities: [...next].join(',') })
  }
  const activeCount = ['event_type', 'city', 'guests', 'max_price', 'available_on', 'amenities', 'min_rating'].filter((k) => filters[k as keyof typeof filters]).length
  const page = Number(filters.page || 1)
  const pages = data ? Math.ceil(data.count / 12) : 1

  const filterPanel = (
    <div className="space-y-5">
      <div>
        <label className="label" htmlFor="f-type">Occasion</label>
        <select id="f-type" className="input" value={filters.event_type} onChange={(e) => set({ event_type: e.target.value })}>
          <option value="">Any</option>
          {eventTypes?.map((t) => <option key={t.slug} value={t.slug}>{t.name}</option>)}
        </select>
      </div>
      <div>
        <label className="label" htmlFor="f-city">City</label>
        <select id="f-city" className="input" value={filters.city} onChange={(e) => set({ city: e.target.value })}>
          <option value="">Anywhere</option>
          {cities?.map((c) => <option key={c.city} value={c.city}>{c.city} ({c.venue_count})</option>)}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label" htmlFor="f-guests">Guests</label>
          <input id="f-guests" type="number" min={1} className="input" value={filters.guests} onChange={(e) => set({ guests: e.target.value })} />
        </div>
        <div>
          <label className="label" htmlFor="f-date">Date</label>
          <input id="f-date" type="date" className="input px-2" value={filters.available_on} onChange={(e) => set({ available_on: e.target.value })} />
        </div>
      </div>
      <div>
        <label className="label" htmlFor="f-price">Max price per day (ETB)</label>
        <select id="f-price" className="input" value={filters.max_price} onChange={(e) => set({ max_price: e.target.value })}>
          <option value="">No limit</option>
          {[25000, 50000, 75000, 100000, 150000].map((p) => <option key={p} value={p}>Up to {p.toLocaleString()}</option>)}
        </select>
      </div>
      <div>
        <p className="label">Minimum rating</p>
        <div className="flex gap-2">
          {['', '3', '4', '4.5'].map((r) => (
            <button key={r} type="button" onClick={() => set({ min_rating: r })} className={clsx('rounded-full border px-3 py-1 text-sm', filters.min_rating === r ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-ink-300')}>
              {r ? `${r}+★` : 'Any'}
            </button>
          ))}
        </div>
      </div>
      <div>
        <p className="label">Amenities</p>
        <div className="flex flex-wrap gap-2">
          {amenities?.map((a) => (
            <button key={a.slug} type="button" onClick={() => toggleAmenity(a.slug)} className={clsx('rounded-full border px-3 py-1 text-sm', selectedAmenities.has(a.slug) ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-ink-300 hover:border-ink-500')}>
              {a.name}
            </button>
          ))}
        </div>
      </div>
      {activeCount > 0 && (
        <button className="btn-ghost w-full" onClick={() => setParams(filters.q ? { q: filters.q } : {})}>Clear filters</button>
      )}
    </div>
  )

  return (
    <div className="container-page py-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <input
          className="input flex-1 py-3 text-base"
          placeholder="Search venues, neighbourhoods… e.g. “garden Bole”"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search venues"
        />
        <div className="flex gap-2">
          <button className="btn-secondary lg:hidden" onClick={() => setShowFilters(true)}>
            <SlidersHorizontal className="size-4" /> Filters{activeCount > 0 && ` (${activeCount})`}
          </button>
          <select className="input w-auto" value={filters.ordering} onChange={(e) => set({ ordering: e.target.value })} aria-label="Sort">
            {SORTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
          <div className="hidden rounded-xl border border-ink-300 bg-white p-1 sm:flex xl:hidden">
            <button className={clsx('rounded-lg p-1.5', view === 'list' && 'bg-ink-100')} onClick={() => setView('list')} aria-label="List view"><List className="size-4" /></button>
            <button className={clsx('rounded-lg p-1.5', view === 'map' && 'bg-ink-100')} onClick={() => setView('map')} aria-label="Map view"><MapIcon className="size-4" /></button>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-8 lg:grid-cols-[260px_1fr] xl:grid-cols-[260px_1fr_400px]">
        <aside className="hidden lg:block">{filterPanel}</aside>

        <section className={clsx(view === 'map' && 'hidden xl:block')}>
          <p className="mb-4 text-sm text-ink-500">
            {data ? `${data.count} venue${data.count === 1 ? '' : 's'}` : ' '}
            {isFetching && !isLoading && ' · updating…'}
          </p>
          {isLoading ? (
            <Spinner />
          ) : data && data.results.length ? (
            <>
              <div className={clsx('grid gap-6 sm:grid-cols-2', isFetching && 'opacity-60')}>
                {data.results.map((v) => <VenueCard key={v.id} venue={v} highlighted={hovered === v.id} onHover={setHovered} />)}
              </div>
              {pages > 1 && (
                <div className="mt-8 flex items-center justify-center gap-2">
                  <button className="btn-secondary" disabled={page <= 1} onClick={() => set({ page: String(page - 1) })}>Previous</button>
                  <span className="text-sm text-ink-500">Page {page} of {pages}</span>
                  <button className="btn-secondary" disabled={page >= pages} onClick={() => set({ page: String(page + 1) })}>Next</button>
                </div>
              )}
            </>
          ) : (
            <Empty title="No venues match">Try a different date, fewer filters or a broader search.</Empty>
          )}
        </section>

        <aside className={clsx('xl:block', view === 'map' ? 'block lg:col-start-2' : 'hidden')}>
          <div className="sticky top-24 h-[70vh] overflow-hidden rounded-2xl border border-ink-100">
            <VenueMap venues={data?.results ?? []} activeId={hovered} className="size-full" />
          </div>
        </aside>
      </div>

      {showFilters && (
        <div className="fixed inset-0 z-40 flex lg:hidden" role="dialog" aria-modal="true" aria-label="Filters">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowFilters(false)} />
          <div className="relative ml-auto h-full w-full max-w-sm overflow-y-auto bg-white p-6">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-xl font-bold">Filters</h2>
              <button className="btn-ghost px-2" onClick={() => setShowFilters(false)} aria-label="Close"><X className="size-5" /></button>
            </div>
            {filterPanel}
            <button className="btn-primary mt-6 w-full" onClick={() => setShowFilters(false)}>Show {data?.count ?? ''} venues</button>
          </div>
        </div>
      )}
    </div>
  )
}
