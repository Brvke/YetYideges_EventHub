import { useMemo, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, ChevronLeft, MapPin, MessageSquareReply, Users } from 'lucide-react'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'
import { isoDate, addDays, money, prettyDate } from '../lib/format'
import type { Booking, GooglePhoto, Paginated, Review, VenueDetail as Venue } from '../lib/types'
import { AvailabilityCalendar } from '../components/AvailabilityCalendar'
import { VenueMap } from '../components/VenueMap'
import { Alert, Cover, Empty, FieldError, Spinner, Stars } from '../components/ui'

export function VenueDetail() {
  const { slug } = useParams()
  const { data: venue, isLoading, error } = useQuery({
    queryKey: ['venue', slug],
    queryFn: () => api<Venue>(`/venues/${slug}/`),
  })

  if (isLoading) return <Spinner />
  if (error || !venue) return <div className="container-page py-16"><Empty title="Venue not found" action={{ to: '/venues', label: 'Browse venues' }} /></div>

  return (
    <div className="container-page py-6">
      <Link to="/venues" className="inline-flex items-center gap-1 text-sm text-ink-500 hover:text-ink-900"><ChevronLeft className="size-4" /> All venues</Link>

      <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold sm:text-4xl">{venue.name}</h1>
          <p className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-ink-500">
            {venue.rating_count > 0 && (
              <span className="flex items-center gap-1"><Stars value={Number(venue.rating_avg)} /> {Number(venue.rating_avg).toFixed(1)} · {venue.rating_count} reviews</span>
            )}
            <span className="flex items-center gap-1"><MapPin className="size-4" /> {[venue.area, venue.city].filter(Boolean).join(', ')}</span>
            <span className="flex items-center gap-1"><Users className="size-4" /> {venue.capacity_min}–{venue.capacity_max} guests</span>
          </p>
        </div>
      </div>

      <Gallery venue={venue} />
      <div className="mt-4"><ImportedNotice venue={venue} /></div>

      <div className="mt-8 grid gap-10 lg:grid-cols-[1fr_380px]">
        <div className="space-y-10">
          <section>
            {venue.tagline && <p className="font-display text-xl text-brand-700">{venue.tagline}</p>}
            <p className="mt-3 whitespace-pre-line leading-relaxed text-ink-700">{venue.description}</p>
            <p className="mt-4 text-sm text-ink-500">Hosted by {venue.owner_name}</p>
          </section>

          {venue.event_types.length > 0 && (
            <section>
              <h2 className="text-xl font-bold">Great for</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {venue.event_types.map((t) => <Link key={t.slug} to={`/venues?event_type=${t.slug}`} className="rounded-full bg-brand-50 px-3 py-1 text-sm text-brand-700 hover:bg-brand-100">{t.name}</Link>)}
              </div>
            </section>
          )}

          {venue.amenities.length > 0 && (
            <section>
              <h2 className="text-xl font-bold">Amenities</h2>
              <ul className="mt-3 grid gap-2 sm:grid-cols-2">
                {venue.amenities.map((a) => <li key={a.slug} className="flex items-center gap-2 text-ink-700"><Check className="size-4 text-emerald-600" /> {a.name}</li>)}
              </ul>
            </section>
          )}

          {venue.rental_policies && (
            <section>
              <h2 className="text-xl font-bold">Rental policies</h2>
              <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-ink-700">{venue.rental_policies}</p>
            </section>
          )}

          {venue.latitude && venue.longitude && (
            <section>
              <h2 className="text-xl font-bold">Location</h2>
              {venue.address && <p className="mt-1 text-sm text-ink-500">{venue.address}</p>}
              <div className="mt-3 h-72 overflow-hidden rounded-2xl border border-ink-100">
                <VenueMap venues={[venue]} className="size-full" />
              </div>
            </section>
          )}

          <Reviews venue={venue} />
        </div>

        <aside>
          <div className="lg:sticky lg:top-24"><BookingCard venue={venue} /></div>
        </aside>
      </div>
    </div>
  )
}

interface Slide {
  key: string
  src: string
  alt: string
  credit?: { name: string; url: string }[]
  /** free-licensed stock photo credit, e.g. "Author · CC BY-SA 4.0 · Wikimedia Commons" */
  stock?: { text: string; url: string; illustrative: boolean }
}

