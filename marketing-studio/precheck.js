'use strict';

/**
 * STEP 0 PRECHECK.
 *
 * Confirms (a) network egress to api.openai.com and (b) that the key works, by
 * listing models. Prints OK, or the exact failure with an explicit reading of
 * 403 (org verification) vs 401 (bad/revoked key) vs a network/egress block.
 *
 * Run:  OPENAI_API_KEY=sk-... node precheck.js
 * The key is read ONLY from process.env.OPENAI_API_KEY. It is never printed.
 */

const OpenAI = require('openai');

(async () => {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('PRECHECK FAIL: OPENAI_API_KEY is not set in the environment.');
    process.exit(1);
  }

  const client = new OpenAI({ apiKey: key, timeout: 30000, maxRetries: 0 });

  try {
    const list = await client.models.list();
    const ids = (list.data || []).map((m) => m.id);
    const imageModels = ids.filter((i) => /image/i.test(i)).sort();
    console.log(`PRECHECK OK: reached api.openai.com and the key is valid. ${ids.length} models available.`);
    console.log(`Image-capable models: ${imageModels.length ? imageModels.join(', ') : '(none matched /image/)'}`);
    const target = process.env.IMAGE_MODEL || 'gpt-image-2';
    console.log(`Target model "${target}" present in list: ${ids.includes(target) ? 'YES' : 'NO (may still be callable; models.list can omit some image models)'}`);
    process.exit(0);
  } catch (e) {
    const status = e && typeof e.status === 'number' ? e.status : null;
    const msg = (e && e.error && e.error.message) || (e && e.message) || String(e);
    if (/not in allowlist|egress|not allowed by .* policy|CONNECT tunnel/i.test(msg)) {
      console.error('PRECHECK FAIL (egress): a NETWORK egress policy blocked the request before it reached OpenAI — api.openai.com is not allowlisted for this environment. This is NOT an OpenAI 403/401. Add api.openai.com to the environment network egress settings, then re-run.');
    } else if (status === 403) {
      console.error('PRECHECK FAIL (403): OpenAI Organization Verification is NOT enabled for this account/org (required for gpt-image models), or the org is not permitted to use this endpoint.');
    } else if (status === 401) {
      console.error('PRECHECK FAIL (401): the API key is invalid or revoked.');
    } else if (!status) {
      console.error('PRECHECK FAIL: no HTTP status returned. This is a NETWORK/EGRESS problem reaching api.openai.com (connection refused / proxy CONNECT denied / DNS), NOT an OpenAI account response.');
    } else {
      console.error(`PRECHECK FAIL (${status}): ${msg}`);
    }
    console.error('Detail:', msg);
    process.exit(1);
  }
})();
