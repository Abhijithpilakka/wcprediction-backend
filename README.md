# WC2026 Predictor — Backend

FastAPI + Supabase backend for the FIFA World Cup 2026 prediction platform.

---

## Stack

| Layer | Tech |
|---|---|
| Framework | FastAPI |
| Database | Supabase (PostgreSQL) |
| Auth | JWT (python-jose) |
| Hosting | Railway or Render |

---

## Project Structure

```
wc2026-backend/
├── app/
│   ├── main.py               ← FastAPI app + CORS + router registration
│   ├── core/
│   │   ├── config.py         ← Settings from .env
│   │   ├── supabase.py       ← Supabase client singleton
│   │   └── auth.py           ← JWT create/decode, auth dependencies
│   ├── routers/
│   │   ├── auth.py           ← POST /auth/login, GET /auth/me
│   │   ├── matches.py        ← GET /matches, /upcoming, /live, /completed
│   │   ├── predictions.py    ← POST /predictions, GET /predictions/my
│   │   ├── leaderboard.py    ← GET /leaderboard/overall, /weekly
│   │   └── admin.py          ← All /admin/* routes
│   ├── schemas/
│   │   └── schemas.py        ← Pydantic request/response models
│   └── services/
│       ├── points.py         ← Points calculation engine
│       └── leaderboard.py    ← Leaderboard recompute logic
├── tests/
│   └── test_points.py        ← Unit tests for points engine
├── supabase_schema.sql       ← Run this in Supabase SQL editor
├── requirements.txt
├── Procfile                  ← For Railway/Render
├── railway.toml
└── .env.example
```

---

## Setup

### 1. Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** → paste and run `supabase_schema.sql`
3. Copy from **Settings → API**:
   - Project URL → `SUPABASE_URL`
   - `anon` public key → `SUPABASE_ANON_KEY`
   - `service_role` secret key → `SUPABASE_SERVICE_ROLE_KEY`

### 2. Local Development

```bash
# Clone and install
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Fill in your Supabase keys and a random JWT_SECRET

# Run
uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

### 3. Create your admin account

After running the app, call `/auth/login` with your name + phone.
Then in Supabase table editor, find your user row and set `is_admin = true`.

---

## API Reference

### Auth
```
POST /auth/login       { name, phone }  → { token, user }
GET  /auth/me          [Bearer token]   → user object
```

### Matches
```
GET /matches           → all matches
GET /matches/upcoming  → upcoming only
GET /matches/live      → live only
GET /matches/completed → completed only
GET /matches/:id       → single match
```

### Predictions
```
POST /predictions      { match_id, predicted_team1_score, predicted_team2_score }
GET  /predictions/my   → all your predictions with match info
GET  /predictions/match/:id → your prediction for one match
```

### Leaderboard
```
GET /leaderboard/overall         → top 50 + your rank
GET /leaderboard/weekly?week=24  → weekly (defaults to current week)
```

### Admin (require is_admin = true)
```
POST   /admin/matches              add match
PATCH  /admin/matches/:id          edit match
DELETE /admin/matches/:id          delete match
POST   /admin/matches/:id/result   { team1_score, team2_score } → scores all predictions
POST   /admin/matches/:id/go-live  mark match live + lock predictions
GET    /admin/users                list all users
PATCH  /admin/users/ban            { user_id, banned: true/false }
PATCH  /admin/users/:id/make-admin promote user to admin
POST   /admin/recompute            trigger leaderboard recompute
POST   /admin/reset-weekly         reset weekly points (use each Monday)
```

---

## Points System

| Result | Points |
|---|---|
| Exact score | 6 |
| Correct winner + goal difference | 4 |
| Correct winner only | 3 |
| One team score correct | 1 |
| Wrong | 0 |

Multipliers: Group 1×, R16 1.2×, QF 1.5×, SF 1.8×, Final 2.5×

---

## Deployment — Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables (same as `.env`)
4. Railway auto-detects `railway.toml` and deploys

Your API will be live at `https://your-app.railway.app`

---

## Deployment — Render

1. New Web Service → connect GitHub repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables

---

## Tests

```bash
pytest tests/ -v
```

---

## Connecting to Frontend

In your Next.js frontend, replace the `API` object:

```js
const BASE = process.env.NEXT_PUBLIC_API_URL; // https://your-app.railway.app

const API = {
  login: async (name, phone) => {
    const r = await fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone }),
    });
    return r.json(); // { token, user }
  },
  getMatches: async () => {
    const r = await fetch(`${BASE}/matches/upcoming`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    });
    return r.json();
  },
  // ... etc
};
```
