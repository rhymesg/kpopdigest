# K-pop Digest

K-pop Digest aggregates Korean entertainment coverage from Naver, Daum, and major community boards, rewrites the highlights in English, and links readers back to the original sources. The project consists of a Python ingestion backend and a Next.js frontend served via Vercel.

## Technology Stack

- **Backend** – Python 3
  - Article ingestion pipeline (`backend/`) combining Naver News/Blog and Daum Web APIs
  - OpenAI Responses API for title/summary rewrites (system prompt tuned for K-pop news/blog/community content)
  - Postgres (Neon) for persistent storage (`Article`, `Artist`, `ArticleArtist`, `ArtistMetrics`)
  - GitHub Actions: scheduled runs + push-triggered runs for ingestion/rewrites
- **Frontend** – Next.js 14 (App Router)
  - `frontend/` renders the latest articles (server components) with expandable cards showing title, summary, category, and KST timestamps
  - Direct Postgres access via `pg`
  - Vercel deployment with custom domain (`kpopdigest.com`)
  - Dynamic sitemap (`app/sitemap.ts`) derived from the artist registry
- **Shared**
  - `backend/src/artist_registry.py` / `frontend/lib/artists.ts`: canonical artist list (slug, display name, search query)
  - `backend/src/api_utils.py`: publisher/source normalization helpers

## How to Run

### Backend Pipeline
1. **Install dependencies**
   ```bash
   cd backend
   pip3 install -r requirements.txt
   ```
2. **Configure environment** (`backend/.env`)
   ```env
   NAVER_CLIENT_ID=...
   NAVER_CLIENT_SECRET=...
   DAUM_REST_API_KEY=...
   OPENAI_API_KEY=...
   DATABASE_URL=postgresql://...
   ```
3. **Run the CLI** (fetch → rewrite → store)
   ```bash
   python3 run_pipeline.py --store --limit 20 --api all --artist BLACKPINK
   ```
   - Supported `--api` values: `naver_news`, `naver_blog`, `daum`, `all`
   - Multiple `--artist` flags allowed (otherwise all registered artists are processed)

### Frontend
1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```
2. **Environment**
   - `frontend/.env` should contain the same `DATABASE_URL` (copied automatically from `backend/.env`).
   - Set `NEXT_PUBLIC_SITE_URL=https://kpopdigest.com` (or your preview URL) when deploying.
3. **Run locally**
   ```bash
   npm run dev
   ```
4. **Production build**
   ```bash
   npm run build
   npm start
   ```

---
For more detailed agent notes and onboarding guidance, see `CLAUDE.md`.
