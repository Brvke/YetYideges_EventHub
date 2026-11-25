import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ImagePlus, Loader2, Trash2 } from 'lucide-react'
import clsx from 'clsx'
import { api, ApiError } from '../../lib/api'
import { addDays, isoDate, prettyDate } from '../../lib/format'
import type { BlockedDate, Named, OwnerVenue } from '../../lib/types'
import { AvailabilityCalendar } from '../../components/AvailabilityCalendar'
import { Alert, FieldError, Spinner } from '../../components/ui'

type Form = Omit<OwnerVenue, 'id' | 'slug' | 'photos' | 'rating_avg' | 'rating_count' | 'created_at'>

const EMPTY: Form = {
  name: '', tagline: '', description: '', city: 'Addis Ababa', area: '', address: '',
  latitude: null, longitude: null, capacity_min: 1, capacity_max: 100, price_per_day: '',
  event_types: [], amenities: [], rental_policies: '', is_published: true,
}

export function VenueEditor() {
  const { id } = useParams()
  const isNew = !id
  const { data: venue, isLoading } = useQuery({
    queryKey: ['owner', 'venue', id],
    queryFn: () => api<OwnerVenue>(`/owner/venues/${id}/`),
    enabled: !isNew,
  })
  if (!isNew && isLoading) return <Spinner />

  return (
    <div className="container-page max-w-4xl py-10">
      <Link to="/owner" className="inline-flex items-center gap-1 text-sm text-ink-500 hover:text-ink-900"><ChevronLeft className="size-4" /> Dashboard</Link>
      <h1 className="mt-2 text-3xl font-bold">{isNew ? 'Add a venue' : `Edit ${venue?.name}`}</h1>
      <DetailsForm venue={venue} />
      {venue && (
        <>
          <Photos venue={venue} />
          <BlockedDates venue={venue} />
        </>
      )}
    </div>
  )
}

