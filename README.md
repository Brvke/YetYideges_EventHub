# YetYideges EventHub

**የት ይደገስ? — "Where shall we celebrate?"**
Find, book and review event venues across Ethiopia: wedding gardens, ballrooms, meeting rooms and more.

| | |
|---|---|
| **Guests** | Search by occasion, city, guest count, budget, amenities and an exact date · see live availability · send booking requests · cancel · review venues after the event |
| **Venue owners** | List venues with photos and a map pin · accept / decline requests · block dates · reply to reviews · dashboard with pending requests, upcoming events, revenue, rating and acceptance rate |

## Stack

- **Backend:** Django 5 + Django REST Framework, PostgreSQL, JWT auth (`backend/`)
- **Frontend:** React 19 + TypeScript (Vite), TanStack Query, Tailwind CSS v4, Leaflet/OpenStreetMap (`frontend/`)
- **API docs:** Swagger UI at `/api/docs/`

### Design decisions

- **No double-booking, guaranteed by the database.** A partial unique index allows only one *accepted* booking per venue per day. Accepting a request locks competing requests and declines them automatically.
- **Reviews are verified.** Only a guest whose booking was accepted, and whose event date has passed, can review, once per booking. Venue rating averages are stored on the venue and kept up to date by a signal, so list pages stay fast.
- **Full-text search** with Postgres (stemmed, so "weddings" finds "wedding"), with a substring fallback for partial words, and a GIN index.
- **Photos are optimised on upload.** Images are auto-rotated, resized to 1920 px and stored as WebP, so a 20 MB phone photo becomes about 300 KB.
- **Quoted price is frozen** on each booking, so later price changes don't affect existing requests.

## Run it locally

Prerequisites: Python 3.12+, Node 20+, PostgreSQL 15+.

```bash
# 1. config
cp .env.example .env        # then fill in DATABASE_URL, DJANGO_SECRET_KEY, DEMO_PASSWORD
createdb eventhub           # or: psql -U postgres -c "CREATE DATABASE eventhub"

# 2. backend  →  http://localhost:8000/api/docs/
cd backend
python -m venv .venv
.venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo  # demo venues + accounts (see below)
python manage.py runserver

# 3. frontend  →  http://localhost:5173
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/media` to Django, so no CORS setup is needed in development.

**Demo accounts** (created by `seed_demo`, password = `DEMO_PASSWORD` from your `.env`):
`owner@demo.yetyideges.test` (venue owner) and `guest@demo.yetyideges.test` (guest).

Admin: `python manage.py createsuperuser`, then go to http://localhost:8000/admin/.

## Tests

```bash
cd backend && python manage.py test apps
```

## API overview

| Endpoint | |
|---|---|
| `POST /api/auth/register/` · `POST /api/auth/token/` · `GET/PATCH /api/auth/me/` | Accounts (JWT) |
| `GET /api/venues/?q=&city=&event_type=&guests=&max_price=&available_on=&amenities=&min_rating=&ordering=` | Search |
| `GET /api/venues/{slug}/` · `/availability/` · `/reviews/` | Venue page |
| `GET/POST /api/bookings/` · `POST /api/bookings/{id}/cancel/` | Guest bookings |
| `POST /api/reviews/` | Review a past booking |
| `/api/owner/venues/` · `/owner/photos/` · `/owner/blocked-dates/` | Manage listings |
| `/api/owner/bookings/` · `POST …/{id}/accept/` · `…/decline/` | Manage requests |
| `GET /api/owner/stats/` · `POST /api/owner/reviews/{id}/reply/` | Dashboard |

## Project layout

```
backend/
  config/            settings, urls
  apps/accounts/     email-login User with guest/owner role
  apps/venues/       Venue, VenuePhoto, EventType, Amenity, BlockedDate, search filters, seed_demo
  apps/bookings/     Booking + state transitions (accept / decline / cancel), owner stats
  apps/reviews/      Review + rating aggregation signal
frontend/src/
  lib/               API client (JWT refresh), auth context, types, formatting
  components/        Layout, VenueCard, VenueMap, AvailabilityCalendar, UI bits
  pages/             Home, Venues, VenueDetail, Auth, MyBookings, owner/Dashboard, owner/VenueEditor
```

## Roadmap ideas

- Online deposits (Chapa / Telebirr)
- Email and SMS notifications when a request is accepted
- Amharic translation
- Deploy: Render/Railway for Django + Postgres, Vercel/Netlify for the frontend
