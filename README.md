# ScholarMatch — Scholarship Recommendation App

A mobile-first, Tinder-style app that matches high school students to
scholarships based on GPA, grade level, state, demographics, interests, and
intended major — and scores every match with an estimated chance of
winning, dollars-per-hour-of-effort, and expected value.

**Stack:** Python/Flask API · PostgreSQL · React (Vite) frontend · Docker Compose

---

## 0. Read this first: two important caveats

**1. The "chance of winning" and related numbers are estimates, not guarantees.**
There is no public dataset of "how many people applied to this exact
scholarship and who won" for most scholarships. `app/services/scoring.py`
builds an estimate from the award amount, the number of awards given, an
estimated applicant pool, and how well the student's profile matches the
eligibility criteria. It's a genuinely useful heuristic for *ranking* which
scholarships are worth a student's time, but the UI says so explicitly
("estimates, not guarantees") and you should keep that framing if you ship
this — don't present the percentage as a statistical fact.

**2. I can't personally run a job at 5am every day — you (or your hosting
platform) have to schedule it.** I'm a chat assistant with no persistent
process running in the background after this conversation ends, so there's
no way for me to "wake up" and scrape on a schedule myself. What I *can* do,
and have done, is build the actual scraper (`backend/scraper/`) and three
ready-to-use ways to make a real daily-5am job happen once you deploy this:
a GitHub Actions scheduled workflow (recommended, free, no server needed —
`deployment/github-actions-scraper.yml`), an always-on scheduler container
(`backend/scraper/scheduler.py`, wired into `docker-compose.yml`), or a
plain crontab line if you run your own server. See **Section 5** below.

---

## 1. Project structure

```
scholarship-app/
├── README.md                          <- you are here
├── docker-compose.yml                 <- one-command local stack (db + backend + scraper + frontend)
├── .env.example                       <- root-level secrets template for docker-compose
│
├── backend/                            FLASK API
│   ├── requirements.txt                 Python dependencies
│   ├── .env.example                     backend secrets template
│   ├── Dockerfile                       container build for the API
│   ├── config.py                        environment-based Flask config classes
│   ├── run.py                           dev entrypoint (`python run.py`)
│   ├── seed_data.py                     inserts sample scholarships for local testing
│   │
│   ├── app/
│   │   ├── __init__.py                  the app factory (create_app)
│   │   ├── extensions.py                shared db/migrate/jwt/cors instances
│   │   ├── models/
│   │   │   ├── user.py                  User table (login + matching-profile fields)
│   │   │   ├── scholarship.py           Scholarship table (listing + eligibility + effort data)
│   │   │   ├── interaction.py           records every swipe (like/pass/save)
│   │   │   └── __init__.py              re-exports the three models above
│   │   ├── routes/
│   │   │   ├── auth.py                  POST /api/auth/signup, /login, GET /me
│   │   │   ├── profile.py               GET/PUT /api/profile
│   │   │   ├── scholarships.py          GET /deck, GET /<id>, POST /<id>/swipe
│   │   │   ├── saved.py                 GET /api/saved, DELETE /api/saved/<id>
│   │   │   └── __init__.py              registers all blueprints on the app
│   │   ├── services/
│   │   │   ├── scoring.py               THE MATH: eligibility, match score, chance/EV/$-per-hr
│   │   │   ├── matching.py              queries candidates + calls scoring.py to build the deck
│   │   │   └── __init__.py
│   │   └── utils/
│   │       └── validators.py            small shared input-validation helpers
│   │
│   ├── scraper/                          THE "FIND NEW SCHOLARSHIPS DAILY" SYSTEM
│   │   ├── run_scraper.py                orchestrator: runs every source, upserts into Postgres
│   │   ├── scheduler.py                  optional always-on process that triggers run_scraper at 5am
│   │   └── sources/
│   │       ├── base.py                   interface every data source implements
│   │       ├── example_api_source.py     template for a real JSON-API scholarship provider
│   │       └── example_html_source.py    template for scraping an HTML listings page (disabled by default)
│   │
│   ├── migrations/                       Flask-Migrate/Alembic migration scripts (generated, see its README.md)
│   └── tests/
│       └── test_scoring.py               unit tests for the scoring math (no DB/Flask needed to run them)
│
├── frontend/                            REACT APP (Vite)
│   ├── package.json                     JS dependencies + npm scripts
│   ├── vite.config.js                   dev server config
│   ├── index.html                       HTML shell + mobile viewport meta tags
│   ├── .env.example                     frontend env template (API base URL)
│   ├── Dockerfile                       container build for the dev server
│   └── src/
│       ├── main.jsx                      React bootstrap / mount point
│       ├── App.jsx                       route table + auth guarding
│       ├── index.css                     ALL design tokens + component styles (mobile-first)
│       ├── api/
│       │   └── client.js                 single place every fetch() call goes through
│       ├── context/
│       │   └── AuthContext.jsx           shared logged-in-user state + login/signup/logout
│       ├── hooks/
│       │   └── useScholarships.js        loads the swipe deck, handles optimistic swipe removal
│       ├── components/
│       │   ├── SwipeCard.jsx             one draggable "ticket" card (pointer-event gestures)
│       │   ├── SwipeDeck.jsx             stacks/manages multiple SwipeCards
│       │   ├── ScholarshipMetrics.jsx    the chance/EV/$-per-hr "ticket stub" readout
│       │   └── BottomNav.jsx             mobile tab bar (Discover / Saved / Profile)
│       └── pages/
│           ├── Login.jsx                 combined login/signup screen
│           ├── ProfileSetup.jsx          GPA/grade/state/demographics/interests/major form
│           ├── Discover.jsx              hosts the swipe deck
│           ├── Saved.jsx                 list of saved scholarships
│           └── Detail.jsx                full detail view for one scholarship
│
└── deployment/
    └── github-actions-scraper.yml       scheduled workflow: runs the scraper daily without a server
```

