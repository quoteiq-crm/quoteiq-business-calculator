# QuoteIQ AI Marketing Studio (prototype)

Generates one branded marketing graphic from brand info + one feature photo + one
reference graphic, using **exactly one** OpenAI `images.edit` call (model
`gpt-image-2`). No pipeline, no second LLM, no critic loop, no negative
references.

- **Backend:** Node + Express, single server (`server.js`). Routes: `GET /`
  (app), `POST /generate`, `GET /health`.
- **Frontend:** one static `public/index.html`, vanilla HTML/CSS/JS, mobile-first.
  Converts phone photos (incl. HEIC on iOS) to JPEG in the browser, downscales to
  ≤2048px, honors EXIF orientation, then uploads.
- **Key:** read only from `process.env.OPENAI_API_KEY`. Never sent to the
  frontend, never logged, never committed.

## Image call (the one call)

Three images are passed as an **ordered array** to `images.edit`, referenced by
index in the prompt:

1. reference graphic — style/layout only
2. logo — preserved exactly
3. feature photo — preserved exactly

`n=2`, `size` and `quality` from the UI. `input_fidelity` is **not** set
(gpt-image-2 locks it to high). gpt-image returns base64, decoded and returned to
the browser as data URIs.

## Run locally

```bash
cd marketing-studio
npm install

# Step 0 precheck — confirms egress + key by listing models:
OPENAI_API_KEY=sk-... npm run precheck
#   OK        -> reached OpenAI and key is valid
#   403       -> Organization Verification not enabled on the account/org
#   401       -> key invalid/revoked
#   no status -> network/egress cannot reach api.openai.com

# Start the server:
OPENAI_API_KEY=sk-... npm start
# open http://localhost:3000
```

Or with a local `.env` (copied from `.env.example`, gitignored):

```bash
npm run precheck:local
npm run start:local
```

## Deploy

Set `OPENAI_API_KEY` as a **secret/environment variable on the platform** — never
in the source.

**Request timeout matters.** One high-quality call with 3 images and `n=2` can
take 60–120s. Deploy somewhere that allows long requests:

- ✅ **Render (Web Service)** / **Railway** / **Fly.io** / a plain VM — no hard
  short request cap. The included `render.yaml` (repo root) deploys this folder
  directly: connect the repo as a Render Blueprint and add `OPENAI_API_KEY` in the
  dashboard.
- ⚠️ **Vercel / Netlify serverless** cap function duration (often 10–60s) — a
  120s image call will be killed. Avoid, or fall back to `n=1` × two parallel
  calls. This app uses a single `n=2` call by design.

The OpenAI client timeout is 300000ms and the HTTP server timeout is 310000ms.
