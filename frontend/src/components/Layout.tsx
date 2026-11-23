import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { CalendarCheck, LayoutDashboard, LogOut, Menu, X } from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../lib/auth'

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <Link to="/" className="flex items-center gap-2">
      <span className="grid size-8 place-items-center rounded-lg bg-brand-600 font-display text-lg font-bold text-white">Y</span>
      <span className={clsx('font-display text-xl font-bold', light ? 'text-white' : 'text-ink-900')}>
        Yet<span className="text-brand-600">Yideges</span>
      </span>
    </Link>
  )
}

const navCls = ({ isActive }: { isActive: boolean }) =>
  clsx('rounded-lg px-3 py-2 text-sm font-medium transition', isActive ? 'bg-brand-50 text-brand-700' : 'text-ink-700 hover:bg-ink-100')

export function Layout() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  const links = (
    <>
      <NavLink to="/venues" className={navCls} onClick={() => setOpen(false)}>Explore venues</NavLink>
      {user && (
        <NavLink to="/bookings" className={navCls} onClick={() => setOpen(false)}>
          <span className="inline-flex items-center gap-1.5"><CalendarCheck className="size-4" />My bookings</span>
        </NavLink>
      )}
      {user?.role === 'owner' ? (
        <NavLink to="/owner" className={navCls} onClick={() => setOpen(false)}>
          <span className="inline-flex items-center gap-1.5"><LayoutDashboard className="size-4" />Host dashboard</span>
        </NavLink>
      ) : (
        <NavLink to="/host" className={navCls} onClick={() => setOpen(false)}>List your venue</NavLink>
      )}
    </>
  )

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-ink-100 bg-white/90 backdrop-blur">
        <div className="container-page flex h-16 items-center justify-between gap-4">
          <Logo />
          <nav className="hidden items-center gap-1 md:flex">{links}</nav>
          <div className="hidden items-center gap-2 md:flex">
            {user ? (
              <>
                <span className="text-sm text-ink-500">Hi, {user.first_name || user.email}</span>
                <button className="btn-ghost" onClick={() => { logout(); navigate('/') }} aria-label="Log out">
                  <LogOut className="size-4" />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn-ghost">Log in</Link>
                <Link to="/register" className="btn-primary">Sign up</Link>
              </>
            )}
          </div>
          <button className="btn-ghost md:hidden" onClick={() => setOpen(!open)} aria-label="Menu">
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
        {open && (
          <div className="container-page flex flex-col gap-1 border-t border-ink-100 py-3 md:hidden">
            {links}
            {user ? (
              <button className="btn-secondary mt-2" onClick={() => { logout(); setOpen(false); navigate('/') }}>Log out</button>
            ) : (
              <div className="mt-2 grid grid-cols-2 gap-2">
                <Link to="/login" className="btn-secondary" onClick={() => setOpen(false)}>Log in</Link>
                <Link to="/register" className="btn-primary" onClick={() => setOpen(false)}>Sign up</Link>
              </div>
            )}
          </div>
        )}
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="mt-16 bg-ink-900 text-ink-300">
        <div className="container-page grid gap-8 py-12 sm:grid-cols-3">
          <div>
            <Logo light />
            <p className="mt-3 max-w-xs text-sm">“Yet Yideges?” — where shall we celebrate? Find the right place for every occasion across Ethiopia.</p>
          </div>
          <div className="text-sm">
            <p className="mb-2 font-semibold text-white">Explore</p>
            <ul className="space-y-1.5">
              <li><Link to="/venues?event_type=wedding" className="hover:text-white">Wedding venues</Link></li>
              <li><Link to="/venues?event_type=corporate-meeting" className="hover:text-white">Meeting rooms</Link></li>
              <li><Link to="/venues?event_type=birthday" className="hover:text-white">Party venues</Link></li>
            </ul>
          </div>
          <div className="text-sm">
            <p className="mb-2 font-semibold text-white">Hosts</p>
            <ul className="space-y-1.5">
              <li><Link to="/host" className="hover:text-white">List your venue</Link></li>
              <li><Link to="/owner" className="hover:text-white">Host dashboard</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-white/10 py-4 text-center text-xs">© {new Date().getFullYear()} YetYideges EventHub</div>
      </footer>
    </div>
  )
}