---

## 2. What each *system* (not just file) does

### The data model
Three tables: `users` (login + the exact profile fields the matcher needs),
`scholarships` (listing details + eligibility rules + effort/applicant-pool
estimates), and `interactions` (every swipe, which doubles as "don't show
this card again" and "what's in my Saved list").

### The scoring engine (`app/services/scoring.py`)
For a given (student, scholarship) pair, computes:
- **eligible** — hard pass/fail against min GPA, grade level, state,
  demographics, major (interests are *not* a hard filter, just a ranking signal)
- **match_score** (0–1) — how well the student fits beyond the minimum bar
- **chance_of_winning** — heuristic %, blending an award-size-based base rate
  with `num_awards / estimated_applicant_pool`, adjusted by match quality,
  clamped to 0.1%–60% so it never claims certainty
- **dollars_per_hour** — `amount / estimated_hours_to_apply` (assumes you win)
- **expected_value** — `amount * chance_of_winning` (a luck-adjusted dollar figure)
- **expected_value_per_hour** — the single best "is this worth my time" number

### The swipe interface
`SwipeCard.jsx` uses native Pointer Events (works for touch and mouse) to
drag a card left/right, with a rotation + fly-off animation and a tap
fallback (round ✕ / ♥ buttons) for accessibility and non-touch input.
`SwipeDeck.jsx` stacks the next few cards behind it so the deck feels
continuous. Every swipe calls `POST /api/scholarships/<id>/swipe`, which is
also how "Saved" gets populated (a swipe action of `"save"`).

### The scraper (Section 5 has full detail)
A pluggable source system: each source (a real partner API, a scrapable
listings page, etc.) implements `fetch()` and returns normalized dicts.
`run_scraper.py` runs every registered source, upserts rows keyed on
`(source_name, external_id)` so re-running is always safe, and marks
previously-seen listings from a source as inactive if that source stops
reporting them (e.g. the deadline passed).

---

## 3. Local setup (Docker — recommended)

```bash
# from the scholarship-app/ root
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker compose up --build
```

This starts Postgres, the Flask API (port 5000), an always-on scraper
scheduler container, and the React dev server (port 5173).

The very first time, initialize the database schema and load sample data
(in a second terminal, while the stack is running):

```bash
docker compose exec backend flask db init
docker compose exec backend flask db migrate -m "initial schema"
docker compose exec backend flask db upgrade
docker compose exec backend python seed_data.py
```

Then open **http://localhost:5173** on your phone (same Wi-Fi) or in your
browser's mobile device emulator.

## 4. Local setup (without Docker)

```bash
# Postgres: have one running locally, then:
createdb scholarship_db

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL if needed
flask db init && flask db migrate -m "initial schema" && flask db upgrade
python seed_data.py
python run.py            # serves http://localhost:5000

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env
npm run dev               # serves http://localhost:5173
```

Run the backend tests with `cd backend && pytest`.

---

## 5. Making "every day at 5am, find new scholarships" actually happen

The scraper code (`backend/scraper/`) is built and tested logic, but
*something* has to invoke it once a day — pick one:

**Option A — GitHub Actions (recommended for most people).**
Move `deployment/github-actions-scraper.yml` to
`.github/workflows/scrape-scholarships.yml` in your repo, add your
production `DATABASE_URL` as a repo secret, and push. GitHub runs it daily
at 9:00 UTC (5am US Eastern during daylight time) at no cost, with no
server of yours needing to stay on. Full instructions are in the comments
at the top of that file.

**Option B — an always-on scheduler container.** `docker-compose.yml`
already includes a `scraper` service running `scraper/scheduler.py`
(APScheduler), which fires at 5:00 AM America/New_York every day as long
as that container keeps running. Good if you're deploying to something
like a small VM or a "background worker" service where you're already
paying for an always-on process anyway.

**Option C — a plain crontab**, if you run your own Linux server:
```
0 5 * * * cd /path/to/backend && /path/to/venv/bin/python -m scraper.run_scraper
```

**Whichever option you pick, you still need a real scholarship data
source.** `scraper/sources/example_api_source.py` and
`example_html_source.py` are working *templates*, not connected to a real
provider — I didn't have a specific scholarship database to integrate with,
since none was named. To get real new scholarships flowing in:
1. Sign up with an actual provider (e.g. evaluate Bold.org's partner API,
   a state higher-education-commission open-data feed, or a paid
   scholarship-data licensing service).
2. Fill in `SCHOLARSHIP_API_BASE_URL` / `SCHOLARSHIP_API_KEY` in
   `example_api_source.py`'s expected env vars, or write a new file in
   `scraper/sources/` following the `ScholarshipSource` interface in
   `base.py`.
3. Add your new source instance to the `SOURCES` list in `run_scraper.py`.
4. If scraping (not using an API) a real public listings page, check that
   site's `robots.txt` and Terms of Service first — many either disallow
   automated scraping or offer a partner data feed you should use instead.

Until a real source is wired in, `run_scraper.py` runs successfully every
day but finds 0 new scholarships (by design — it won't insert placeholder
data), so `seed_data.py`'s sample set is what powers the app out of the box.

---

## 6. Deploying to Railway (backend + database) and Vercel (frontend)

### 6a. Backend + Postgres on Railway

1. Create a new Railway project, add a **Postgres** plugin to it (Railway
   provisions `DATABASE_URL` automatically for that plugin).
2. Add a second service: **Deploy from GitHub repo**, then set its
   **Root Directory** to `backend`. Railway will detect `backend/Dockerfile`
   and `backend/railway.toml` and build from those.
3. On that service, set these environment variables:
   - `DATABASE_URL` — reference the Postgres plugin's variable
     (`${{Postgres.DATABASE_URL}}` in Railway's variable picker), don't
     retype it by hand.
   - `FLASK_ENV=production`
   - `SECRET_KEY` — a long random string, **not** the `dev-secret-key` default
   - `JWT_SECRET_KEY` — a different long random string
   - `CORS_ORIGINS` — your Vercel URL once you have it (step 6b), e.g.
     `https://scholarmatch.vercel.app` (comma-separate multiple origins)
   - Leave `PORT` unset — Railway injects it, and the Dockerfile's `gunicorn`
     binds to it automatically.
4. Deploy. The container runs `flask db upgrade` automatically before
   starting `gunicorn` (see `backend/Dockerfile`), so the schema is created
   on first deploy and kept current on every deploy after — no manual
   migration step needed on Railway. Confirm it's healthy by hitting
   `https://<your-railway-domain>/api/health`.
5. One-time only: seed data if you want the sample scholarships. Open a
   shell on the Railway service (Railway dashboard → service → "Shell") and
   run `python seed_data.py`, or run it locally against the Railway
   `DATABASE_URL` via `DATABASE_URL=<railway-url> python seed_data.py`.
6. Scraper: Railway doesn't run `docker-compose.yml`'s `scraper` service —
   use the GitHub Actions option instead (Section 5, Option A), pointing
   its `DATABASE_URL` secret at the same Railway Postgres instance.

### 6b. Frontend on Vercel

1. Import the repo into Vercel, set the project's **Root Directory** to
   `frontend`. Vercel auto-detects the Vite framework preset (build command
   `npm run build`, output directory `dist`).
2. Set one environment variable: `VITE_API_BASE_URL` = your Railway backend
   URL (e.g. `https://scholarmatch-backend.up.railway.app`, no trailing
   slash). Vite bakes this into the build, so redeploy after changing it.
3. `frontend/vercel.json` rewrites every path to `index.html` — required
   because this is a client-side-routed React Router app (`BrowserRouter`);
   without it, refreshing or deep-linking to `/saved` or `/scholarship/:id`
   would 404 on Vercel's static host.
4. Deploy. Once live, go back to Railway and set `CORS_ORIGINS` to this
   Vercel URL (step 6a.3) if you hadn't yet, then redeploy the backend.

### General notes

- **Database:** the Railway Postgres plugin (or any managed Postgres — RDS,
  Supabase, etc.) replaces the Docker Compose `db` service, which is dev-only.
- Rotate `SECRET_KEY` / `JWT_SECRET_KEY` to long random values before going
  live — never reuse the `dev-*` defaults in `config.py`.
- Vercel preview deploys (per-branch/PR URLs) get a different origin than
  production each time; add them to `CORS_ORIGINS` only if you need API
  access from previews, otherwise they'll just fail CORS harmlessly.
