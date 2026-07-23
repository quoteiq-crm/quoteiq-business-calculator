'use strict';

/*
 * QuoteIQ marketing graphic generator — single file.
 *
 * Makes ONE OpenAI images.edit call (model gpt-image-2) with three images passed
 * as an ORDERED ARRAY, referenced by index in the prompt:
 *     1 = reference graphic (STYLE/LAYOUT only)
 *     2 = logo             (preserve exactly)
 *     3 = feature photo    (preserve exactly)
 * No pipeline, no second LLM, no critic loop, no negative references. One call.
 *
 * Multi-image signature verified against the installed openai SDK types
 * (openai/resources/images.d.ts, ImageEditParams):
 *     image: Uploadable | Array<Uploadable>   // an array preserves order
 * Buffers become Uploadables via toFile(buffer, filename, { type }).
 * gpt-image always returns b64_json, so response_format is not set.
 *
 * The API key is read ONLY from process.env.OPENAI_API_KEY. Never hardcoded,
 * never logged.
 *
 * Usage:
 *   npm install
 *   # put your three files next to this script (or edit the paths below):
 *   #   reference.png  logo.png  photo.png   (png/jpg/jpeg/webp)
 *   OPENAI_API_KEY=sk-... node generate.js
 */

const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');
const { toFile } = require('openai');

// ===== EDIT ME — brand variables =============================================
const BRAND = {
  color:    '#1f6feb',
  name:     'Summit Pro Painting',
  tagline:  'Licensed. Insured. On time.',
  headline: '$300 Off a Full Exterior Repaint',
  phone:    '(555) 018-2277',
  website:  'summitpropainting.com',
  city:     'Austin, Round Rock, Cedar Park',
};

// ===== EDIT ME — input image paths (ORDER MATTERS) ===========================
const IMAGE_1_REFERENCE = path.join(__dirname, 'reference.png'); // STYLE/LAYOUT only
const IMAGE_2_LOGO      = path.join(__dirname, 'logo.png');      // preserve exactly
const IMAGE_3_PHOTO     = path.join(__dirname, 'photo.png');     // preserve exactly
// =============================================================================

// Fixed params (per spec). input_fidelity is intentionally NOT set.
const MODEL   = 'gpt-image-2';
const SIZE    = '1024x1280';
const QUALITY = 'high';
const N       = 2;

const PROMPT =
`Create ONE complete marketing graphic, filling the entire frame edge to edge — no blank, empty, or letterboxed areas.
- Image 1 is a STYLE AND LAYOUT REFERENCE ONLY. Recreate its composition, color treatment, and visual hierarchy as a brand-new graphic. Do NOT copy its text, its logo, or its photos. Do NOT reproduce any social media interface elements from it.
- Image 2 is the LOGO. Place it cleanly and legibly. Preserve it EXACTLY as provided — do not redraw, recolor, crop, or distort it.
- Image 3 is the FEATURE PHOTO. Use it as the main image. Preserve the subject EXACTLY as provided.
Dominant brand color: ${BRAND.color}.
Business name (exact text): "${BRAND.name}".
Tagline (exact text): "${BRAND.tagline}".
Headline (exact text, large and prominent): "${BRAND.headline}".
Contact line (exact text, small, along one edge): "${BRAND.phone} · ${BRAND.website} · ${BRAND.city}".
Render only the exact text strings above, spelled exactly. No extra words, no duplicate text, no placeholder text. Full-bleed, professional, print-ready — every region of the canvas is designed. Do not invent statistics, reviews, ratings, awards, or trust badges.`;

function mimeOf(p) {
  const e = path.extname(p).toLowerCase();
  if (e === '.png') return 'image/png';
  if (e === '.webp') return 'image/webp';
  if (e === '.jpg' || e === '.jpeg') return 'image/jpeg';
  return 'image/png';
}

