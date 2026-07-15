# Pull Operating Spec — what the demo executes vs. what's backend-only

`ATLASPULLSPEC` is a **backend** operating spec (server-side Google Places calls, a
`atlasPull` cloud function, Firestore, credit ledgers). `atlas-demo.html` is a
self-contained front-end demo with no server — so this pass made the demo's **Pull
simulation obey every rule a front-end can observably honor**, and documents the pieces
that can only live on the server.

Verified headless (`pull-smoke.js`): bounded pull loads 43/43 at metro zoom but only 11
in a tight view; 50-IQC pull; free re-toggle costs 0; 60 cap honored; Full City Sweep
blocked at 130 IQC and pulls all 11 categories at 400 IQC; graceful "no more in area";
phone hidden until reveal. No JS errors.

| Spec | In the demo now | Backend-only (documented, not runnable here) |
|---|---|---|
| **§1** One pull | Sends nothing unbounded — a pull loads only category prospects **inside the current map viewport**, capped at **60**, costs **50 IQC**, then the chip becomes a free on/off toggle. | `atlasPull` cloud fn; Places API (New) Text Search (≤3 pages); **server-side key only**. |
| **§2** Locations only | Pulled prospects expose **location only**; phone/website are withheld until Reveal/Save (Call-Now no longer appears until then). | Places field mask `place_id,displayName,formattedAddress,location,primaryType,types`. |
| **§3** "All" vs Full City Sweep | Re-showing a pulled category is a **free view toggle** (no fetch). **Full City Sweep** button pulls **all 11 categories in view** for **400 IQC**. | — |
| **§4** Load more | `+25 IQC` runs a **new bounded pull** for the next batch of the same category/area; graceful message when none remain. | Next Places page token. |
| **§5** Metering order | Balance is checked **before** the pull; credits deduct **before** the "fetch"; **never a partial unlock**; insufficient funds → shake + top-up path. | Refund on total failure; per-pull **audit ledger**; **≤30 pulls/workspace/hour** abuse brake. |
| **§6** Reveal contact | `10 IQC` reveal, **free on Save**; keeps the existing "no phone/website" info state. | Single Place Details call for one place. |
| **§7** Save to Contacts | Copies name/address into the contractor's own record; contact info free at save; persists across restart. | First-party CRM record; never re-syncs from Google. |
| **§8** Dedupe | Customers and prospects are separate datasets in the demo, so a customer never appears as a prospect. | Name + normalized-address match against existing contacts. |
| **§9** 30-day expiry | Copy states prospect data "expires in 30 days unless saved." | `place_id` kept forever; Google display fields cached with `fetched_at` + 30-day TTL; expired → "refresh to view" = new metered pull. |
| **§10** Category → Places type | Mapping embedded as a reference `PLACES_TYPE_MAP` const (all 11). | Lives in server config; new categories = config-only. |
| **Build-time checks** | — | Verify live Places (New) SKU/field prices and the current 30-day ToS clause before locking economics. |

**Credit prices** (`PULL_PRICE` 50 / `LOADMORE_PRICE` 25 / `SWEEP_PRICE` 400 / reveal 10) are
grouped as named constants in the pull-spec script for the demo. Per §5 they ship behind
remote config in production — do not hardcode there.
