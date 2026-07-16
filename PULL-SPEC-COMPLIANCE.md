# Pull Operating Spec — what the demo executes vs. what's backend-only

`ATLASPULLSPEC` is a **backend** operating spec (server-side Google Places calls, a
`atlasPull` cloud function, Firestore, credit ledgers). `atlas-demo.html` is a
self-contained front-end demo with no server — so this pass made the demo's **Pull
simulation obey every rule a front-end can observably honor**, and documents the pieces
that can only live on the server.

Verified headless: a pull loads 100% of the category in the current viewport (fewer when
zoomed in) for a one-time 50 IQC; once owned, toggling the chip 5× costs 0 and never
re-shows "Pulling…"; Full City Sweep blocks when short and pulls all 11 categories at
400 IQC; contact reveal is a one-time 10 IQC (free re-open); phone hidden until
reveal/save; nothing expires. No JS errors.

| Spec | In the demo now | Backend-only (documented, not runnable here) |
|---|---|---|
| **§1** One pull | A pull loads **every** category prospect **inside the current map viewport** (100% of what's listed there — no cap), costs **50 IQC once**, and the category is then **owned for the whole session** — its chip is a free show/hide toggle (marked "Saved") that is never charged or re-pulled. | `atlasPull` cloud fn; Places API (New) Text Search; **server-side key only**. |
| **§2** Locations only | Pulled prospects expose **location only**; phone/website are withheld until Reveal/Save (Call-Now no longer appears until then). | Places field mask `place_id,displayName,formattedAddress,location,primaryType,types`. |
| **§3** "All" vs Full City Sweep | Re-showing a pulled category is a **free view toggle** (no fetch). **Full City Sweep** pulls **every not-yet-owned category** at once; its price is **dynamic — 50 IQC × categories still locked, capped at 400** (so it drops as you own more, and the button disables to "All categories pulled" once you own all 11). Already-owned categories are never re-charged. | — |
| **§4** Load more | **Removed** — a pull already loads 100% of the category in-area, so there is nothing left to load (no "+25 IQC" / "next batch"). | — |
| **§5** Metering order | Balance is checked **before** the pull; credits deduct **before** the "fetch"; **never a partial unlock**; insufficient funds → shake + top-up path. | Refund on total failure; per-pull **audit ledger**; **≤30 pulls/workspace/hour** abuse brake. |
| **§6** Reveal contact | `10 IQC` reveal, **free on Save**; keeps the existing "no phone/website" info state. | Single Place Details call for one place. |
| **§7** Save to Contacts | Copies name/address into the contractor's own record; contact info free at save; persists across restart. | First-party CRM record; never re-syncs from Google. |
| **§8** Dedupe | Customers and prospects are separate datasets in the demo, so a customer never appears as a prospect. | Name + normalized-address match against existing contacts. |
| **§9** Expiry | **Nothing expires** (product decision): once pulled/revealed/saved, data persists for the entire session with no TTL, staleness, or "refresh to view." | If a TTL is ever reintroduced server-side, it would be a `fetched_at` cache window — not enabled today. |
| **§10** Category → Places type | Mapping embedded as a reference `PLACES_TYPE_MAP` const (all 11). | Lives in server config; new categories = config-only. |
| **Build-time checks** | — | Verify live Places (New) SKU/field prices and the current 30-day ToS clause before locking economics. |

**Credit prices** (`PULL_PRICE` 50 / reveal 10) are named constants in the pull-spec script;
**Full City Sweep** is computed dynamically as `min(400, 50 × locked-category count)`. Per §5
they ship behind remote config in production — do not hardcode there.

**Areas** (drawn pull boundaries): an Area scopes `pickPullBatch` by point-in-polygon instead of
the viewport, so pulling a locked category loads 100% of it *inside the shape* for the usual 50 IQC.
Category ownership is global (own-once), so no per-area re-charging exists — that stays a backend
metering concern. Areas persist in the same `localStorage` state as the rest of the demo.