function Gallery({ venue }: { venue: Venue }) {
  const [active, setActive] = useState(0)
  // Owner photos win; imported venues fall back to live Google photos (never stored).
  const useGoogle = venue.photos.length === 0 && venue.source === 'google'
  const { data: google, isLoading } = useQuery({
    queryKey: ['google-photos', venue.slug],
    queryFn: () => api<{ photos: GooglePhoto[] }>(`/venues/${venue.slug}/google-photos/`),
    enabled: useGoogle,
    staleTime: 4 * 60_000, // Google photo URLs are short-lived
  })

  const slides: Slide[] = useGoogle
    ? (google?.photos ?? []).map((p, i) => ({ key: `g${i}`, src: p.url, alt: venue.name, credit: p.attributions }))
    : venue.photos.map((p) => ({
        key: String(p.id),
        src: p.image,
        alt: p.caption || venue.name,
        stock: p.credit ? { text: p.credit, url: p.credit_url, illustrative: p.is_illustrative } : undefined,
      }))

  if (useGoogle && isLoading) return <div className="mt-6 aspect-[21/9] w-full animate-pulse rounded-3xl bg-ink-100" />
  if (!slides.length) return <Cover src={null} alt={venue.name} className="mt-6 aspect-[21/9] w-full rounded-3xl" />
  const current = slides[Math.min(active, slides.length - 1)]

  return (
    <div className="mt-6">
      <div className="relative">
        <img src={current.src} alt={current.alt} referrerPolicy="no-referrer" className="aspect-[21/9] w-full rounded-3xl object-cover" />
        {current.credit && (
          <p className="absolute bottom-3 right-3 rounded-lg bg-black/60 px-2 py-1 text-xs text-white">
            Photo{current.credit.length ? ' by ' : ''}
            {current.credit.map((a, i) => (
              <span key={a.url || a.name}>{i > 0 && ', '}<a href={a.url} target="_blank" rel="noreferrer" className="underline">{a.name}</a></span>
            ))}
            {' · '}Google Maps
          </p>
        )}
        {current.stock && (
          <p className="absolute bottom-3 right-3 max-w-[80%] truncate rounded-lg bg-black/60 px-2 py-1 text-xs text-white">
            {current.stock.illustrative && <strong>Illustrative photo, not this venue · </strong>}
            <a href={current.stock.url} target="_blank" rel="noreferrer" className="underline">{current.stock.text}</a>
          </p>
        )}
      </div>
      {slides.length > 1 && (
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {slides.map((s, i) => (
            <button key={s.key} onClick={() => setActive(i)} className={`shrink-0 overflow-hidden rounded-xl ring-2 ${s === current ? 'ring-brand-600' : 'ring-transparent'}`} aria-label={`Photo ${i + 1}`}>
              <img src={s.src} alt="" referrerPolicy="no-referrer" className="h-16 w-24 object-cover" loading="lazy" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function ImportedNotice({ venue }: { venue: Venue }) {
  if (venue.source === 'owner' && !venue.details_estimated) return null
  const provider = venue.source === 'google' ? 'Google Maps' : venue.source === 'gebeta' ? 'Gebeta Maps' : null
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <strong>Demo listing.</strong>{' '}
      {provider && `Name, address and location come from ${provider}. `}
      {venue.source === 'osm' && <>Name and location from <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer" className="underline">© OpenStreetMap contributors</a>. </>}
      {venue.details_estimated && 'Price and capacity are estimates, not confirmed by the venue. '}
      {venue.google_maps_url && <a href={venue.google_maps_url} target="_blank" rel="noreferrer" className="font-semibold underline">View on Google Maps</a>}
    </div>
  )
}

function BookingCard({ venue }: { venue: Venue }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ event_date: '', guest_count: String(venue.capacity_min), event_type: venue.event_types[0]?.slug ?? '', message: '' })
  const [done, setDone] = useState<Booking | null>(null)

  const start = isoDate(new Date())
  const { data: avail } = useQuery({
    queryKey: ['availability', venue.slug],
    queryFn: () => api<{ unavailable: string[] }>(`/venues/${venue.slug}/availability/`, { query: { start, end: isoDate(addDays(new Date(), 365)) } }),
  })
  const unavailable = useMemo(() => new Set(avail?.unavailable ?? []), [avail])

  const book = useMutation({
    mutationFn: () => api<Booking>('/bookings/', { body: { venue: venue.slug, ...form, guest_count: Number(form.guest_count), event_type: form.event_type || null } }),
    onSuccess: (b) => {
      setDone(b)
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
    },
  })
  const err = book.error instanceof ApiError ? book.error : null

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!user) return navigate('/login', { state: { from: location.pathname } })
    book.mutate()
  }

  if (done) {
    return (
      <div className="card p-6">
        <div className="grid size-12 place-items-center rounded-full bg-emerald-100 text-emerald-700"><Check className="size-6" /></div>
        <h3 className="mt-4 text-xl font-bold">Request sent!</h3>
        <p className="mt-2 text-sm text-ink-500">
          We've asked {venue.owner_name || 'the host'} to confirm <strong>{prettyDate(done.event_date)}</strong> for {done.guest_count} guests. You'll see their reply in My bookings.
        </p>
        <Link to="/bookings" className="btn-primary mt-5 w-full">View my bookings</Link>
      </div>
    )
  }

  return (
    <form onSubmit={submit} className="card space-y-4 p-6">
      <p>
        {venue.details_estimated && <span className="mr-1 text-sm text-ink-500">about</span>}
        <span className="text-2xl font-bold">{money(venue.price_per_day)}</span> <span className="text-ink-500">/ event day</span>
      </p>
      {venue.details_estimated && <p className="-mt-2 text-xs text-ink-500">Estimated: confirm the price with the venue.</p>}

      <div>
        <p className="label">Pick your date</p>
        <AvailabilityCalendar unavailable={unavailable} selected={form.event_date} onSelect={(d) => setForm({ ...form, event_date: d })} />
        <FieldError msg={err?.fields.event_date} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label" htmlFor="b-guests">Guests</label>
          <input id="b-guests" type="number" className="input" min={venue.capacity_min} max={venue.capacity_max} required value={form.guest_count} onChange={(e) => setForm({ ...form, guest_count: e.target.value })} />
          <FieldError msg={err?.fields.guest_count} />
        </div>
        <div>
          <label className="label" htmlFor="b-type">Occasion</label>
          <select id="b-type" className="input" value={form.event_type} onChange={(e) => setForm({ ...form, event_type: e.target.value })}>
            <option value="">Other</option>
            {venue.event_types.map((t) => <option key={t.slug} value={t.slug}>{t.name}</option>)}
          </select>
        </div>
      </div>
      <div>
        <label className="label" htmlFor="b-msg">Message to the host <span className="font-normal text-ink-500">(optional)</span></label>
        <textarea id="b-msg" rows={3} className="input" placeholder="Tell them about your event, timings, catering needs…" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
      </div>

      {err && !err.fields.event_date && !err.fields.guest_count && <Alert>{err.message}</Alert>}

      <button className="btn-primary w-full py-3" disabled={!form.event_date || book.isPending}>
        {book.isPending ? 'Sending…' : user ? (form.event_date ? `Request ${prettyDate(form.event_date, { day: 'numeric', month: 'short' })}` : 'Choose a date') : 'Log in to request'}
      </button>
      <p className="text-center text-xs text-ink-500">You won't be charged now. The host confirms first.</p>
    </form>
  )
}

function Reviews({ venue }: { venue: Venue }) {
  const { data } = useQuery({
    queryKey: ['venue-reviews', venue.slug],
    queryFn: () => api<Paginated<Review>>(`/venues/${venue.slug}/reviews/`),
  })
  const reviews = data?.results ?? []
  const dist = [5, 4, 3, 2, 1].map((s) => ({ s, n: reviews.filter((r) => r.rating === s).length }))

  return (
    <section>
      <h2 className="text-xl font-bold">Reviews</h2>
      {reviews.length === 0 ? (
        <p className="mt-2 text-sm text-ink-500">No reviews yet. Reviews come only from guests whose event was confirmed here.</p>
      ) : (
        <>
          <div className="mt-4 grid items-center gap-6 sm:grid-cols-[auto_1fr]">
            <div className="text-center">
              <p className="font-display text-5xl font-bold">{Number(venue.rating_avg).toFixed(1)}</p>
              <Stars value={Number(venue.rating_avg)} size="lg" />
              <p className="mt-1 text-sm text-ink-500">{venue.rating_count} verified reviews</p>
            </div>
            <div className="space-y-1">
              {dist.map(({ s, n }) => (
                <div key={s} className="flex items-center gap-2 text-sm">
                  <span className="w-3">{s}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-ink-100"><div className="h-full bg-saffron-400" style={{ width: `${(n / reviews.length) * 100}%` }} /></div>
                  <span className="w-6 text-right text-ink-500">{n}</span>
                </div>
              ))}
            </div>
          </div>
          <ul className="mt-6 space-y-4">
            {reviews.map((r) => (
              <li key={r.id} className="card p-5">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{r.author_name}</p>
                  <Stars value={r.rating} />
                </div>
                <p className="text-xs text-ink-500">Event on {prettyDate(r.event_date, { month: 'long', year: 'numeric' })}</p>
                {r.comment && <p className="mt-2 text-sm text-ink-700">{r.comment}</p>}
                {r.owner_reply && (
                  <div className="mt-3 rounded-xl bg-ink-50 p-3 text-sm">
                    <p className="flex items-center gap-1 font-semibold"><MessageSquareReply className="size-4" /> Host reply</p>
                    <p className="mt-1 text-ink-700">{r.owner_reply}</p>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
