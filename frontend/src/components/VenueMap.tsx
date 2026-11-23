import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import { moneyCompact } from '../lib/format'
import type { VenueSummary } from '../lib/types'

// Price-tag markers (like a booking site) instead of Leaflet's default pin images.
const priceIcon = (label: string, active: boolean) =>
  L.divIcon({
    className: '',
    html: `<div style="transform:translate(-50%,-50%);white-space:nowrap;padding:4px 8px;border-radius:999px;font:600 12px Inter,sans-serif;box-shadow:0 1px 4px rgba(0,0,0,.25);${
      active ? 'background:#b4462a;color:#fff' : 'background:#fff;color:#1f1a17'
    }">${label}</div>`,
  })

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap()
  useEffect(() => {
    if (points.length === 1) map.setView(points[0], 14)
    else if (points.length > 1) map.fitBounds(points, { padding: [40, 40], maxZoom: 14 })
  }, [map, points])
  return null
}

const ADDIS: [number, number] = [9.02, 38.75]

export function VenueMap({ venues, activeId, className }: { venues: VenueSummary[]; activeId?: number | null; className?: string }) {
  const located = venues.filter((v) => v.latitude && v.longitude)
  const points = located.map((v) => [Number(v.latitude), Number(v.longitude)] as [number, number])

  return (
    <MapContainer center={points[0] ?? ADDIS} zoom={12} scrollWheelZoom className={className}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds points={points} />
      {located.map((v, i) => (
        <Marker
          key={v.id}
          position={points[i]}
          icon={priceIcon(moneyCompact(v.price_per_day), v.id === activeId)}
          zIndexOffset={v.id === activeId ? 1000 : 0}
        >
          <Popup>
            <Link to={`/venues/${v.slug}`} className="font-semibold">{v.name}</Link>
            <div className="text-xs text-ink-500">{v.area}, {v.city}</div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