function Chips({ options, value, onChange }: { options?: Named[]; value: string[]; onChange(v: string[]): void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {options?.map((o) => {
        const on = value.includes(o.slug)
        return (
          <button key={o.slug} type="button" aria-pressed={on} onClick={() => onChange(on ? value.filter((s) => s !== o.slug) : [...value, o.slug])}
            className={clsx('rounded-full border px-3 py-1 text-sm', on ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-ink-300 hover:border-ink-500')}>
            {o.name}
          </button>
        )
      })}
    </div>
  )
}

function DetailsForm({ venue }: { venue?: OwnerVenue }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form, setForm] = useState<Form>(EMPTY)
  const [saved, setSaved] = useState(false)
  useEffect(() => { if (venue) setForm({ ...EMPTY, ...venue }) }, [venue])

  const { data: eventTypes } = useQuery({ queryKey: ['event-types'], queryFn: () => api<Named[]>('/event-types/') })
  const { data: amenities } = useQuery({ queryKey: ['amenities'], queryFn: () => api<Named[]>('/amenities/') })

  const save = useMutation({
    mutationFn: () => api<OwnerVenue>(venue ? `/owner/venues/${venue.id}/` : '/owner/venues/', {
      method: venue ? 'PATCH' : 'POST',
      body: { ...form, latitude: form.latitude || null, longitude: form.longitude || null },
    }),
    onSuccess: (v) => {
      queryClient.invalidateQueries({ queryKey: ['owner'] })
      queryClient.invalidateQueries({ queryKey: ['venues'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
      if (!venue) navigate(`/owner/venues/${v.id}`, { replace: true })
    },
  })
  const err = save.error instanceof ApiError ? save.error.fields : {}

  const remove = useMutation({
    mutationFn: () => api(`/owner/venues/${venue!.id}/`, { method: 'DELETE' }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['owner'] }); navigate('/owner') },
  })

  const input = (k: keyof Form, props: React.InputHTMLAttributes<HTMLInputElement> = {}) => (
    <>
      <input id={`v-${k}`} className="input" value={(form[k] as string | number | null) ?? ''} onChange={(e) => setForm({ ...form, [k]: e.target.value })} {...props} />
      <FieldError msg={err[k]} />
    </>
  )

  function useMyLocation() {
    navigator.geolocation?.getCurrentPosition((p) =>
      setForm((f) => ({ ...f, latitude: p.coords.latitude.toFixed(6), longitude: p.coords.longitude.toFixed(6) })))
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    save.mutate()
  }

  return (
    <form onSubmit={submit} className="card mt-6 space-y-6 p-6">
      <h2 className="text-xl font-bold">Details</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2"><label className="label" htmlFor="v-name">Venue name</label>{input('name', { required: true, maxLength: 120 })}</div>
        <div className="sm:col-span-2"><label className="label" htmlFor="v-tagline">Tagline <span className="font-normal text-ink-500">— one line guests see first</span></label>{input('tagline', { maxLength: 160, placeholder: 'e.g. Garden weddings with a view over the city' })}</div>
        <div className="sm:col-span-2">
          <label className="label" htmlFor="v-desc">Description</label>
          <textarea id="v-desc" className="input" rows={5} required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <FieldError msg={err.description} />
        </div>
        <div><label className="label" htmlFor="v-city">City</label>{input('city', { required: true })}</div>
        <div><label className="label" htmlFor="v-area">Area / sub-city</label>{input('area', { placeholder: 'e.g. Bole' })}</div>
        <div className="sm:col-span-2"><label className="label" htmlFor="v-address">Address</label>{input('address')}</div>
        <div><label className="label" htmlFor="v-latitude">Latitude</label>{input('latitude', { inputMode: 'decimal', placeholder: '9.0108' })}</div>
        <div>
          <label className="label" htmlFor="v-longitude">Longitude</label>{input('longitude', { inputMode: 'decimal', placeholder: '38.7613' })}
          <button type="button" onClick={useMyLocation} className="mt-1 text-xs font-semibold text-brand-600 hover:underline">Use my current location</button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div><label className="label" htmlFor="v-capacity_min">Min guests</label>{input('capacity_min', { type: 'number', min: 1, required: true })}</div>
        <div><label className="label" htmlFor="v-capacity_max">Max guests</label>{input('capacity_max', { type: 'number', min: 1, required: true })}</div>
        <div><label className="label" htmlFor="v-price_per_day">Price per day (ETB)</label>{input('price_per_day', { type: 'number', min: 0, step: 100, required: true })}</div>
      </div>

      <div><p className="label">Suitable for</p><Chips options={eventTypes} value={form.event_types} onChange={(event_types) => setForm({ ...form, event_types })} /></div>
      <div><p className="label">Amenities</p><Chips options={amenities} value={form.amenities} onChange={(a) => setForm({ ...form, amenities: a })} /></div>
      <div>
        <label className="label" htmlFor="v-policies">Rental policies</label>
        <textarea id="v-policies" className="input" rows={3} placeholder="Deposit, cancellation, music curfew, decoration rules…" value={form.rental_policies} onChange={(e) => setForm({ ...form, rental_policies: e.target.value })} />
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="size-4 accent-brand-600" checked={form.is_published} onChange={(e) => setForm({ ...form, is_published: e.target.checked })} />
        Published — visible to guests in search
      </label>

      {save.error && !Object.keys(err).some((k) => k in EMPTY) && <Alert>{save.error.message}</Alert>}
      {saved && <Alert tone="success">Saved.</Alert>}

      <div className="flex flex-wrap items-center gap-2">
        <button className="btn-primary" disabled={save.isPending}>{save.isPending ? 'Saving…' : venue ? 'Save changes' : 'Create venue & add photos'}</button>
        {venue && (
          <button type="button" className="btn-danger ml-auto" disabled={remove.isPending}
            onClick={() => confirm(`Delete ${venue.name}? Its bookings and reviews are deleted too. This can't be undone.`) && remove.mutate()}>
            <Trash2 className="size-4" /> Delete venue
          </button>
        )}
      </div>
    </form>
  )
}

function Photos({ venue }: { venue: OwnerVenue }) {
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['owner'] })

  const upload = useMutation({
    mutationFn: (files: FileList) => {
      const fd = new FormData()
      fd.append('venue', String(venue.id))
      Array.from(files).forEach((f) => fd.append('images', f))
      return api('/owner/photos/', { body: fd })
    },
    onSuccess: refresh,
  })
  const remove = useMutation({ mutationFn: (id: number) => api(`/owner/photos/${id}/`, { method: 'DELETE' }), onSuccess: refresh })
  const makeCover = useMutation({
    mutationFn: async (id: number) => {
      // Move the chosen photo to order 0 and shift the rest after it.
      const ordered = [venue.photos.find((p) => p.id === id)!, ...venue.photos.filter((p) => p.id !== id)]
      const fd = (i: number) => { const f = new FormData(); f.append('order', String(i)); return f }
      await Promise.all(ordered.map((p, i) => api(`/owner/photos/${p.id}/`, { method: 'PATCH', body: fd(i) })))
    },
    onSuccess: refresh,
  })

  return (
    <section className="card mt-6 p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold">Photos</h2>
          <p className="text-sm text-ink-500">Upload as many as you like — large photos are resized automatically. The first photo is the cover.</p>
        </div>
        <button type="button" className="btn-secondary shrink-0" onClick={() => fileRef.current?.click()} disabled={upload.isPending}>
          {upload.isPending ? <Loader2 className="size-4 animate-spin" /> : <ImagePlus className="size-4" />} Add photos
        </button>
        <input ref={fileRef} type="file" accept="image/*" multiple hidden onChange={(e) => e.target.files?.length && upload.mutate(e.target.files)} />
      </div>
      {upload.error && <div className="mt-3"><Alert>{upload.error.message}</Alert></div>}
      {venue.photos.length === 0 ? (
        <button type="button" onClick={() => fileRef.current?.click()} className="mt-4 grid h-40 w-full place-items-center rounded-2xl border-2 border-dashed border-ink-300 text-sm text-ink-500 hover:border-brand-500">
          Click to upload photos
        </button>
      ) : (
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {venue.photos.map((p, i) => (
            <div key={p.id} className="group relative overflow-hidden rounded-xl">
              <img src={p.image} alt="" className="aspect-[4/3] w-full object-cover" />
              {i === 0 && <span className="absolute left-2 top-2 rounded-full bg-white/95 px-2 py-0.5 text-xs font-semibold">Cover</span>}
              <div className="absolute inset-x-0 bottom-0 flex justify-between gap-1 bg-gradient-to-t from-black/60 p-2 opacity-0 transition group-hover:opacity-100 focus-within:opacity-100">
                {i > 0 ? <button type="button" className="rounded-lg bg-white/90 px-2 py-1 text-xs font-medium" onClick={() => makeCover.mutate(p.id)}>Make cover</button> : <span />}
                <button type="button" className="rounded-lg bg-white/90 p-1 text-red-700" aria-label="Delete photo" onClick={() => remove.mutate(p.id)}><Trash2 className="size-4" /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

function BlockedDates({ venue }: { venue: OwnerVenue }) {
  const queryClient = useQueryClient()
  const { data: blocked } = useQuery({
    queryKey: ['owner', 'blocked', venue.id],
    queryFn: () => api<BlockedDate[]>('/owner/blocked-dates/', { query: { venue: venue.id } }),
  })
  const { data: avail } = useQuery({
    queryKey: ['owner', 'availability', venue.slug],
    queryFn: () => api<{ unavailable: string[] }>(`/venues/${venue.slug}/availability/`, { query: { start: isoDate(new Date()), end: isoDate(addDays(new Date(), 365)) } }),
    enabled: venue.is_published,
  })
  const blockedSet = useMemo(() => new Set(blocked?.map((b) => b.date) ?? []), [blocked])
  const unavailable = useMemo(() => new Set([...(avail?.unavailable ?? []), ...blockedSet]), [avail, blockedSet])

  const toggle = useMutation({
    mutationFn: (date: string) => {
      const existing = blocked?.find((b) => b.date === date)
      return existing
        ? api(`/owner/blocked-dates/${existing.id}/`, { method: 'DELETE' })
        : api('/owner/blocked-dates/', { body: { venue: venue.id, date } })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['owner'] }),
  })

  const upcoming = blocked?.filter((b) => b.date >= isoDate(new Date())) ?? []

  return (
    <section className="card mt-6 grid gap-6 p-6 md:grid-cols-[320px_1fr]">
      <div>
        <h2 className="text-xl font-bold">Availability</h2>
        <p className="mb-4 text-sm text-ink-500">Click a day to block or unblock it. Booked days can't be blocked.</p>
        <AvailabilityCalendar mode="manage" unavailable={unavailable} blocked={blockedSet} onSelect={(d) => toggle.mutate(d)} />
        {toggle.error && <div className="mt-3"><Alert>{toggle.error.message}</Alert></div>}
      </div>
      <div>
        <p className="label">Blocked dates</p>
        {upcoming.length ? (
          <ul className="divide-y divide-ink-100 text-sm">
            {upcoming.map((b) => (
              <li key={b.id} className="flex items-center justify-between py-2">
                {prettyDate(b.date)}
                <button type="button" className="text-xs font-semibold text-brand-600 hover:underline" onClick={() => toggle.mutate(b.date)}>Unblock</button>
              </li>
            ))}
          </ul>
        ) : <p className="text-sm text-ink-500">None — every free day is open for requests.</p>}
      </div>
    </section>
  )
}
