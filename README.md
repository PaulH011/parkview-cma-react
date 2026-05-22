# Parkview Capital Market Assumptions Tool

A web application for generating 10-year expected returns across asset classes using the Research Affiliates methodology. Users can override any input assumption to create stress scenarios, save/load scenarios, and view detailed building-block breakdowns of each return forecast.

An admin panel enables quarterly AI-powered refreshes of market data assumptions using Claude with live web search.

> **For a complete methodology reference** — every formula, every default, every constant, every dependency, with worked examples that match the engine to 4 decimal places — see **[METHODOLOGY.md](METHODOLOGY.md)**. That document is detailed enough to reconstruct the entire tool as a spreadsheet without reading the source code.

## Architecture

```
┌─────────────────────┐       ┌──────────────────────┐       ┌────────────────┐
│   Next.js Frontend  │──────▶│   FastAPI Backend     │──────▶│   Supabase     │
│   (Vercel)          │  API  │   (Render)            │       │   (PostgreSQL) │
│                     │◀──────│                       │◀──────│                │
│  React 19 + Zustand │       │  ra_stress_tool engine│       │  Auth, Scenarios│
│  Shadcn/ui + Tailwind│      │  Anthropic Claude AI  │       │  Defaults, Logs│
└─────────────────────┘       └──────────────────────┘       └────────────────┘
```

| Layer | Tech | Hosted on |
|-------|------|-----------|
| Frontend | Next.js 16, React 19, Zustand, Shadcn/ui, Tailwind CSS, Recharts | Vercel |
| Backend API | FastAPI, Uvicorn, Pydantic | Render |
| Calculation Engine | Pure Python (`ra_stress_tool/`) | Runs inside the API |
| Database & Auth | Supabase (PostgreSQL + Auth + RLS) | Supabase Cloud |
| AI Research | Anthropic Claude Haiku 4.5 with web search | Called from backend |

## Features

- **10 asset classes**: Liquidity, Bonds Global, Bonds High Yield, Bonds EM, Bonds Inflation Linked, US/Europe/Japan/EM Equities, Absolute Return
- **Building-block methodology**: Each return is decomposed (yield + growth + valuation + currency, etc.)
- **Full override system**: Change any input assumption and see the impact in real time
- **Advanced mode**: Exposes additional parameters like valuation reversion speed (lambda)
- **Macro preview**: Real-time GDP/inflation/T-Bill forecasts as you adjust building blocks
- **Scenario management**: Save, load, and compare scenarios (Supabase when logged in, localStorage when not)
- **Risk-return chart**: Interactive scatter plot of expected return vs. volatility
- **Export**: Download results as CSV
- **Base currency toggle**: USD or EUR
- **Admin quarterly refresh**: AI-powered market data research with web search, batched to respect rate limits, run as a background job with real-time progress polling
- **Methodology page**: Full documentation of every formula and building block

## Project Structure

```
├── api/                        # FastAPI backend
│   ├── main.py                 # App entry point, CORS, router registration
│   ├── config.py               # Environment variables
│   ├── data_sources.json       # AI research metadata for each assumption
│   ├── models/                 # Pydantic request/response models
│   │   ├── requests.py
│   │   └── responses.py
│   ├── routes/
│   │   ├── calculate.py        # POST /api/calculate/full, /macro-preview
│   │   ├── defaults.py         # GET /api/defaults/all (Supabase + fallback)
│   │   └── admin.py            # AI research, apply/revert defaults, history
│   └── requirements.txt        # Local dev dependencies
│
├── ra_stress_tool/             # Core calculation engine (pure Python)
│   ├── main.py                 # CMEEngine class — orchestrates all models
│   ├── config.py               # Asset classes, EWMA params, credit params, defaults
│   ├── models/
│   │   ├── macro.py            # GDP, inflation, T-Bill forecasting
│   │   ├── bonds.py            # Gov bonds, HY, EM bond models
│   │   ├── equities.py         # Equity return model (dividend + growth + valuation)
│   │   ├── alternatives.py     # Hedge fund / absolute return model
│   │   └── currency.py         # FX impact calculations
│   ├── inputs/
│   │   ├── defaults.py         # Hardcoded default assumptions
│   │   └── overrides.py        # Override manager (merges user inputs with defaults)
│   ├── output.py               # Result formatting and comparison tables
│   ├── cli.py                  # Command-line interface
│   └── utils/ewma.py           # EWMA utility functions
│
├── web/                        # Next.js frontend
│   ├── app/
│   │   ├── page.tsx            # Main dashboard (inputs + results)
│   │   ├── methodology/        # Formula documentation page
│   │   └── admin/refresh/      # Admin quarterly refresh page
│   ├── components/
│   │   ├── inputs/             # Input panels (Macro, Equity, Bond, Alternatives)
│   │   ├── results/            # Results table, chart, breakdown, export
│   │   ├── scenarios/          # Scenario save/load manager
│   │   ├── auth/               # Auth button (Supabase)
│   │   ├── layout/             # Header
│   │   └── ui/                 # Shadcn/ui primitives
│   ├── hooks/                  # useCalculation, useMacroPreview
│   ├── stores/                 # Zustand stores (inputs, auth)
│   ├── lib/
│   │   ├── api.ts              # Backend API client
│   │   ├── scenarios.ts        # Supabase + localStorage scenario persistence
│   │   ├── supabase.ts         # Supabase client setup
│   │   ├── constants.ts        # Default input values
│   │   ├── formulas.ts         # Formula display definitions
│   │   ├── types.ts            # TypeScript interfaces
│   │   └── utils.ts            # Tailwind merge utility
│   └── public/                 # Static assets (logos)
│
├── migrations/                 # Supabase SQL migrations
│   ├── 001_react_scenarios.sql # Scenarios table + RLS policies
│   └── 002_default_assumptions.sql  # Defaults + refresh log tables
│
├── requirements-api.txt        # Python deps for Render deployment
├── .env.example                # Environment variable template
└── .gitignore
```

