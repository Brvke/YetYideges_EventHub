import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CalendarDays, Star, Users, X } from 'lucide-react'
import clsx from 'clsx'
import { api, ApiError } from '../lib/api'
import { money, prettyDate } from '../lib/format'
import type { Booking, Paginated } from '../lib/types'
import { Alert, Cover, Empty, Spinner, StarInput, StatusBadge } from '../components/ui'

type Tab = 'upcoming' | 'past'

export function MyBookings() {
  const [tab, setTab] = useState<Tab>('upcoming')
  const [reviewing, setReviewing] = useState<Booking | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['bookings', tab],
    queryFn: () => api<Paginated<Booking>>('/bookings/', { query: { when: tab } }),
  })

  const cancel = useMutation({
    mutationFn: (id: number) => api<Booking>(`/bookings/${id}/cancel/`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['bookings'] }),
  })

  return (
    <div className="container-page max-w-4xl py-10">
      <h1 className="text-3xl font-bold">My bookings</h1>
      <div className="mt-6 inline-flex rounded-xl border border-ink-300 bg-white p-1">
        {(['upcoming', 'past'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={clsx('rounded-lg px-4 py-1.5 text-sm font-medium capitalize', tab === t ? 'bg-ink-900 text-white' : 'text-ink-700')}>{t}</button>
        ))}
      </div>

      <div className="mt-6 space-y-4">
        {isLoading ? <Spinner /> : !data?.results.length ? (
          <Empty title={tab === 'upcoming' ? 'No upcoming events yet' : 'No past events'} action={tab === 'upcoming' ? { to: '/venues', label: 'Find a venue' } : undefined}>
            {tab === 'upcoming' && 'When you request a venue, it will show up here with the host’s reply.'}
          </Empty>
        ) : data.results.map((b) => (
          <article key={b.id} className="card flex flex-col gap-4 overflow-hidden sm:flex-row">
            <Link to={`/venues/${b.venue.slug}`} className="sm:w-48 sm:shrink-0">
              <Cover src={b.venue.cover_photo} alt={b.venue.name} className="h-40 w-full sm:h-full" />
            </Link>
            <div className="flex flex-1 flex-col gap-2 p-5 sm:pl-0">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <Link to={`/venues/${b.venue.slug}`} className="text-lg font-semibold hover:underline">{b.venue.name}</Link>
                  <p className="text-sm text-ink-500">{[b.venue.area, b.venue.city].filter(Boolean).join(', ')}</p>
                </div>
                <StatusBadge status={b.status} />
              </div>
              <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-ink-700">
                <span className="flex items-center gap-1"><CalendarDays className="size-4" /> {prettyDate(b.event_date)}</span>
                <span className="flex items-center gap-1"><Users className="size-4" /> {b.guest_count} guests</span>
                <span>{money(b.quoted_price)}</span>
              </div>
              {b.owner_note && <p className="rounded-lg bg-ink-50 px-3 py-2 text-sm text-ink-700"><strong>Host:</strong> {b.owner_note}</p>}
              <div className="mt-auto flex flex-wrap gap-2 pt-2">
                {b.can_review && (
                  <button className="btn-primary" onClick={() => setReviewing(b)}><Star className="size-4" /> Write a review</button>
                )}
                {b.review_id && <span className="text-sm text-emerald-700">✓ Thanks for your review</span>}
                {tab === 'upcoming' && (b.status === 'pending' || b.status === 'accepted') && (
                  <button className="btn-danger" disabled={cancel.isPending}
                    onClick={() => confirm(`Cancel your ${b.status === 'accepted' ? 'confirmed booking' : 'request'} at ${b.venue.name}?`) && cancel.mutate(b.id)}>
                    {b.status === 'accepted' ? 'Cancel booking' : 'Withdraw request'}
                  </button>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>

      {reviewing && <ReviewDialog booking={reviewing} onClose={() => setReviewing(null)} />}
    </div>
  )
}

function ReviewDialog({ booking, onClose }: { booking: Booking; onClose(): void }) {
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState('')
  const queryClient = useQueryClient()
  const save = useMutation({
    mutationFn: () => api('/reviews/', { body: { booking: booking.id, rating, comment } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      queryClient.invalidateQueries({ queryKey: ['venue-reviews', booking.venue.slug] })
      queryClient.invalidateQueries({ queryKey: ['venue', booking.venue.slug] })
      onClose()
    },
  })

  function submit(e: FormEvent) {
    e.preventDefault()
    save.mutate()
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4" role="dialog" aria-modal="true" aria-labelledby="rv-title">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <form onSubmit={submit} className="card relative w-full max-w-lg space-y-4 p-6">
        <button type="button" className="btn-ghost absolute right-3 top-3 px-2" onClick={onClose} aria-label="Close"><X className="size-5" /></button>
        <h2 id="rv-title" className="text-xl font-bold">How was {booking.venue.name}?</h2>
        <p className="text-sm text-ink-500">Your event on {prettyDate(booking.event_date)}</p>
        <StarInput value={rating} onChange={setRating} />
        <textarea className="input" rows={4} placeholder="What went well? Anything future guests should know?" value={comment} onChange={(e) => setComment(e.target.value)} />
        {save.error && <Alert>{(save.error as ApiError).message}</Alert>}
        <button className="btn-primary w-full" disabled={!rating || save.isPending}>{save.isPending ? 'Posting…' : 'Post review'}</button>
      </form>
    </div>
  )
}
