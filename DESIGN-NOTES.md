# Atlas — 2026 UI Redesign ("Nightwatch / Obsidian Command")

A full visual redesign of the **Atlas** prospecting map (`atlas-demo.html`). The old
light-cream theme with 1px-bordered cards and a cramped, 4-row-wrapping top bar was
replaced with a dark, glass **mission-control** interface — designed to harmonize with
the dark map instead of fighting it.

**Nothing about the product logic changed.** All behavior, data, scoring, IQ-Credits
metering, door-knock statuses, route builder, AI intro, CSV import, and localStorage
persistence are byte-for-byte the same. This was a chrome + CSS + marker-styling pass,
not a rewrite.

## What changed

**Look & feel**
- OLED-black canvas with a subtle gold/green/blue ambient aurora bleeding from the edges.
- Depth comes from **layered translucency and glow**, not gray hairlines — floating
  glass on the map controls, popups, modals, toast, and pipeline panel.
- Tight, tabular display typography; large expressive data numbers.
- A strict color contract: **gold = "act now"**, **green = "yours / secured"**, the 11
  category hues appear only as emitted light (pin glow, chip dots, gauge arcs).

**Signature elements**
- **Radial Route-Match score gauge** — a conic-gradient ring that animates 0→score on
  open (via a registered `@property --val`), with a leading tick and a counting number.
- **Score breakdown as an instrument readout** — the three weighted factors
  (proximity / density / category fit) render as animated fill-bars.
- **Glowing map pins** — category-colored halos; high-opportunity pins pulse.
- **Credits "reactor" chip** — pulses each time the balance changes (spend feedback).

**Layout fixes**
- The filter chips that used to wrap into ~4 messy rows in the top bar were relocated
  into a proper **"Atlas · Prospects" control deck** at the top of the left panel. The
  top bar is now a single clean row.
- The control deck + legend hide while a detail view is open for a focused reading view.

**Small correctness fixes made along the way**
- `Banks` used `icon:'building'`, which doesn't exist in the icon set (pins/thumbs
  rendered empty). Corrected to `icon:'bank'`.
- Category palette retuned for legibility on a dark basemap.
- Removed a leftover light (`#fafbfc`) panel background inside the customer detail view.

## How it's built

The redesign is applied deterministically so the diff is reviewable and reproducible:

```
design/
  atlas-demo.orig.html   # pristine reference demo (the "before")
  atlas-2026.css         # the new design system (edit this to tweak the look)
  build.py               # swaps the 3 legacy <style> blocks + a few structural edits
atlas-demo.html          # the shipped, self-contained result (the "after")
```

Rebuild after editing the CSS or the assembler:

```bash
python3 design/build.py        # regenerates ./atlas-demo.html
```

`atlas-demo.html` is fully self-contained (Leaflet + data are inlined) — just open it
in a browser. It loads Inter and the CARTO dark basemap over the network, exactly as
the original did.
