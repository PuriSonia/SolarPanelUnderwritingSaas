# Solar SaaS Dashboard (Next.js)

Basic Next.js dashboard that plugs into the FastAPI backend endpoints:
- Login / Register
- Portfolio cards
- Sites list + create
- Site detail page with charts (Recharts) + financial + Scope 2

## Setup
1) Copy `.env.local.example` to `.env.local`
2) Set API base:
   - `NEXT_PUBLIC_API_BASE=http://localhost:8000`

## Run
```bash
npm install
npm run dev
```

Open:
- http://localhost:3000

## Notes
- Auth token is stored in localStorage for MVP simplicity.
  For production, switch to httpOnly cookies.


## Upload UI
Go to `/uploads` to upload generation and grid CSVs without Swagger.


## Onboarding UI
Open a site detail page `/sites/[id]` to create a Solar System and set the site tariff.