function errBody(e) {
  if (e && e.error) return e.error;
  return { message: (e && e.message) || String(e), name: e && e.name };
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('FATAL: OPENAI_API_KEY is not set in the environment.');
    process.exit(1);
  }

  const client = new OpenAI({ apiKey: key, timeout: 300000, maxRetries: 1 });

  // ---- PRECHECK FIRST: confirm egress + key by listing models --------------
  try {
    const list = await client.models.list();
    const ids = (list.data || []).map((m) => m.id);
    const imageModels = ids.filter((i) => /image/i.test(i)).sort();
    console.log(`PRECHECK OK: reached api.openai.com and the key is valid. ${ids.length} models available.`);
    console.log(`Image-capable models: ${imageModels.length ? imageModels.join(', ') : '(none matched /image/)'}`);
    console.log(`Target model "${MODEL}" present in list: ${ids.includes(MODEL) ? 'YES' : 'NO (may still be callable)'}`);
  } catch (e) {
    const status = typeof e?.status === 'number' ? e.status : null;
    const body = JSON.stringify(errBody(e));
    if (/not in allowlist|egress|CONNECT tunnel|not allowed by .* policy/i.test(body)) {
      console.error('PRECHECK FAIL (egress): a NETWORK egress policy blocked the request before it reached OpenAI. This is NOT an OpenAI 401/403. Allowlist api.openai.com for this environment, then re-run.');
    } else if (status === 401) {
      console.error('PRECHECK FAIL (401): the API key is invalid or revoked.');
    } else if (status === 403) {
      console.error('PRECHECK FAIL (403): OpenAI Organization Verification is NOT enabled for this org (required for gpt-image models).');
    } else {
      console.error(`PRECHECK FAIL${status ? ' (' + status + ')' : ''}.`);
    }
    console.error('Exact error body:', body);
    process.exit(1); // STOP.
  }

  // ---- Read the three input images -----------------------------------------
  const inputs = [
    { label: '1 reference', file: IMAGE_1_REFERENCE },
    { label: '2 logo',      file: IMAGE_2_LOGO },
    { label: '3 photo',     file: IMAGE_3_PHOTO },
  ];
  const missing = inputs.filter((i) => !fs.existsSync(i.file));
  if (missing.length) {
    console.error('FATAL: missing input image file(s):');
    missing.forEach((i) => console.error(`  ${i.label}: ${i.file}`));
    console.error('Place your 3 images at those paths (or edit the paths at the top), then re-run.');
    process.exit(1);
  }

  const files = await Promise.all(
    inputs.map((i) => toFile(fs.readFileSync(i.file), path.basename(i.file), { type: mimeOf(i.file) }))
  );

  // ---- THE SINGLE CALL ------------------------------------------------------
  console.log(`Generating: model=${MODEL} size=${SIZE} quality=${QUALITY} n=${N} …`);
  const t0 = Date.now();
  let result;
  try {
    result = await client.images.edit({
      model: MODEL,
      image: files,      // ordered array: [reference, logo, photo]
      prompt: PROMPT,
      size: SIZE,
      quality: QUALITY,
      n: N,
    });
  } catch (e) {
    const elapsed = Date.now() - t0;
    console.error(`\nGENERATION FAILED after ${elapsed} ms.`);
    console.error('HTTP status:', e?.status ?? '(none — network/SDK error)');
    console.error('Full API error body:\n' + JSON.stringify(errBody(e), null, 2));
    process.exit(1); // STOP. Do not add stages.
  }

  const elapsed = Date.now() - t0;
  const b64s = (result.data || []).map((d) => d && d.b64_json).filter(Boolean);
  if (!b64s.length) {
    console.error('FATAL: OpenAI returned no image data. Raw:', JSON.stringify(result).slice(0, 500));
    process.exit(1);
  }

  const saved = [];
  b64s.forEach((b64, i) => {
    const out = path.join(__dirname, `variant_${i + 1}.png`);
    fs.writeFileSync(out, Buffer.from(b64, 'base64'));
    saved.push(out);
  });

  console.log(`\nOK: generated ${saved.length} image(s) in ${elapsed} ms (${(elapsed / 1000).toFixed(1)} s).`);
  saved.forEach((s) => console.log('  saved ' + s));
}

main().catch((e) => {
  console.error('Unexpected error:', e && e.stack ? e.stack : e);
  process.exit(1);
});
