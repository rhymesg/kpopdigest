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
