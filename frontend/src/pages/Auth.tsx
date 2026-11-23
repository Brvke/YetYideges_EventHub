import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Building2, PartyPopper } from 'lucide-react'
import clsx from 'clsx'
import { ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'
import type { Role } from '../lib/types'
import { Alert, FieldError } from '../components/ui'
import { Logo } from '../components/Layout'

function Shell({ title, subtitle, children }: { title: string; subtitle: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="container-page flex justify-center py-16">
      <div className="w-full max-w-md">
        <div className="mb-6 flex justify-center"><Logo /></div>
        <div className="card p-8">
          <h1 className="text-2xl font-bold">{title}</h1>
          <p className="mt-1 text-sm text-ink-500">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  )
}

export function Login() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={from ?? '/'} replace />

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const me = await login(email, password)
      navigate(from ?? (me.role === 'owner' ? '/owner' : '/venues'), { replace: true })
    } catch (err) {
      setError(err instanceof ApiError && err.status === 401 ? 'Email or password is incorrect.' : (err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell title="Welcome back" subtitle={<>New here? <Link to="/register" state={{ from }} className="font-semibold text-brand-600">Create an account</Link></>}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label" htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="email" required className="input" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="current-password" required className="input" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        {error && <Alert>{error}</Alert>}
        <button className="btn-primary w-full py-3" disabled={busy}>{busy ? 'Signing in…' : 'Log in'}</button>
      </form>
    </Shell>
  )
}

export function Register({ defaultRole = 'guest' }: { defaultRole?: Role }) {
  const { register, user } = useAuth()
  const navigate = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', password: '', role: defaultRole })
  const [error, setError] = useState<ApiError | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={from ?? '/'} replace />
  const f = (k: keyof typeof form) => ({ value: form[k], onChange: (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value }) })

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const me = await register(form)
      navigate(from ?? (me.role === 'owner' ? '/owner/venues/new' : '/venues'), { replace: true })
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell title="Create your account" subtitle={<>Already have one? <Link to="/login" state={{ from }} className="font-semibold text-brand-600">Log in</Link></>}>
      <form onSubmit={submit} className="space-y-4">
        <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Account type">
          {([['guest', PartyPopper, 'I’m planning an event'], ['owner', Building2, 'I have a venue']] as const).map(([role, Icon, label]) => (
            <button key={role} type="button" role="radio" aria-checked={form.role === role} onClick={() => setForm({ ...form, role })}
              className={clsx('flex flex-col items-center gap-1 rounded-xl border p-3 text-sm', form.role === role ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-ink-300')}>
              <Icon className="size-5" /> {label}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label" htmlFor="fn">First name</label>
            <input id="fn" required className="input" autoComplete="given-name" {...f('first_name')} />
          </div>
          <div>
            <label className="label" htmlFor="ln">Last name</label>
            <input id="ln" className="input" autoComplete="family-name" {...f('last_name')} />
          </div>
        </div>
        <div>
          <label className="label" htmlFor="r-email">Email</label>
          <input id="r-email" type="email" required className="input" autoComplete="email" {...f('email')} />
          <FieldError msg={error?.fields.email} />
        </div>
        <div>
          <label className="label" htmlFor="phone">Phone <span className="font-normal text-ink-500">(shared with hosts when you book)</span></label>
          <input id="phone" type="tel" className="input" placeholder="+251 9…" autoComplete="tel" {...f('phone')} />
        </div>
        <div>
          <label className="label" htmlFor="r-pass">Password</label>
          <input id="r-pass" type="password" required minLength={8} className="input" autoComplete="new-password" {...f('password')} />
          <FieldError msg={error?.fields.password ?? error?.fields.non_field_errors} />
        </div>
        {error && !error.fields.email && !error.fields.password && !error.fields.non_field_errors && <Alert>{error.message}</Alert>}
        <button className="btn-primary w-full py-3" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button>
      </form>
    </Shell>
  )
}

/** "List your venue" entry point: sign up as owner, or upgrade an existing guest account. */
export function BecomeHost() {
  const { user, updateMe } = useAuth()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)

  if (!user) return <Register defaultRole="owner" />
  if (user.role === 'owner') return <Navigate to="/owner" replace />

  return (
    <Shell title="Become a host" subtitle="List your venue and start receiving booking requests.">
      <p className="text-sm text-ink-700">We'll switch <strong>{user.email}</strong> to a host account. You can still book other venues as a guest.</p>
      <button className="btn-primary mt-6 w-full py-3" disabled={busy}
        onClick={async () => { setBusy(true); await updateMe({ role: 'owner' }); navigate('/owner/venues/new') }}>
        {busy ? 'Switching…' : 'Switch to host account'}
      </button>
    </Shell>
  )
}
