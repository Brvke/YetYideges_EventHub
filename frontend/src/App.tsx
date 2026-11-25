import type { ReactNode } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './lib/auth'
import { Layout } from './components/Layout'
import { Empty, Spinner } from './components/ui'
import { Home } from './pages/Home'
import { Venues } from './pages/Venues'
import { VenueDetail } from './pages/VenueDetail'
import { BecomeHost, Login, Register } from './pages/Auth'
import { MyBookings } from './pages/MyBookings'
import { OwnerDashboard } from './pages/owner/Dashboard'
import { VenueEditor } from './pages/owner/VenueEditor'

function RequireAuth({ children, owner = false }: { children: ReactNode; owner?: boolean }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <Spinner />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (owner && user.role !== 'owner') return <Navigate to="/host" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="venues" element={<Venues />} />
        <Route path="venues/:slug" element={<VenueDetail />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="host" element={<BecomeHost />} />
        <Route path="bookings" element={<RequireAuth><MyBookings /></RequireAuth>} />
        <Route path="owner" element={<RequireAuth owner><OwnerDashboard /></RequireAuth>} />
        <Route path="owner/venues/new" element={<RequireAuth owner><VenueEditor /></RequireAuth>} />
        <Route path="owner/venues/:id" element={<RequireAuth owner><VenueEditor /></RequireAuth>} />
        <Route path="*" element={<div className="container-page py-16"><Empty title="Page not found" action={{ to: '/', label: 'Go home' }} /></div>} />
      </Route>
    </Routes>
  )
}