## Asset Class Models

| Asset Class | Formula | Key Inputs |
|-------------|---------|------------|
| **Liquidity** | E[T-Bill Rate] | Current T-Bill, GDP growth, inflation, country factor |
| **Bonds Global** | Yield + Roll Return + Valuation − Credit Loss | Current yield, duration, term premium |
| **Bonds HY** | Yield + Roll Return + Valuation − Credit Loss | Yield, credit spread, default rate, recovery rate |
| **Bonds EM** | Yield + Roll Return + Valuation − Credit Loss | Yield, duration, default rate, recovery rate |
| **Bonds Inflation Linked** | Real Carry + Real Roll + Real Valuation + Inflation Indexation − Lag Drag | Current real yield, duration, real term premium, inflation beta, lag drag |
| **Equity (4 regions)** | Dividend Yield + Real EPS Growth + Inflation + Valuation Change | Dividend yield, CAEY, fair CAEY, EPS growth, reversion speed (λ) |
| **Absolute Return** | Risk-Free + Σ(β × Factor Premium) + Alpha | Factor betas, trading alpha, market/size/value/momentum |

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

| Variable | Required | Description |
|----------|----------|-------------|
| `FRONTEND_URL` | Yes | Your Vercel deployment URL (for CORS) |
| `SUPER_USER_EMAIL` | Yes | Email of the admin who can trigger AI refreshes |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key (for quarterly AI research) |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key (bypasses RLS) |
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Same Supabase URL (for frontend) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Supabase anon key (for frontend auth) |
| `NEXT_PUBLIC_API_URL` | Yes | Your Render API URL |
| `DEBUG` | No | `true`/`false` — enables Swagger docs (default: `true`) |

## Local Development

### Backend

```bash
# From the project root
pip install -r requirements-api.txt

# Start the API server
uvicorn api.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Swagger docs at `/docs` when `DEBUG=true`.

### Frontend

```bash
cd web
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

### Database Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run both migration files in the Supabase SQL Editor:
   - `migrations/001_react_scenarios.sql` — scenarios table with RLS
   - `migrations/002_default_assumptions.sql` — defaults and refresh log tables
3. Copy your project URL and keys into your `.env` file

## Deployment

| Service | What | Config |
|---------|------|--------|
| **Vercel** | Frontend (`web/`) | Root directory: `web`, framework: Next.js, add `NEXT_PUBLIC_*` env vars |
| **Render** | Backend API | Build command: `pip install -r requirements-api.txt`, Start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`, add env vars |
| **Supabase** | Database + Auth | Run migration SQL, configure auth providers |

## Admin: Quarterly Assumption Refresh

The admin panel (`/admin/refresh`) allows the super user to:

1. **Research** — Launches a background job that queries Claude Haiku 4.5 with web search across 8 batches (~80 assumptions), with 75-second delays between batches to respect rate limits
2. **Review** — Compare AI-suggested values against current defaults in a sortable table with confidence indicators and source links
3. **Apply** — Accept individual changes which are saved to Supabase and immediately reflected for all users
4. **Revert** — Roll back to the original hardcoded defaults at any time

Estimated cost per refresh: ~$0.15–0.25 USD (Claude Haiku 4.5 with web search).

## Calculation Engine (Standalone)

The `ra_stress_tool` can be used independently of the web app:

```bash
# As a Python module
python -m ra_stress_tool

# Or in code
from ra_stress_tool.main import CMEEngine

engine = CMEEngine()
results = engine.calculate()
print(results.summary_table())
```

See `example_usage.py` for detailed examples.
