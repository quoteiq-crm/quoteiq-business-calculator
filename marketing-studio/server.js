'use strict';

/**
 * QuoteIQ AI Marketing Studio (prototype) — backend.
 *
 * ONE Express server. Serves ./public/index.html and exposes POST /generate,
 * which makes exactly ONE OpenAI images.edit call (model gpt-image-2) with the
 * three uploaded images passed as an ordered array. No pipeline, no second LLM,
 * no critic loop, no negative references.
 *
 * The API key is read ONLY from process.env.OPENAI_API_KEY. It is never sent to
 * the frontend and never logged.
 */

const path = require('path');
const express = require('express');
const OpenAI = require('openai');
const { toFile } = require('openai');

// ---- Config ------------------------------------------------------------------
const PORT = process.env.PORT || 3000;

// The image model. Single constant so it is trivial to change. gpt-image-2 locks
// input fidelity to high automatically — there is intentionally no input_fidelity
// parameter set anywhere in this file.
const MODEL = process.env.IMAGE_MODEL || 'gpt-image-2';

// Allowed output sizes -> exact pixel strings sent to the API.
const SIZE_MAP = {
  '1:1': '1024x1024',    // Square
  '4:5': '1024x1280',    // Portrait (Instagram/Facebook feed)
  '9:16': '1024x1792',   // Story/Reels
  '3:2': '1536x1024',    // Landscape
};

const ALLOWED_QUALITY = new Set(['medium', 'high']);

// ---- OpenAI client -----------------------------------------------------------
// timeout 5 min, maxRetries 1 — one high-quality call with 3 images + n=2 can
// take 60-120s.
function makeClient() {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return null;
  return new OpenAI({ apiKey, timeout: 300000, maxRetries: 1 });
}

// ---- Helpers -----------------------------------------------------------------

// Accept either a data URL ("data:image/jpeg;base64,....") or a bare base64
// string. Returns { buffer, mime }.
function decodeImage(input, fallbackName) {
  if (typeof input !== 'string' || !input.length) {
    throw new Error(`Missing image: ${fallbackName}`);
  }
  let mime = 'image/jpeg';
  let b64 = input;
  const m = /^data:([^;]+);base64,(.*)$/s.exec(input);
  if (m) {
    mime = m[1];
    b64 = m[2];
  }
  const buffer = Buffer.from(b64, 'base64');
  if (!buffer.length) throw new Error(`Empty image: ${fallbackName}`);
  return { buffer, mime };
}

function ext(mime) {
  if (mime === 'image/png') return 'png';
  if (mime === 'image/webp') return 'webp';
  return 'jpg';
}

// Build the EXACT prompt from the spec, interpolating the brand fields.
// Regenerate = no tweak. Apply tweak = append ONE line, change nothing else.
function buildPrompt(fields, tweak) {
  const {
    color = '', name = '', tagline = '', headline = '',
    phone = '', website = '', city = '',
  } = fields;

  let prompt =
`Create ONE complete marketing graphic, filling the entire frame edge to edge — no blank, empty, or letterboxed areas.
- Image 1 is a STYLE AND LAYOUT REFERENCE ONLY. Recreate its composition, color treatment, and visual hierarchy as a brand-new graphic. Do NOT copy its text, its logo, or its photos. Do NOT reproduce any social media interface elements from it.
- Image 2 is the LOGO. Place it cleanly and legibly. Preserve it EXACTLY as provided — do not redraw, recolor, crop, or distort it.
- Image 3 is the FEATURE PHOTO. Use it as the main image in the design. Preserve the subject EXACTLY as provided — do not regenerate or alter it.
Dominant brand color: ${color}.
Business name (exact text): "${name}".
Tagline (exact text): "${tagline}".
Headline (exact text, large and prominent): "${headline}".
Contact line (exact text, small, along one edge): "${phone}  ·  ${website}  ·  ${city}".
Render only the exact text strings above, spelled exactly. No extra words, no duplicate text, no placeholder text, no lorem ipsum. Full-bleed, professional, print-ready — every region of the canvas is designed. Do not invent statistics, reviews, ratings, awards, or trust badges.`;

  const t = (tweak || '').trim();
  if (t) prompt += `\nAdjustment: ${t}.`;
  return prompt;
}

