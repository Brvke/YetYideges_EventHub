import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CalendarDays, Check, Eye, EyeOff, Mail, Pencil, Phone, Plus, Users, X } from 'lucide-react'
import clsx from 'clsx'
import { api, ApiError } from '../../lib/api'
import { isoDate, money, moneyCompact, prettyDate } from '../../lib/format'
import type { Booking, OwnerStats, OwnerVenue, Paginated, Review } from '../../lib/types'
import { Alert, Cover, Empty, Spinner, Stars, StatusBadge } from '../../components/ui'

type Tab = 'requests' | 'upcoming' | 'venues' | 'reviews'

export function OwnerDashboard() {
  const [tab, setTab] = useState<Tab>('requests')
  const { data: stats } = useQuery({ queryKey: ['owner', 'stats'], queryFn: () => api<OwnerStats>('/owner/stats/') })

  const tiles = stats && [
    { label: 'Pending requests', value: stats.pending_requests, accent: stats.pending_requests > 0 },
    { label: 'Upcoming events', value: stats.upcoming_events },
    { label: `Revenue ${new Date().getFullYear()}`, value: moneyCompact(stats.revenue_this_year) },
    { label: 'Average rating', value: stats.review_count ? `${stats.average_rating.toFixed(1)} ★` : '—', sub: stats.review_count ? `${stats.review_count} reviews` : undefined },
    { label: 'Acceptance rate', value: stats.acceptance_rate === null ? '—' : `${stats.acceptance_rate}%` },
  ]

  return (
    <div className="container-page py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold">Host dashboard</h1>
        <Link to="/owner/venues/new" className="btn-primary"><Plus className="size-4" /> Add a venue</Link>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-5">
        {tiles?.map((t) => (
          <div key={t.label} className={clsx('card p-4', t.accent && 'border-brand-200 bg-brand-50')}>
            <p className="text-xs font-medium uppercase tracking-wide text-ink-500">{t.label}</p>
            <p className="mt-1 font-display text-2xl font-bold">{t.value}</p>
            {t.sub && <p className="text-xs text-ink-500">{t.sub}</p>}
          </div>
        ))}
      </div>

      <div className="mt-8 flex gap-1 overflow-x-auto border-b border-ink-100">
        {([['requests', 'Requests'], ['upcoming', 'Upcoming'], ['venues', 'My venues'], ['reviews', 'Reviews']] as const).map(([k, label]) => (
          <button key={k} onClick={() => setTab(k)} className={clsx('-mb-px whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium', tab === k ? 'border-brand-600 text-brand-700' : 'border-transparent text-ink-500 hover:text-ink-900')}>
            {label}{k === 'requests' && stats?.pending_requests ? <span className="ml-1.5 rounded-full bg-brand-600 px-1.5 text-xs text-white">{stats.pending_requests}</span> : null}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {tab === 'requests' && <BookingList status="pending" empty="No requests waiting. New booking requests will appear here." />}
        {tab === 'upcoming' && <BookingList status="accepted" empty="No confirmed events coming up." />}
        {tab === 'venues' && <VenueList />}
        {tab === 'reviews' && <ReviewList />}
      </div>
    </div>
  )
}

function BookingList({ status, empty }: { status: 'pending' | 'accepted'; empty: string }) {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['owner', 'bookings', status],
    queryFn: () => api<Paginated<Booking>>('/owner/bookings/', { query: { status, ordering: 'event_date' } }),
  })
  const [error, setError] = useState('')
  const decide = useMutation({
    mutationFn: ({ id, verb, note }: { id: number; verb: 'accept' | 'decline'; note?: string }) =>
      api<Booking>(`/owner/bookings/${id}/${verb}/`, { body: { note: note ?? '' } }),
    onSuccess: () => { setError(''); queryClient.invalidateQueries({ queryKey: ['owner'] }) },
    onError: (e) => setError((e as ApiError).message),
  })

  const today = isoDate(new Date())
  const rows = (data?.results ?? []).filter((b) => b.event_date >= today)
  if (isLoading) return <Spinner />
  if (!rows.length) return <Empty title="All caught up">{empty}</Empty>

  // Group requests that compete for the same venue + date, so the owner sees the conflict.
  const clash = new Map<string, number>()
  rows.forEach((b) => clash.set(`${b.venue.id}:${b.event_date}`, (clash.get(`${b.venue.id}:${b.event_date}`) ?? 0) + 1))

  return (
    <div className="space-y-3">
      {error && <Alert>{error}</Alert>}
      {rows.map((b) => {
        const competing = (clash.get(`${b.venue.id}:${b.event_date}`) ?? 1) - 1
        return (
          <article key={b.id} className="card p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-semibold">{b.guest.name || b.guest.email} <span className="font-normal text-ink-500">→ {b.venue.name}</span></p>
                <div className="mt-1 flex flex-wrap gap-x-5 gap-y-1 text-sm text-ink-700">
                  <span className="flex items-center gap-1"><CalendarDays className="size-4" /> {prettyDate(b.event_date)}</span>
                  <span className="flex items-center gap-1"><Users className="size-4" /> {b.guest_count} guests</span>
                  {b.event_type && <span className="capitalize">{b.event_type.replace(/-/g, ' ')}</span>}
                  <span>{money(b.quoted_price)}</span>
                </div>
              </div>
              <StatusBadge status={b.status} />
            </div>
            {b.message && <p className="mt-3 rounded-lg bg-ink-50 px-3 py-2 text-sm italic text-ink-700">“{b.message}”</p>}
            <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-ink-500">
              <a href={`mailto:${b.guest.email}`} className="flex items-center gap-1 hover:text-ink-900"><Mail className="size-4" /> {b.guest.email}</a>
              {b.guest.phone && <a href={`tel:${b.guest.phone}`} className="flex items-center gap-1 hover:text-ink-900"><Phone className="size-4" /> {b.guest.phone}</a>}
            </div>
            {status === 'pending' && (
              <>
                {competing > 0 && <p className="mt-3 text-sm text-amber-700">⚠ {competing} other request{competing > 1 ? 's' : ''} for this date. Accepting this one declines the others automatically.</p>}
                <div className="mt-4 flex gap-2">
                  <button className="btn-primary" disabled={decide.isPending} onClick={() => decide.mutate({ id: b.id, verb: 'accept' })}><Check className="size-4" /> Accept</button>
                  <button className="btn-secondary" disabled={decide.isPending}
                    onClick={() => { const note = prompt('Optional note to the guest (e.g. suggest another date):'); if (note !== null) decide.mutate({ id: b.id, verb: 'decline', note }) }}>
                    <X className="size-4" /> Decline
                  </button>
                </div>
              </>
            )}
          </article>
        )
      })}
    </div>
  )
}

function VenueList() {
  const { data, isLoading } = useQuery({ queryKey: ['owner', 'venues'], queryFn: () => api<Paginated<OwnerVenue & { pending_requests?: number }>>('/owner/venues/') })
  if (isLoading) return <Spinner />
  if (!data?.results.length) return <Empty title="List your first venue" action={{ to: '/owner/venues/new', label: 'Add a venue' }}>It takes about five minutes. You can save it as a draft and publish later.</Empty>
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data.results.map((v) => (
        <div key={v.id} className="card overflow-hidden">
          <Cover src={v.photos[0]?.image} alt={v.name} className="aspect-[16/9] w-full" />
          <div className="p-4">
            <div className="flex items-start justify-between gap-2">
              <p className="font-semibold">{v.name}</p>
              <span className={clsx('flex shrink-0 items-center gap-1 text-xs', v.is_published ? 'text-emerald-700' : 'text-ink-500')}>
                {v.is_published ? <><Eye className="size-3.5" /> Live</> : <><EyeOff className="size-3.5" /> Draft</>}
              </span>
            </div>
            <p className="text-sm text-ink-500">{v.city} · {money(v.price_per_day)} / day</p>
            <p className="mt-1 text-sm text-ink-500">{v.photos.length} photos{v.rating_count ? ` · ${Number(v.rating_avg).toFixed(1)}★ (${v.rating_count})` : ''}</p>
            <div className="mt-3 flex gap-2">
              <Link to={`/owner/venues/${v.id}`} className="btn-secondary flex-1"><Pencil className="size-4" /> Edit</Link>
              {v.is_published && <Link to={`/venues/${v.slug}`} className="btn-ghost">View</Link>}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function ReviewList() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['owner', 'reviews'], queryFn: () => api<Paginated<Review>>('/owner/reviews/') })
  const [drafts, setDrafts] = useState<Record<number, string>>({})
  const reply = useMutation({
    mutationFn: ({ id, text }: { id: number; text: string }) => api(`/owner/reviews/${id}/reply/`, { body: { owner_reply: text } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['owner', 'reviews'] }),
  })
  if (isLoading) return <Spinner />
  if (!data?.results.length) return <Empty title="No reviews yet">Guests can review after their confirmed event.</Empty>
  return (
    <div className="space-y-3">
      {data.results.map((r) => (
        <article key={r.id} className="card p-5">
          <div className="flex items-center justify-between">
            <p className="font-semibold">{r.author_name} <span className="font-normal text-ink-500">· {r.venue}</span></p>
            <Stars value={r.rating} />
          </div>
          {r.comment && <p className="mt-2 text-sm text-ink-700">{r.comment}</p>}
          {r.owner_reply ? (
            <p className="mt-3 rounded-lg bg-ink-50 px-3 py-2 text-sm"><strong>Your reply:</strong> {r.owner_reply}</p>
          ) : (
            <form className="mt-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); reply.mutate({ id: r.id, text: drafts[r.id] ?? '' }) }}>
              <input className="input" placeholder="Write a public reply…" value={drafts[r.id] ?? ''} onChange={(e) => setDrafts({ ...drafts, [r.id]: e.target.value })} />
              <button className="btn-secondary" disabled={!drafts[r.id]?.trim() || reply.isPending}>Reply</button>
            </form>
          )}
        </article>
      ))}
    </div>
  )
}
