import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { CalendarDays, CheckCircle2, MapPin, Search, ShieldCheck, Sparkles, Users } from 'lucide-react'
import { api } from '../lib/api'
import type { Named, Paginated, VenueSummary } from '../lib/types'
import { VenueCard } from '../components/VenueCard'

const OCCASIONS = [
  { slug: 'wedding', label: 'Weddings', emoji: '💍' },
  { slug: 'birthday', label: 'Birthdays', emoji: '🎂' },
  { slug: 'corporate-meeting', label: 'Meetings', emoji: '💼' },
  { slug: 'conference', label: 'Conferences', emoji: '🎤' },
  { slug: 'graduation', label: 'Graduations', emoji: '🎓' },
  { slug: 'concert', label: 'Concerts', emoji: '🎶' },
]

export function Home() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ event_type: '', city: '', guests: '', available_on: '' })

  const { data: eventTypes } = useQuery({ queryKey: ['event-types'], queryFn: () => api<Named[]>('/event-types/') })
  const { data: cities } = useQuery({ queryKey: ['cities'], queryFn: () => api<{ city: string; venue_count: number }[]>('/cities/') })
  const { data: top } = useQuery({
    queryKey: ['venues', 'top'],
    queryFn: () => api<Paginated<VenueSummary>>('/venues/', { query: { ordering: '-rating_avg' } }),
  })

  function submit(e: FormEvent) {
    e.preventDefault()
    const sp = new URLSearchParams(Object.entries(form).filter(([, v]) => v))
    navigate(`/venues?${sp}`)
  }

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-ink-900 text-white">
        <div
          aria-hidden
          className="absolute inset-0 opacity-30"
          style={{ backgroundImage: 'radial-gradient(circle at 20% 20%, #d0623d 0, transparent 45%), radial-gradient(circle at 85% 60%, #e09c1f 0, transparent 40%)' }}
        />
        <div className="container-page relative py-20 sm:py-28">
          <p className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm">
            <Sparkles className="size-4 text-saffron-400" /> የት ይደገስ? — Where shall we celebrate?
          </p>
          <h1 className="max-w-3xl text-4xl font-bold leading-tight sm:text-6xl">
            The right venue for every <span className="text-saffron-400">celebration</span>.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-ink-300">
            Compare halls, gardens and meeting rooms across Ethiopia, check real availability, and send a booking request in minutes.
          </p>

          <form onSubmit={submit} className="mt-10 grid gap-2 rounded-2xl bg-white p-2 text-ink-900 shadow-xl sm:grid-cols-2 lg:grid-cols-[1fr_1fr_0.8fr_1fr_auto]">
            <label className="flex items-center gap-2 rounded-xl px-3 py-2 hover:bg-ink-50">
              <Sparkles className="size-4 shrink-0 text-ink-500" />
              <select className="w-full bg-transparent text-sm focus:outline-none" value={form.event_type} onChange={(e) => setForm({ ...form, event_type: e.target.value })} aria-label="Occasion">
                <option value="">Any occasion</option>
                {eventTypes?.map((t) => <option key={t.slug} value={t.slug}>{t.name}</option>)}
              </select>
            </label>
            <label className="flex items-center gap-2 rounded-xl px-3 py-2 hover:bg-ink-50">
              <MapPin className="size-4 shrink-0 text-ink-500" />
              <select className="w-full bg-transparent text-sm focus:outline-none" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} aria-label="City">
                <option value="">Anywhere</option>
                {cities?.map((c) => <option key={c.city} value={c.city}>{c.city}</option>)}
              </select>
            </label>
            <label className="flex items-center gap-2 rounded-xl px-3 py-2 hover:bg-ink-50">
              <Users className="size-4 shrink-0 text-ink-500" />
              <input type="number" min={1} placeholder="Guests" className="w-full bg-transparent text-sm focus:outline-none" value={form.guests} onChange={(e) => setForm({ ...form, guests: e.target.value })} aria-label="Guests" />
            </label>
            <label className="flex items-center gap-2 rounded-xl px-3 py-2 hover:bg-ink-50">
              <CalendarDays className="size-4 shrink-0 text-ink-500" />
              <input type="date" className="w-full bg-transparent text-sm focus:outline-none" value={form.available_on} onChange={(e) => setForm({ ...form, available_on: e.target.value })} aria-label="Date" />
            </label>
            <button className="btn-primary py-3 sm:col-span-2 lg:col-span-1"><Search className="size-4" /> Search</button>
          </form>
        </div>
      </section>

      {/* Occasions */}
      <section className="container-page py-14">
        <h2 className="text-2xl font-bold sm:text-3xl">Browse by occasion</h2>
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {OCCASIONS.map((o) => (
            <Link key={o.slug} to={`/venues?event_type=${o.slug}`} className="card flex flex-col items-center gap-2 px-4 py-6 transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-md">
              <span className="text-3xl" aria-hidden>{o.emoji}</span>
              <span className="text-sm font-semibold">{o.label}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Top rated */}
      {top && top.results.length > 0 && (
        <section className="container-page">
          <div className="flex items-end justify-between">
            <h2 className="text-2xl font-bold sm:text-3xl">Guest favourites</h2>
            <Link to="/venues" className="text-sm font-semibold text-brand-600 hover:underline">See all venues →</Link>
          </div>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {top.results.slice(0, 4).map((v) => <VenueCard key={v.id} venue={v} />)}
          </div>
        </section>
      )}

      {/* How it works */}
      <section className="container-page py-16">
        <div className="grid gap-6 md:grid-cols-3">
          {[
            { icon: Search, title: 'Find', text: 'Filter by occasion, guest count, budget and the exact date you need.' },
            { icon: CalendarDays, title: 'Request', text: 'See live availability and send a request. Owners usually reply within a day.' },
            { icon: ShieldCheck, title: 'Celebrate', text: 'Once confirmed, the date is yours — no double bookings, ever.' },
          ].map(({ icon: Icon, title, text }, i) => (
            <div key={title} className="card p-6">
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-xl bg-brand-50 text-brand-600"><Icon className="size-5" /></span>
                <span className="text-sm font-semibold text-ink-500">Step {i + 1}</span>
              </div>
              <h3 className="mt-4 text-xl font-bold">{title}</h3>
              <p className="mt-1 text-sm text-ink-500">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Host CTA */}
      <section className="container-page">
        <div className="grid items-center gap-8 overflow-hidden rounded-3xl bg-brand-600 p-8 text-white sm:p-12 md:grid-cols-2">
          <div>
            <h2 className="text-3xl font-bold">Own a venue?</h2>
            <p className="mt-3 text-brand-100">List it for free, manage requests from one dashboard and keep your calendar in sync.</p>
            <Link to="/host" className="btn mt-6 bg-white text-brand-700 hover:bg-brand-50">Start hosting</Link>
          </div>
          <ul className="space-y-3 text-brand-50">
            {['Accept or decline requests in one click', 'Block dates for private use or maintenance', 'Photos optimised automatically for fast loading', 'Reply publicly to guest reviews'].map((t) => (
              <li key={t} className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 size-5 shrink-0 text-saffron-400" /> {t}</li>
            ))}
          </ul>
        </div>
      </section>
    </>
  )
}
