# Atlas — 2026 UI Redesign ("Daylight Command", light/white theme)

A full visual redesign of the **Atlas** prospecting map (`atlas-demo.html`). The old
theme (1px-bordered cards, flat gray, and a cramped top bar whose filter chips wrapped
into ~4 messy rows) was replaced with a bright, premium **light/white** interface, paired
with a light CARTO Positron basemap so the map and chrome read as one clean surface.

**Nothing about the product logic changed.** All behavior, data, scoring, IQ-Credits
metering, door-knock statuses, route builder, AI intro, CSV import, and localStorage
persistence are byte-for-byte the same. This was a chrome + CSS + marker-styling pass,
not a rewrite.

## What changed

**Look & feel**
- Bright white surfaces on a soft warm-white field (a faint gold/green ambient wash).
- Depth from **soft layered shadows and generous whitespace**, not gray hairlines.
- Frosted-white glass for floating map controls, popups, modals, toast, and the pipeline
  panel.
- Tight, tabular display typography; large expressive data numbers.
- A clear color language: **gold = "act now"**, **green = "yours / secured"**, the 11
  category hues carry identity on thumbs, chips, pins, and the score arc.
- Light **CARTO Positron** basemap (was dark), so pins and chrome sit on a clean map.

**Signature elements**
- **Radial Route-Match score gauge** — a conic-gradient ring that animates 0→score on
  open (via a registered `@property --val`), with a leading tick and a counting number.
- **Score breakdown as an instrument readout** — the three weighted factors
  (proximity / density / category fit) render as animated fill-bars.
- **Map pins tuned for a light basemap** — white pills with a category-colored border and
  icon; high-opportunity pins pulse; customers are white discs with a green ring; clusters
  are dark ink discs that pop on the light map.
- **Credits "reactor" chip** — pulses each time the balance changes (spend feedback).

**Layout fixes**
- The filter chips that used to wrap into ~4 messy rows in the top bar were relocated
  into a proper **"Atlas · Prospects" control deck** at the top of the left panel. The
  top bar is now a single clean row.
- The control deck + legend hide while a detail view is open for a focused reading view.

**Small correctness fixes made along the way**
- `Banks` used `icon:'building'`, which doesn't exist in the icon set (pins/thumbs
  rendered empty). Corrected to `icon:'bank'`.
- Retuned the category palette for the light basemap.
- Removed a leftover light panel background inside the customer detail view.

## How it's built

The redesign is applied deterministically so the diff is reviewable and reproducible:

```
design/
  atlas-demo.orig.html   # pristine reference demo (the "before")
  atlas-2026.css         # the new design system (edit this to tweak the look)
  build.py               # swaps the 3 legacy <style> blocks, structural edits, light basemap
atlas-demo.html          # the shipped, self-contained result (the "after")
```

Rebuild after editing the CSS or the assembler:

```bash
python3 design/build.py        # regenerates ./atlas-demo.html
```

`atlas-demo.html` is fully self-contained (Leaflet + data are inlined) — just open it
in a browser. It loads Inter and the CARTO light basemap over the network, exactly as
the original did.
