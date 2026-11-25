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

### Demo data from Gebeta Maps (Addis Ababa, free)

`python manage.py import_gebeta_places` imports Addis Ababa halls, hotels, resorts, gardens and conference centres from [Gebeta Maps](https://gebeta.app), an Ethiopian map provider. The free Developer plan includes 1,500 search calls, and sign-up needs no payment card.

1. Register at https://gebeta.app (choose **Individual**), then create an API key in the dashboard.
2. Put it in `.env` as `GEBETA_API_KEY=...`.
3. Run `python manage.py import_gebeta_places --dry-run` to preview, then without `--dry-run` to save.

One run makes about 90 calls: 10 searches across a 3×3 grid of Addis. Use `--grid 2` for about 40. Gebeta returns names, locations and neighbourhoods but no photos, so these venues show a placeholder image, and their price and capacity are labelled as estimates. A venue that's already listed with the same name within 300 m, for example from Google, is skipped.

### Demo data from Google Places (Addis Ababa)

`python manage.py import_google_places` imports real event venues in Addis Ababa (wedding halls, banquet halls, hotel ballrooms, conference halls, gardens) from the **Google Places API (New)**, for demo and testing.

1. In Google Cloud Console, create a project, enable **Places API (New)**, create an API key, and restrict it to that API.
2. Put it in `.env` as `GOOGLE_MAPS_API_KEY=...`.
3. Run `python manage.py import_google_places --dry-run` to preview, then without `--dry-run` to save. Use `--refresh` later to re-sync.

How it follows Google's terms: only the place ID is kept long-term. Name, address and location are re-synced with `--refresh`. Photos are **never stored**: the API fetches a short-lived photo URL from Google on each view and the UI shows the photographer credit and "Google Maps". Price and capacity aren't in Google's data, so imported venues get placeholder values labelled as estimates. These clear as soon as an owner edits them.

Each search page is a billable request (about 14 to 21 per full import), and every photo view calls the API too. Google has a free monthly allowance; check current pricing before running it often.

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
