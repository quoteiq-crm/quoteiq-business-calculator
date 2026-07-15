#!/usr/bin/env python3
# Deterministic assembler: pristine atlas-demo.orig.html -> redesigned atlas-demo.html
import re, sys, pathlib

HERE = pathlib.Path(__file__).parent          # design/
ROOT = HERE.parent                            # repo root
SRC  = (HERE / "atlas-demo.orig.html").read_text()
CSS  = (HERE / "atlas-2026.css").read_text()
OUT  = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (ROOT / "atlas-demo.html")

lines = SRC.split("\n")

def find(pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    raise RuntimeError("marker not found")

# ---- locate the four <style> blocks ----
leaflet_close = find(lambda l: l.strip() == "</style>")            # 1st </style> (leaflet-css)
A_open  = find(lambda l: l.strip() == "<style>", leaflet_close+1)  # main design block
A_close = find(lambda l: l.strip() == "</style>", A_open+1)
cl_open = find(lambda l: l.strip() == "<style>", A_close+1)        # leaflet cluster block
cl_close= find(lambda l: l.strip() == "</style>", cl_open+1)
B_open  = find(lambda l: 'id="v4-modern-pass"' in l)
B_close = find(lambda l: l.strip() == "</style>", B_open+1)
C_open  = find(lambda l: 'id="atlas-additions"' in l)
C_close = find(lambda l: l.strip() == "</style>", C_open+1)

# keep only the animation/base portion of the cluster block (drop legacy theme + zoom rules)
theme_idx = find(lambda l: "/* QuoteIQ custom cluster theme */" in l, cl_open+1)
cluster_base = "\n".join(lines[cl_open+1:theme_idx]).rstrip()

BLOCK_A = '<style id="atlas-2026">\n' + CSS.rstrip() + "\n</style>"
BLOCK_CLUSTER = ('<style id="leaflet-cluster-base">\n' + cluster_base +
                 "\n/* theme + zoom-gated pins now live in #atlas-2026 */\n</style>")
BLOCK_B = '<style id="v4-modern-pass">/* superseded by #atlas-2026 */</style>'
BLOCK_C = '<style id="atlas-additions">/* merged into #atlas-2026 */</style>'

new_lines = (
    lines[:A_open]
    + [BLOCK_A]
    + lines[A_close+1:cl_open]
    + [BLOCK_CLUSTER]
    + lines[cl_close+1:B_open]
    + [BLOCK_B]
    + lines[B_close+1:C_open]
    + [BLOCK_C]
    + lines[C_close+1:]
)
html = "\n".join(new_lines)

# ============ targeted structural edits ============
def sub(old, new, count=1, label=""):
    global html
    n = html.count(old)
    assert n == count, f"[{label}] expected {count} of target, found {n}"
    html = html.replace(old, new)

# 1) remove the filter-chips from the topbar (relocated into the left panel)
sub('  <div class="filter-chips" id="filterChips"></div>\n', '', 1, "topbar-chips-remove")

# 2) insert the control deck (relocated filters) + id the legend, at top of left panel
sub(
 '  <div class="left-panel" id="leftPanel">\n\n    <!-- INLINE LEGEND -->\n    <div class="inline-legend">',
 '  <div class="left-panel" id="leftPanel">\n\n'
 '    <!-- CONTROL DECK — filters relocated out of the cramped top bar -->\n'
 '    <div class="control-deck" id="controlDeck">\n'
 '      <div class="deck-title">\n'
 '        <h1><span class="deck-mark">◈</span> Atlas · Prospects</h1>\n'
 '        <span class="live">Live map</span>\n'
 '      </div>\n'
 '      <div class="filter-chips" id="filterChips"></div>\n'
 '    </div>\n\n'
 '    <!-- INLINE LEGEND -->\n    <div class="inline-legend" id="inlineLegend">',
 1, "control-deck-insert")

# 3) radial score gauge replaces the flat score number
sub(
 '<div class="score-callout">\n'
 '      <div class="score-num ${ct}">${p.opportunity_score}</div>\n'
 '      <div class="score-info">\n'
 '        <strong>Route Match Score · ${p.opportunity_score}/100</strong>\n'
 '        ${tierExplain}\n'
 '      </div>\n'
 '    </div>',
 '<div class="score-callout">\n'
 '      <div class="gauge ${ct}" id="scoreGauge" data-score="${Math.max(0,Math.min(100,p.opportunity_score))}" style="--val:0">\n'
 '        <div class="g-tick"></div>\n'
 '        <div style="position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;">\n'
 '          <span class="g-num">0</span><span class="g-max">/ 100</span>\n'
 '        </div>\n'
 '      </div>\n'
 '      <div class="score-info">\n'
 '        <strong>Route Match Score</strong>\n'
 '        ${tierExplain}\n'
 '      </div>\n'
 '    </div>',
 1, "score-gauge")

# 3b) score breakdown factor rows get animated instrument fill-bars
sub('<strong>Proximity</strong> — ${p.distance_to_nearest} mi from ${escapeHtml(p.nearest_customer)} (${escapeHtml(p.nearest_customer_city)}).\n        </div>',
    '<strong>Proximity</strong> — ${p.distance_to_nearest} mi from ${escapeHtml(p.nearest_customer)} (${escapeHtml(p.nearest_customer_city)}).\n'
    '          <div class="why-bar dist"><span data-w="${Math.round(Math.min(100,p.score_breakdown.proximity_pts/60*100))}%"></span></div>\n        </div>',
    1, "bar-proximity")
sub("${p.nearby_customer_count} of your customer${p.nearby_customer_count === 1 ? ' is' : 's are'} within 2 miles.\n        </div>",
    "${p.nearby_customer_count} of your customer${p.nearby_customer_count === 1 ? ' is' : 's are'} within 2 miles.\n"
    '          <div class="why-bar density"><span data-w="${Math.round(Math.min(100,p.score_breakdown.density_pts/25*100))}%"></span></div>\n        </div>',
    1, "bar-density")
sub('converts at <strong>${p.score_breakdown.category_fit_pct}%</strong> rate for your trade.\n        </div>',
    'converts at <strong>${p.score_breakdown.category_fit_pct}%</strong> rate for your trade.\n'
    '          <div class="why-bar fit"><span data-w="${Math.round(Math.min(100,p.score_breakdown.category_pts/15*100))}%"></span></div>\n        </div>',
    1, "bar-fit")

# 3c) animate the gauge + bars on open (registered @property drives the sweep)
sub("function showToast(msg) {",
    "function animateGauge(){\n"
    "  var g=document.getElementById('scoreGauge');\n"
    "  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;\n"
    "  var bars=document.querySelectorAll('.why-bar>span');\n"
    "  if(g){\n"
    "    var score=parseInt(g.getAttribute('data-score'))||0;\n"
    "    var num=g.querySelector('.g-num');\n"
    "    if(reduce){ g.style.setProperty('--val',score); if(num) num.textContent=score; }\n"
    "    else {\n"
    "      requestAnimationFrame(function(){ requestAnimationFrame(function(){ g.style.setProperty('--val',score); }); });\n"
    "      var dur=950,t0=performance.now();\n"
    "      (function tick(t){ var p=Math.min(1,(t-t0)/dur), e=1-Math.pow(1-p,3); if(num) num.textContent=Math.round(e*score); if(p<1) requestAnimationFrame(tick); })(t0);\n"
    "    }\n"
    "  }\n"
    "  bars.forEach(function(s){ var w=s.getAttribute('data-w')||'0%'; if(reduce){ s.style.width=w; } else { requestAnimationFrame(function(){ requestAnimationFrame(function(){ s.style.width=w; }); }); } });\n"
    "}\n"
    "function showToast(msg) {",
    1, "animateGauge-fn")

sub("  document.getElementById('leftPanel').scrollTop = 0;\n}",
    "  document.getElementById('leftPanel').scrollTop = 0;\n  animateGauge();\n}",
    2, "animateGauge-call")

# 3d) credits reactor pulses whenever the balance updates (spend feedback)
sub("function updateCreditsChip() {\n"
    "  const el = document.getElementById('creditsBalance');\n"
    "  if (el) el.textContent = atlasCredits;\n"
    "}",
    "function updateCreditsChip() {\n"
    "  const el = document.getElementById('creditsBalance');\n"
    "  if (el) el.textContent = atlasCredits;\n"
    "  const chip = document.getElementById('creditsChip');\n"
    "  if (chip) { chip.classList.remove('pulse'); void chip.offsetWidth; chip.classList.add('pulse'); }\n"
    "}",
    1, "credits-pulse")

# 4) hide the control deck + legend while a detail view is open (2 call sites)
sub(
 "document.getElementById('statsBanner').classList.add('hidden');\n"
 "  document.getElementById('listHeader').classList.add('hidden');\n"
 "  document.getElementById('resultsList').classList.add('hidden');\n"
 "  document.getElementById('detailView').classList.add('active');",
 "document.getElementById('statsBanner').classList.add('hidden');\n"
 "  document.getElementById('listHeader').classList.add('hidden');\n"
 "  document.getElementById('resultsList').classList.add('hidden');\n"
 "  document.getElementById('controlDeck').classList.add('hidden');\n"
 "  document.getElementById('inlineLegend').classList.add('hidden');\n"
 "  document.getElementById('detailView').classList.add('active');",
 2, "detail-hide")

sub(
 "document.getElementById('statsBanner').classList.remove('hidden');\n"
 "  document.getElementById('listHeader').classList.remove('hidden');\n"
 "  document.getElementById('resultsList').classList.remove('hidden');\n"
 "  document.getElementById('detailView').classList.remove('active');",
 "document.getElementById('statsBanner').classList.remove('hidden');\n"
 "  document.getElementById('listHeader').classList.remove('hidden');\n"
 "  document.getElementById('resultsList').classList.remove('hidden');\n"
 "  document.getElementById('controlDeck').classList.remove('hidden');\n"
 "  document.getElementById('inlineLegend').classList.remove('hidden');\n"
 "  document.getElementById('detailView').classList.remove('active');",
 1, "detail-show")

# 5) kill the leftover light background inside the customer detail
sub('style="background:#fafbfc;border-bottom:none;"',
    'style="background:rgba(255,255,255,.02);border-bottom:none;"', 1, "customer-bg")

# 6) dark-tuned category palette + fix the Banks icon (was 'building', which ICONS lacks)
sub(
 "const CATEGORIES = {\n"
 "  'Gas Stations':      { color:'#ef4444', icon:'fuel'       },\n"
 "  'Hotels':            { color:'#3b82f6', icon:'hotel'      },\n"
 "  'Restaurants':       { color:'#f59e0b', icon:'utensils'   },\n"
 "  'Banks':             { color:'#10b981', icon:'building'   },\n"
 "  'Schools':           { color:'#8b5cf6', icon:'school'     },\n"
 "  'Shopping Centers':  { color:'#ec4899', icon:'shopping'   },\n"
 "  'Apartments':        { color:'#06b6d4', icon:'apartment'  },\n"
 "  'Hospitals':         { color:'#dc2626', icon:'hospital'   },\n"
 "  'Auto Dealerships':  { color:'#7c3aed', icon:'car'        },\n"
 "  'Self-Storage':      { color:'#64748b', icon:'storage'    },\n"
 "  'Churches':          { color:'#a16207', icon:'church'     },\n"
 "};",
 "const CATEGORIES = {\n"
 "  'Gas Stations':      { color:'#ff7a3d', icon:'fuel'       },\n"
 "  'Hotels':            { color:'#4d9bff', icon:'hotel'      },\n"
 "  'Restaurants':       { color:'#ffa02e', icon:'utensils'   },\n"
 "  'Banks':             { color:'#2dd4a7', icon:'bank'       },\n"
 "  'Schools':           { color:'#a78bff', icon:'school'     },\n"
 "  'Shopping Centers':  { color:'#ff6fb3', icon:'shopping'   },\n"
 "  'Apartments':        { color:'#22d3ee', icon:'apartment'  },\n"
 "  'Hospitals':         { color:'#ff4d6a', icon:'hospital'   },\n"
 "  'Auto Dealerships':  { color:'#8b7dff', icon:'car'        },\n"
 "  'Self-Storage':      { color:'#93a3bd', icon:'storage'    },\n"
 "  'Churches':          { color:'#cf9646', icon:'church'     },\n"
 "};",
 1, "categories")

# 7) light theme wants a light basemap — swap CARTO dark tiles for Positron (light)
sub("cartocdn.com/dark_all/", "cartocdn.com/light_all/", 1, "light-basemap")

OUT.write_text(html)
print(f"built -> {OUT}  ({len(html)} bytes)")
