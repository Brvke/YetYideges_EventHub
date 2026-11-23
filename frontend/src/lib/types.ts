export type Role = 'guest' | 'owner'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone: string
  role: Role
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface Named { slug: string; name: string }

export interface VenueSummary {
  id: number
  slug: string
  name: string
  tagline: string
  city: string
  area: string
  capacity_min: number
  capacity_max: number
  price_per_day: string
  rating_avg: string
  rating_count: number
  latitude: string | null
  longitude: string | null
  cover_photo: string | null
  event_types: Named[]
}

export interface Photo {
  id: number
  image: string
  caption: string
  order: number
  width: number
  height: number
}

export interface VenueDetail extends VenueSummary {
  description: string
  address: string
  rental_policies: string
  amenities: Named[]
  photos: Photo[]
  owner_name: string
}

/** Shape the owner edits; relations are slug lists. */
export interface OwnerVenue {
  id: number
  slug: string
  name: string
  tagline: string
  description: string
  city: string
  area: string
  address: string
  latitude: string | null
  longitude: string | null
  capacity_min: number
  capacity_max: number
  price_per_day: string
  event_types: string[]
  amenities: string[]
  rental_policies: string
  is_published: boolean
  rating_avg: string
  rating_count: number
  photos: Photo[]
  created_at: string
}

export type BookingStatus = 'pending' | 'accepted' | 'declined' | 'cancelled'

export interface Booking {
  id: number
  venue: { id: number; slug: string; name: string; city: string; area: string; cover_photo: string | null }
  guest: { name: string; email: string; phone: string }
  event_date: string
  guest_count: number
  event_type: string | null
  message: string
  status: BookingStatus
  owner_note: string
  quoted_price: string
  created_at: string
  responded_at: string | null
  can_review: boolean
  review_id: number | null
}

export interface Review {
  id: number
  booking: number
  venue: string
  author_name: string
  rating: number
  comment: string
  owner_reply: string
  event_date: string
  created_at: string
}

export interface OwnerStats {
  venues: number
  published_venues: number
  pending_requests: number
  upcoming_events: number
  revenue_this_year: string | number
  average_rating: number
  review_count: number
  acceptance_rate: number | null
}

export interface BlockedDate { id: number; venue: number; date: string; reason: string }
