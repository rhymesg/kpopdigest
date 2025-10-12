# K-pop Digest Project Notes

- Build a simple website named K-pop Digest.
- Domain: kpopdigest.com (registered and reserved by the team).
- Fetch K-pop news headlines and summaries via a news search API, rewrite them in natural English, and present them with source links.
- Frontend: deploy on Vercel.
- Backend: run on Google Cloud Run, integrate the news search API, call an LLM to rewrite articles, and store records in the database.
- Database: Neon.
- Prototype the backend first using the Naver News Search API.

## Agent Working Guidelines

- Execution: Safe to run build, lint, type-check, and other automated tasks; avoid interactive commands that require user input. The user will handle any simulator or visual testing steps.
- Runtime: Use `python3` and `pip3` when running Python commands to match the system default.
- Secrets: Classify every configuration value; keep server-only secrets out of the repo and in secret managers; document client-safe keys that ship with the app.
- Process: Think through tasks sequentially, start with the simplest solution, and add nothing beyond explicit requirements; ask before expanding scope.
- Problem Solving: Address root causes instead of masking issues. If a fix is out of scope, surface alternatives clearly.
- Planning: Describe task effort with relative terms and dependencies—never include explicit time estimates.
- Documentation: Keep all comments and docs concise and in English only.
- Technology: Favor the latest stable, non-deprecated libraries and frameworks, and recommend modern alternatives when legacy tech appears.

## Project Structure

- `backend/`
  - Python data ingestion pipeline that fetches articles from Naver (news + blog) and Daum, rewrites them with the OpenAI Responses API, and persists results to Postgres (Neon).
  - Key modules:
    - `run_pipeline.py`: CLI entry point. Supported `--api` flags are `naver_news`, `naver_blog`, and `daum` (or `all` for all three).
    - `src/pipeline.py`: orchestrates fetch → rewrite → store flow. Automatic duplicate detection, final URL resolution, artist linkage, and metrics.
    - `src/naver_news_api.py`, `src/naver_blog_api.py`, `src/daum_api.py`: individual adapters per upstream source.
    - `src/chatgpt_client.py`: system prompt and OpenAI Responses client.
    - `src/artist_registry.py`: canonical artist definitions (slug, display name, search query).
- `frontend/`
  - Next.js (App Router) app served via Vercel. Connects directly to the Neon database using `pg` and renders the latest rewritten articles.
  - Components and pages live in `app/`; server components fetch data from `lib/articles.ts`, which calls Postgres.
  - `app/components/ArticleBoard.tsx` renders the expandable news cards (category-specific styling, KST timestamps).
  - `app/sitemap.ts` produces `sitemap.xml` using the artist registry.
  - Requires `DATABASE_URL` (copied from `backend/.env`) and `NEXT_PUBLIC_SITE_URL` in deployment environments.

## Adding a New Artist

1. **Backend registry** – Edit `backend/src/artist_registry.py` and add an `ArtistDefinition` entry with:
   - `display_name`: canonical uppercase name (shown to users).
   - `slug`: URL slug (lowercase, hyphenated as needed).
   - `search_query`: comma-separated Korean/English keywords for Naver/Daum queries.
2. **Frontend navigation** – Edit `frontend/lib/artists.ts` and append the same `slug`/`name` pair so the UI lists the artist and sitemap includes it.
3. **(Optional) Category tuning** – If the new artist relies on a unique community or blog host, update `_COMMUNITY_HOST_TOKENS` / `_BLOG_HOST_TOKENS` in `backend/src/daum_api.py` so categorization stays accurate.
4. Run `python backend/run_pipeline.py --store --artist NEW_ARTIST --api all --limit …` to seed initial articles and metrics.

## Deployment Notes

- **Backend jobs** run via GitHub Actions (daily cron + on-push) and expect secrets (`NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `DAUM_REST_API_KEY`, `OPENAI_API_KEY`, `DATABASE_URL`).
- **Frontend** is deployed on Vercel; ensure `DATABASE_URL` and `NEXT_PUBLIC_SITE_URL` are configured in project settings. The app requires full Node.js runtime (Cloudflare Pages is incompatible with `pg`).
- Custom domain DNS: root A records to Vercel IPs (`76.76.21.21`, `216.198.79.1`), `www` as CNAME to the provided Vercel DNS hostname, proxy disabled.