// Turn an OpenAI/network error into a plain, user-facing message + status.
function describeError(err) {
  const status = err && typeof err.status === 'number' ? err.status : null;
  const apiBody = (err && err.error) || null;
  const code = apiBody && apiBody.code;
  const apiMsg = (apiBody && apiBody.message) || err.message || String(err);

  // Content moderation refusals must be explicit, never silent.
  // An egress/allowlist proxy can inject its own 403 before the request ever
  // reaches OpenAI. Detect that and report it as a network-policy block, NOT as
  // OpenAI org verification.
  if (/not in allowlist|egress|not allowed by .* policy|CONNECT tunnel/i.test(apiMsg)) {
    return {
      status: 502,
      kind: 'egress_blocked',
      message:
        'Blocked by a network egress policy before reaching OpenAI — the host ' +
        'api.openai.com is not allowlisted for this environment. Add it to the ' +
        'environment\'s network egress settings. Details: ' + apiMsg,
    };
  }

  const looksModerated =
    status === 400 &&
    (code === 'moderation_blocked' ||
      /moderation|safety system|content policy|rejected as a result/i.test(apiMsg));

  if (looksModerated) {
    return {
      status: 400,
      kind: 'moderation',
      message:
        'The request was REFUSED by OpenAI\'s content moderation. It was not generated. ' +
        'Try a different photo/reference or reword the headline. Details: ' + apiMsg,
    };
  }
  if (status === 403) {
    return {
      status: 403,
      kind: 'org_verification',
      message:
        'OpenAI returned 403. This account/organization is not verified for image ' +
        'generation (Organization Verification is required to use gpt-image models), ' +
        'or the org lacks access to ' + MODEL + '. Enable Organization Verification in ' +
        'the OpenAI dashboard. Details: ' + apiMsg,
    };
  }
  if (status === 401) {
    return {
      status: 401,
      kind: 'bad_key',
      message: 'OpenAI returned 401 — the API key is invalid or revoked. Details: ' + apiMsg,
    };
  }
  if (status === 400) {
    return {
      status: 400,
      kind: 'bad_request',
      message:
        'OpenAI returned 400 — bad request, usually an unsupported image format/size for ' +
        MODEL + '. Details: ' + apiMsg,
    };
  }
  if (status === 429) {
    return {
      status: 429,
      kind: 'rate_limit',
      message: 'OpenAI returned 429 — rate limit or quota exceeded. Wait and retry. Details: ' + apiMsg,
    };
  }
  if (/tim(e|)out|ETIMEDOUT|ESOCKETTIMEDOUT/i.test(apiMsg) || err.name === 'APIConnectionTimeoutError') {
    return {
      status: 504,
      kind: 'timeout',
      message: 'The image generation timed out. Try again, or use Medium quality. Details: ' + apiMsg,
    };
  }
  if (!status) {
    return {
      status: 502,
      kind: 'network',
      message:
        'Could not reach api.openai.com (network/egress error, not an OpenAI response). ' +
        'If this is a sandbox, its egress policy may block api.openai.com. Details: ' + apiMsg,
    };
  }
  return { status: status || 500, kind: 'unknown', message: apiMsg };
}

// ---- App ---------------------------------------------------------------------
const app = express();

// The 100kb default WILL fail on phone photos. Raise to 50mb.
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

app.use(express.static(path.join(__dirname, 'public')));

app.get('/health', (req, res) => {
  res.json({ ok: true, model: MODEL, keyConfigured: !!process.env.OPENAI_API_KEY });
});

app.post('/generate', async (req, res) => {
  // Give this response plenty of time.
  res.setTimeout(310000);

  const started = Date.now();
  const client = makeClient();
  if (!client) {
    return res.status(500).json({
      error: {
        status: 500,
        kind: 'config',
        message: 'Server misconfigured: OPENAI_API_KEY is not set in the environment.',
      },
    });
  }

  try {
    const body = req.body || {};
    const sizeKey = body.size || '4:5';
    const size = SIZE_MAP[sizeKey];
    if (!size) throw Object.assign(new Error(`Unknown size "${sizeKey}"`), { status: 400 });

    const quality = ALLOWED_QUALITY.has(body.quality) ? body.quality : 'medium';

    // Decode the three images. ORDER MATTERS and must match the prompt:
    // index 1 = reference, index 2 = logo, index 3 = feature photo.
    const ref = decodeImage(body.reference, 'reference graphic');
    const logo = decodeImage(body.logo, 'logo');
    const photo = decodeImage(body.photo, 'feature photo');

    const files = await Promise.all([
      toFile(ref.buffer, `1-reference.${ext(ref.mime)}`, { type: ref.mime }),
      toFile(logo.buffer, `2-logo.${ext(logo.mime)}`, { type: logo.mime }),
      toFile(photo.buffer, `3-photo.${ext(photo.mime)}`, { type: photo.mime }),
    ]);

    const prompt = buildPrompt(body, body.tweak);

    // ---- THE SINGLE CALL -----------------------------------------------------
    // One images.edit call. Three images as an ordered array. n=2. No
    // input_fidelity, no response_format (gpt-image returns b64_json).
    const result = await client.images.edit({
      model: MODEL,
      image: files,
      prompt,
      size,
      quality,
      n: 2,
    });
    // --------------------------------------------------------------------------

    const images = (result.data || [])
      .map((d) => d && d.b64_json)
      .filter(Boolean)
      .map((b64) => `data:image/png;base64,${b64}`);

    if (!images.length) {
      throw new Error('OpenAI returned no image data.');
    }

    const elapsedMs = Date.now() - started;
    console.log(`[generate] model=${MODEL} size=${size} quality=${quality} n=2 variants=${images.length} elapsedMs=${elapsedMs}`);

    res.json({ images, meta: { model: MODEL, size, quality, elapsedMs } });
  } catch (err) {
    const info = describeError(err);
    const elapsedMs = Date.now() - started;
    // Log status + body (never the key).
    console.error(`[generate] ERROR status=${info.status} kind=${info.kind} elapsedMs=${elapsedMs} :: ${info.message}`);
    if (err && err.error) {
      try { console.error('[generate] api error body:', JSON.stringify(err.error)); } catch (_) {}
    }
    res.status(info.status).json({ error: info });
  }
});

const server = app.listen(PORT, () => {
  console.log(`QuoteIQ AI Marketing Studio listening on :${PORT} (model=${MODEL}, key ${process.env.OPENAI_API_KEY ? 'configured' : 'NOT configured'})`);
});

// Route/server timeouts must allow 120s+ responses.
server.setTimeout(310000);
server.requestTimeout = 310000;
server.headersTimeout = 320000;
server.keepAliveTimeout = 320000;
