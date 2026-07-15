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

# 7b) demo starting balance -> 5000 IQC (enough to exercise everything incl. Full City Sweep)
sub("let atlasCredits = 180;", "let atlasCredits = 5000;", 1, "credits-5000")
# the IQ-credits chip moves into the QuoteIQ universal header (built in step 11) — drop it from the Atlas toolbar
sub('    <!-- ATLAS: IQ Credits chip (demo starts intentionally low at 180 so the paywall is hit in a walkthrough) -->\n'
    '    <div class="credits-chip" id="creditsChip" title="IQ Credits — demo balance"><span id="creditsBalance">180</span>&nbsp;IQC</div>\n',
    '', 1, "remove-topbar-credits")

# ---------------------------------------------------------------------------
# 8) "Your customers" -> person silhouette (keep the green outline)
CHECK_DEF = ("  check:     '<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" "
             "stroke-width=\"3\"><path d=\"M20 6 9 17l-5-5\"/></svg>',")
sub(CHECK_DEF, CHECK_DEF + "\n"
    "  person:    '<svg viewBox=\"0 0 24 24\" fill=\"currentColor\"><path d=\"M12 12a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9zm0 2.25c-3.87 0-7 2.02-7 4.5V21h14v-2.25c0-2.48-3.13-4.5-7-4.5z\"/></svg>',",
    1, "icon-person")

# customer map pin
sub('class="pin-customer" data-idx="${idx}" style="${isSelected ? \'transform:scale(1.2);box-shadow:0 4px 16px rgba(16,185,129,.6);\' : \'\'}">${ICONS.check}</div>',
    'class="pin-customer" data-idx="${idx}" style="${isSelected ? \'transform:scale(1.2);box-shadow:0 4px 16px rgba(16,185,129,.6);\' : \'\'}">${ICONS.person}</div>',
    1, "customer-pin-person")

# legend swatch
sub('<span class="ll-dot ll-cust"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg></span> Your customers',
    '<span class="ll-dot ll-cust"><svg width="10" height="10" viewBox="0 0 24 24" fill="#12b981"><path d="M12 12a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9zm0 2.25c-3.87 0-7 2.02-7 4.5V21h14v-2.25c0-2.48-3.13-4.5-7-4.5z"/></svg></span> Your customers',
    1, "legend-person")

# customer detail strip
sub('color:#fff;"><div style="width:20px;height:20px;">${ICONS.check}</div></div>',
    'color:#fff;"><div style="width:20px;height:20px;">${ICONS.person}</div></div>',
    1, "customer-strip-person")

# ---------------------------------------------------------------------------
# 9) HELP / GUIDE — floating "?" button + full walkthrough modal
_close = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
IC = {
 "overview": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="16.2 7.8 14.1 14.1 7.8 16.2 9.9 9.9 16.2 7.8"/></svg>',
 "credits":  '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z"/></svg>',
 "pull":     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
 "score":    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
 "mapkey":   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 7-8 13-8 13s-8-6-8-13a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>',
 "work":     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.1 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7 12.8 12.8 0 0 0 .7 2.8 2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4 12.8 12.8 0 0 0 2.8.7 2 2 0 0 1 1.7 2z"/></svg>',
 "mymap":    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9.5 12 3l9 6.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/></svg>',
 "filter":   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>',
 "routes":   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/></svg>',
}
NAV = [
 ("overview","What is Atlas?"),("credits","IQ Credits"),("pull","Pull prospects"),
 ("score","Route Match Score"),("mapkey","Reading the map"),("work","Work a lead"),
 ("mymap","My Map & door knocks"),("filter","Filter, sort & search"),("routes","Routes & pipeline"),
]
nav_html = "".join(
 f'<a data-help="{k}" onclick="helpGo(\'help-{k}\')"><span class="hn-ico">{IC[k]}</span>{label}</a>'
 for k,label in NAV)

def sec(k, title, inner):
    return (f'<section class="help-sec" id="help-{k}"><h3><span class="hs-ico">{IC[k]}</span>{title}</h3>{inner}</section>')

# door-knock status swatches
_knocks = [("#b7c2cc","Not Home"),("#e0b64f","Knocked — No Answer"),("#4cc3e0","Contacted"),
           ("#a3e635","Interested — Follow Up"),("#5b6570","Not Interested"),
           ("#ef5b6e","Do Not Knock  (✕)"),("#f2b148","Appointment Set")]
knock_grid = '<div class="hstatus-grid">' + "".join(
  f'<div class="hstatus"><span class="dot" style="background:{c}"></span>{n}</div>' for c,n in _knocks) + '</div>'

HELP_HTML = f'''
<!-- HELP / GUIDE -->
<div class="help-overlay" id="helpOverlay" onclick="if(event.target===this)closeHelp()">
  <div class="help-modal" role="dialog" aria-label="How Atlas works">
    <div class="help-rail">
      <div class="help-rail-head">
        <div class="hk"><span class="qiq-cube">Q</span> How Atlas works</div>
        <p>A quick guide to finding, scoring and winning commercial leads on the map.</p>
      </div>
      <nav class="help-nav" id="helpNav">{nav_html}</nav>
    </div>
    <div class="help-body">
      <div class="help-body-head">
        <h2>Atlas — the field guide</h2>
        <button class="help-close" onclick="closeHelp()" aria-label="Close">{_close}</button>
      </div>
      <div class="help-scroll" id="helpScroll">
        {sec("overview","What is Atlas?",
          '<p>Atlas turns the map into a <strong>lead machine</strong>. Pull real local businesses onto the map, '
          'see which ones best fit the routes you <em>already</em> drive, work them, and convert them into customers.</p>'
          '<p>There are two layers on one map:</p>'
          '<ul>'
          '<li><strong>My Map</strong> — your existing customers &amp; jobs, plus door-knock pins you drop yourself.</li>'
          '<li><strong>Prospects</strong> — commercial leads you pull by category (restaurants, hotels, gas stations…). '
          'Each one is scored on how well it fits your business.</li>'
          '</ul>'
          '<div class="help-card"><div class="hc-t">The 30-second version</div>'
          'Pull a category → the best-fit businesses light up on the map → tap one to see why it scores well, '
          'call it, save it, or add it to your pipeline.</div>')}
        {sec("credits","IQ Credits — your prospecting fuel",
          '<p>Pulling real business data costs <strong>IQ Credits (IQC)</strong> — your balance sits at the '
          'top-right <span class="hcost">⚡ IQC</span> chip. Everything you do with your <em>own</em> data '
          '(customers, notes, door knocks, pipeline) is always free.</p>'
          '<ul>'
          '<li><span class="hcost">50 IQC</span> &nbsp;<strong>Pull a category</strong> — loads up to ~60 businesses in view.</li>'
          '<li><span class="hcost">+25 IQC</span> &nbsp;<strong>Load more</strong> — the next batch of results for a category.</li>'
          '<li><span class="hcost">400 IQC</span> &nbsp;<strong>Full City Sweep</strong> — pull all 11 categories in the current view at once.</li>'
          '<li><span class="hcost">10 IQC</span> &nbsp;<strong>Reveal contact info</strong> — a prospect’s phone &amp; website.</li>'
          '<li><span class="hcost free">FREE</span> &nbsp;Contact info is <strong>included free</strong> when you Save a prospect to Contacts.</li>'
          '<li><span class="hcost free">FREE</span> &nbsp;Re-showing categories you’ve <strong>already pulled</strong> — that’s just a view toggle, no fetch, no charge.</li>'
          '</ul>'
          '<p>If you don’t have enough, the credits chip gives a shake and nothing is charged — top up and try again.</p>')}
        {sec("pull","Pulling prospects onto the map",
          '<p>Open the <strong>“Atlas · Prospects”</strong> deck at the top of the left panel. Each category chip '
          '(Restaurants, Hotels, Gas Stations, Banks, Schools, Shopping Centers, Apartments, Hospitals, Auto '
          'Dealerships, Self-Storage, Churches) starts <strong>locked</strong> with a <span class="hcost">50 IQC</span> price.</p>'
          '<div class="help-card"><div class="hc-t">The golden rule</div>'
          'Every pull is bounded <strong>two ways at once</strong>: the <strong>map area you’re viewing</strong> and a hard cap '
          'of <strong>60 businesses per category</strong>. Atlas never pulls the whole world — pan / zoom to the neighbourhood '
          'you want, then pull.</div>'
          '<ul>'
          '<li><strong>Tap a locked chip</strong> to pull it — the in-view businesses drop as pins and the list fills with ranked results.</li>'
          '<li>Got the full 60 and want more of the same category here? Tap <span class="hcost">+25 IQC</span> on the chip to load the next batch in the same area.</li>'
          '<li>Once pulled, the chip toggles that layer <strong>on / off for free</strong> — re-showing it never costs credits.</li>'
          '<li><strong>Full City Sweep</strong> <span class="hcost">400 IQC</span> pulls <strong>all 11 categories in the current view</strong> in one go.</li>'
          '<li>Pull as many categories as you like — they stack on the same map, colour-coded.</li>'
          '</ul>')}
        {sec("score","Route Match Score (0–100)",
          '<p>Every prospect gets a <strong>Route Match Score</strong> — how well it fits <em>your</em> business, '
          'not generic popularity. It’s built from three real signals:</p>'
          '<div class="hbars">'
          '<div class="hbar"><span class="hb-l">Proximity</span><div class="hb-track"><div class="hb-fill" style="width:100%;background:linear-gradient(90deg,#0ea371,#12b981)"></div></div><span class="hb-max">/ 60</span></div>'
          '<div class="hbar"><span class="hb-l">Customer density</span><div class="hb-track"><div class="hb-fill" style="width:42%;background:linear-gradient(90deg,#2f6fd0,#3b82f6)"></div></div><span class="hb-max">/ 25</span></div>'
          '<div class="hbar"><span class="hb-l">Category fit</span><div class="hb-track"><div class="hb-fill" style="width:25%;background:linear-gradient(90deg,#7c5cf0,#a78bff)"></div></div><span class="hb-max">/ 15</span></div>'
          '</div>'
          '<ul>'
          '<li><strong>Proximity</strong> — how close it is to your nearest customer.</li>'
          '<li><strong>Customer density</strong> — how many of your customers sit within 2 miles.</li>'
          '<li><strong>Category fit</strong> — how well that category historically converts for your trade.</li>'
          '</ul>'
          '<p>Open any prospect to see its <strong>“How this score was calculated”</strong> breakdown. Star ratings and '
          'review counts are shown for context but do <strong>not</strong> affect the score.</p>'
          '<p>Prospects are then tiered <em>relative to what’s on screen</em>:</p>'
          '<div class="hlegend">'
          '<div class="hlegend-row"><span class="hswatch" style="background:var(--green-tint);color:var(--green-hi);font-weight:800">A</span><div><strong>Excellent fit</strong> — top ~20%. Chase these first.</div></div>'
          '<div class="hlegend-row"><span class="hswatch" style="background:var(--gold-tint);color:var(--gold-lo);font-weight:800">B</span><div><strong>Strong fit</strong> — next ~30%. Worth a sales call.</div></div>'
          '<div class="hlegend-row"><span class="hswatch" style="background:var(--surface-3);color:var(--ink-3);font-weight:800">C</span><div><strong>Skip for now</strong> — outside your routes.</div></div>'
          '</div>')}
        {sec("mapkey","Reading the map",
          '<div class="hlegend">'
          '<div class="hlegend-row"><span class="hswatch round" style="background:#fff;border:2px solid #12b981"><svg width="13" height="13" viewBox="0 0 24 24" fill="#12b981"><path d="M12 12a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9zm0 2.2c-3.9 0-7 2-7 4.5V21h14v-2.3c0-2.5-3.1-4.5-7-4.5z"/></svg></span><div><strong>Your customer</strong> — white circle with a green ring.</div></div>'
          '<div class="hlegend-row"><span class="hswatch round" style="background:#fff;border:2px solid #ffa02e;position:relative"><span style="position:absolute;top:-3px;right:-3px;width:9px;height:9px;border-radius:50%;background:#12b981;border:2px solid #fff"></span></span><div><strong>Prospect pin</strong> — coloured by category. A <span style="color:#12b981;font-weight:700">green dot</span> = high opportunity (it gently pulses); a <span style="color:#d9861a;font-weight:700">gold dot</span> = medium.</div></div>'
          '<div class="hlegend-row"><span class="hswatch diamond" style="background:#fff;border:3px solid #f2b148"></span><div><strong>Door knock</strong> — a diamond, coloured by its status.</div></div>'
          '<div class="hlegend-row"><span class="hswatch round" style="background:#0d1220;color:#fff;font-weight:800;font-size:11px">12</span><div><strong>Cluster</strong> — many pins grouped together. Zoom in (or click) to split it.</div></div>'
          '<div class="hlegend-row"><span class="hswatch round" style="background:rgba(18,185,129,.12);border:2px dashed #12b981"></span><div><strong>Service zone</strong> — a dashed ~2-mile ring around each of your customer clusters.</div></div>'
          '</div>'
          '<p>Tap a pin (or its card in the list) to open the full detail view. Use <strong>“What’s near me?”</strong> '
          '(bottom-right) to jump to your location.</p>')}
        {sec("work","Working a lead",
          '<p>Tap any prospect to open its detail panel. From there you can:</p>'
          '<ul>'
          '<li><strong>Call Now</strong> — one tap to dial (once the phone is known).</li>'
          '<li><strong>Save to Contacts</strong> — turns the prospect into <em>your</em> record. Its contact info comes '
          'free, the pin gets a green ring, and it stays on the map regardless of filters.</li>'
          '<li><strong>Add to Pipeline</strong> — queues it as a lead. <strong>No outreach is ever sent automatically.</strong></li>'
          '<li><strong>AI Intro</strong> — draft a tailored email, text, or call script in one click.</li>'
          '<li><strong>Mark Contacted</strong> &amp; <strong>Notes</strong> — track your progress; notes auto-save.</li>'
          '</ul>')}
        {sec("mymap","My Map &amp; door knocks",
          '<p>The <strong>My Map</strong> toggles in the deck control your own data:</p>'
          '<ul>'
          '<li><strong>Customers &amp; Jobs</strong> — show/hide your existing customer pins.</li>'
          '<li><strong>Door Knocks</strong> — show/hide the doors you’ve logged.</li>'
          '</ul>'
          '<p>Tap <span class="hkey">+ Drop a pin</span> (top-right of the map), then tap anywhere on the map to log a '
          'door — it creates a lightweight contact record, not a stray map dot. Open any knock to set its status:</p>'
          + knock_grid)}
        {sec("filter","Filter, sort &amp; search",
          '<ul>'
          '<li><strong>Tier chips</strong> — <span class="hkey">All</span> <span class="hkey">Excellent</span> '
          '<span class="hkey">Strong</span> <span class="hkey">Skip</span> narrow the map and list to a fit level.</li>'
          '<li><strong>Category chips</strong> — toggle each pulled category on or off.</li>'
          '<li><strong>Sort</strong> — by Opportunity Score, distance to your nearest customer, or highest rated.</li>'
          '<li><strong>Show my customers</strong> — overlay your customers alongside prospects.</li>'
          '<li><strong>Search</strong> — the box up top filters by business name or city.</li>'
          '</ul>')}
        {sec("routes","Routes &amp; pipeline",
          '<ul>'
          '<li><strong>Route Builder</strong> (the route icon, top-right) — pick a day, an area, and how many customer '
          '+ prospect stops. Atlas builds an optimised loop and can open it straight in Google Maps.</li>'
          '<li><strong>Pipeline</strong> — the green pill appears once you add prospects. Open it to review everything '
          'you’ve queued and send it all to your QuoteIQ Pipelines in one go.</li>'
          '</ul>'
          '<div class="help-card tip"><div class="hc-t">Pro tip</div>'
          'Pull one category near your customers, sort by <strong>Opportunity</strong>, and work the '
          '<strong>Excellent</strong> tier first while you’re already in the area. Save the winners to Contacts so they’re yours to keep.</div>')}
      </div>
    </div>
  </div>
</div>

<script id="atlas-help">
function openHelp(){{ var o=document.getElementById('helpOverlay'); o.classList.add('show'); helpSpy(); }}
function closeHelp(){{ document.getElementById('helpOverlay').classList.remove('show'); }}
function helpGo(id){{ var el=document.getElementById(id); if(el) el.scrollIntoView({{behavior:'smooth',block:'start'}}); }}
function helpSpy(){{
  var sc=document.getElementById('helpScroll'); if(!sc) return;
  var secs=[].slice.call(sc.querySelectorAll('.help-sec'));
  var top=sc.scrollTop, best=secs[0], bd=1e9;
  secs.forEach(function(s){{ var d=Math.abs(s.offsetTop-sc.offsetTop-top); if(d<bd){{bd=d;best=s;}} }});
  document.querySelectorAll('#helpNav a').forEach(function(a){{
    a.classList.toggle('active', best && a.getAttribute('data-help')===best.id.replace('help-',''));
  }});
}}
(function(){{
  var sc=document.getElementById('helpScroll'); if(sc) sc.addEventListener('scroll', helpSpy, {{passive:true}});
  document.addEventListener('keydown', function(e){{ if(e.key==='Escape') closeHelp(); }});
}})();
</script>
'''

sub('\n<script id="atlas-layer">', HELP_HTML + '\n<script id="atlas-layer">', 1, "help-modal")

# floating "?" button, bottom-left of the map
sub('<div class="map-wrap">\n    <div id="map"></div>',
    '<div class="map-wrap">\n    <div id="map"></div>\n\n'
    '    <!-- HELP: floating guide button (bottom-left) -->\n'
    '    <button class="help-fab" onclick="openHelp()" aria-label="How Atlas works">?'
    '<span class="help-tip">How Atlas works</span></button>',
    1, "help-fab")

# ---------------------------------------------------------------------------
# 10) PULL OPERATING SPEC — make the demo's Pull obey the spec's observable rules:
#     viewport-bounded + 60-cap pulls, free "All" view, +25 load-more, 400-IQC
#     Full City Sweep, and "locations only" (phone/website lazily revealed).

# gate every render path on a per-prospect "_loaded" flag (set by a pull)
sub(".filter(({ p }) => activeFilters.has(p.category))",
    ".filter(({ p }) => activeFilters.has(p.category) && p._loaded)",
    2, "gate-loaded-filters")               # computeTiers + renderList
sub("if (!activeFilters.has(p.category)) return;",
    "if (!activeFilters.has(p.category) || !p._loaded) return;",
    1, "gate-loaded-markers")               # renderMarkers (saved contacts still bypass)

# customer "nearby prospects" only surfaces what's been pulled
sub(".filter(x => x.dist <= 2.0)",
    ".filter(x => x.dist <= 2.0 && x.p._loaded)",
    1, "gate-loaded-nearby")

# route builder only routes over pulled prospects
sub("&& (unlockedCategories.has(x.p.category) || savedContacts.has(x.idx)))",
    "&& (x.p._loaded || savedContacts.has(x.idx)))",
    1, "gate-loaded-route")

# §2/§6 locations only: phone/website hidden until Reveal (10 IQC) or Save (free)
sub("const _rev = revealedContacts.get(idx);\n"
    "  const effPhone = p.phone || (_rev ? _rev.phone : '');\n"
    "  const effWebsite = p.website || (_rev ? _rev.website : '');",
    "const _rev = revealedContacts.get(idx);\n"
    "  const _hasContact = !!_rev || savedContacts.has(idx); // PULL SPEC §2: pulls return locations only\n"
    "  const effPhone = _hasContact ? (p.phone || (_rev ? _rev.phone : '')) : '';\n"
    "  const effWebsite = _hasContact ? (p.website || (_rev ? _rev.website : '')) : '';",
    1, "locations-only")

# add the Full City Sweep button at the end of the category chips
sub("    chip.onclick = () => handleCategoryChipClick(name, chip);\n    wrap.appendChild(chip);\n  });\n}",
    "    chip.onclick = () => handleCategoryChipClick(name, chip);\n    wrap.appendChild(chip);\n  });\n"
    "\n  // PULL SPEC §3: Full City Sweep — pull all 11 categories in view at once (400 IQC)\n"
    "  if (typeof addSweepButton === 'function') addSweepButton(wrap);\n}",
    1, "sweep-in-chips")

PULL_SCRIPT = r'''
<script id="atlas-pull-spec">
/* ============================================================
   PULL OPERATING SPEC — front-end-observable behaviour.
   Every pull is bounded by (a) the current map viewport and
   (b) a hard cap of 60 results per category. There is no
   unbounded "fetch everything" path. Backend concerns (real
   Places API, server-side key, Firestore 30-day TTL, per-hour
   abuse brake, audit ledger, name+address dedupe) live on the
   server — see ATLASPULLSPEC.md; they cannot run in a static demo.
   ============================================================ */
const PULL_CAP = 60;                 // §1 hard cap per category per pull (3 pages x 20)
const PULL_PRICE = 50;               // §1
const LOADMORE_PRICE = 25;           // §4
const SWEEP_PRICE = 400;             // §3 Full City Sweep

// §10 category -> Places (New) includedType (server-side config; shown here for reference)
const PLACES_TYPE_MAP = {
  'Restaurants':'restaurant','Hotels':'lodging','Gas Stations':'gas_station','Banks':'bank',
  'Schools':'school','Hospitals':'hospital','Churches':'church','Shopping Centers':'shopping_mall',
  'Auto Dealerships':'car_dealer','Apartments':'apartment_complex','Self-Storage':'storage'
};

// nothing is "on the map" until it is pulled
PROSPECTS.forEach(function(p){ p._loaded = false; });

function inCurrentBounds(p){ return !map || map.getBounds().contains([p.lat, p.lng]); }

// pick up to `limit` in-bounds, not-yet-loaded prospects of a category
// (ordered by opportunity as a stand-in for Places text-search relevance)
function pickPullBatch(cat, limit){
  return PROSPECTS
    .map(function(p, idx){ return { p: p, idx: idx }; })
    .filter(function(x){ return x.p.category === cat && !x.p._loaded && inCurrentBounds(x.p); })
    .sort(function(a, b){ return b.p.opportunity_score - a.p.opportunity_score; })
    .slice(0, limit)
    .map(function(x){ return x.idx; });
}
function inBoundsRemaining(cat){
  return PROSPECTS.filter(function(p){ return p.category === cat && !p._loaded && inCurrentBounds(p); }).length;
}

// §1 a category pull is viewport-bounded, capped at 60, costs 50 IQC.
// §5 check balance first; never partially unlock; deduct then "fetch".
function handleCategoryChipClick(name, chipEl){
  if (pullingCategories.has(name)) return;
  if (!unlockedCategories.has(name)){
    if (atlasCredits < PULL_PRICE){ creditFail(); return; }        // §5 not-enough-credits
    var batch = pickPullBatch(name, PULL_CAP);
    atlasCredits -= PULL_PRICE; updateCreditsChip();
    pullingCategories.add(name); renderChips();
    setTimeout(function(){
      pullingCategories.delete(name);
      unlockedCategories.add(name); activeFilters.add(name);
      batch.forEach(function(i){ PROSPECTS[i]._loaded = true; });
      window.__staggerCat = name;
      renderChips(); renderList();
      setTimeout(function(){ window.__staggerCat = null; }, 1200);
      showToast(batch.length
        ? ('Pulled ' + batch.length + ' ' + name + ' in this area — ' + PULL_PRICE + ' IQC')
        : ('No ' + name + ' in this map area — pan or zoom out and try again'));
    }, 800);
  } else {
    // §3 already pulled -> free on/off VIEW toggle (no fetch, no credits)
    if (activeFilters.has(name)) activeFilters.delete(name); else activeFilters.add(name);
    renderChips(); renderList();
  }
}

// §4 Load more = a new bounded pull, +60 increment, 25 IQC, same category & area
function loadMoreCategory(name, ev){
  if (ev) ev.stopPropagation();
  if (inBoundsRemaining(name) === 0){ showToast('No more ' + name + ' in this area — pan or zoom out'); return; }
  if (atlasCredits < LOADMORE_PRICE){ creditFail(); return; }
  var batch = pickPullBatch(name, PULL_CAP);
  atlasCredits -= LOADMORE_PRICE; updateCreditsChip();
  batch.forEach(function(i){ PROSPECTS[i]._loaded = true; });
  window.__staggerCat = name;
  renderChips(); renderList();
  setTimeout(function(){ window.__staggerCat = null; }, 1200);
  showToast('Loaded ' + batch.length + ' more ' + name + ' — ' + LOADMORE_PRICE + ' IQC');
}

// §3 Full City Sweep — all 11 categories in the CURRENT viewport at once, 400 IQC
function fullCitySweep(){
  if (atlasCredits < SWEEP_PRICE){ creditFail(); return; }
  atlasCredits -= SWEEP_PRICE; updateCreditsChip();
  var total = 0;
  Object.keys(CATEGORIES).forEach(function(name){
    var batch = pickPullBatch(name, PULL_CAP);
    batch.forEach(function(i){ PROSPECTS[i]._loaded = true; });
    if (batch.length){ unlockedCategories.add(name); activeFilters.add(name); total += batch.length; }
  });
  renderChips(); renderList();
  showToast('Full City Sweep — ' + total + ' prospects across ' + Object.keys(CATEGORIES).length + ' categories · ' + SWEEP_PRICE + ' IQC');
}

function addSweepButton(wrap){
  var b = document.createElement('button');
  b.className = 'sweep-btn';
  b.innerHTML = '<span class="sweep-ic">⚡</span> Full City Sweep <span class="sweep-price">400 IQC</span>';
  b.title = 'Pull all 11 categories in the current map area at once';
  b.onclick = fullCitySweep;
  wrap.appendChild(b);
}

// refresh chips so the sweep button appears, and clear the (now unpulled) list
renderChips();
if (typeof renderList === 'function') renderList();
</script>
'''

sub("\n</body>", PULL_SCRIPT + "\n</body>", 1, "pull-spec-script")

# ---------------------------------------------------------------------------
# 11) QUOTEIQ DESKTOP SHELL — consolidated icon rail + universal header
S = {  # 24x24 stroke icons
 "burger":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>',
 "plus":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
 "sparkle":'<svg viewBox="0 0 24 24" fill="currentColor"><path d="m12 2 2.2 5.8L20 10l-5.8 2.2L12 18l-2.2-5.8L4 10l5.8-2.2z"/></svg>',
 "home":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9.5 12 3l9 6.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/></svg>',
 "users":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
 "briefcase":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
 "inbox":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 21h8M12 18v3"/></svg>',
 "phone":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.1 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7 12.8 12.8 0 0 0 .7 2.8 2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4 12.8 12.8 0 0 0 2.8.7 2 2 0 0 1 1.7 2z"/></svg>',
 "megaphone":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 11v2a1 1 0 0 0 1 1h2l5 4V6L6 10H4a1 1 0 0 0-1 1z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/></svg>',
 "book":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
 "logout":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
 "help":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12" y2="17"/></svg>',
 "gear":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
 "chev":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="6 9 12 15 18 9"/></svg>',
 "bolt":'<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z"/></svg>',
 # header nav
 "calendar":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
 "clipboard":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>',
 "filetext":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
 "receipt":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 2v20l2.5-1.5L9 22l3-1.5L15 22l2.5-1.5L20 22V2l-2.5 1.5L15 2l-3 1.5L9 2 6.5 3.5z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/></svg>',
 "map":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 8 3 16 6 23 3 23 18 16 21 8 18 1 21"/><line x1="8" y1="3" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="21"/></svg>',
 "cam":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
 "bell":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>',
 "account":'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 12 0v1"/></svg>',
}

def rail_item(key, icon, label, sub="", badge="", chev=False):
    ex = ""
    if badge: ex += badge
    if chev:  ex += '<span class="qi-chev">' + S["chev"] + '</span>'
    return ('<button class="qiq-item" data-tip="' + label + '" onclick="qiqStub(\'' + label + '\')">'
            '<span class="qi-ico">' + icon + '</span><span class="qi-label">' + label + '</span>' + ex + '</button>' + sub)

CRM_SUB = ('<div class="qiq-sub">'
  '<a class="active" onclick="qiqStub(\'Contacts\')">Contacts</a>'
  '<a onclick="qiqStub(\'Jobs\')">Jobs</a>'
  '<a onclick="qiqStub(\'Estimates\')">Estimates</a>'
  '<a onclick="qiqStub(\'Invoices\')">Invoices</a>'
  '<a onclick="qiqStub(\'Expenses\')">Expenses</a>'
  '<a onclick="qiqStub(\'Price Book\')">Price Book (Services)</a>'
  '<a onclick="qiqStub(\'Client Portal\')">Client Portal</a>'
  '</div>')

RAIL_NAV = (
  rail_item("create", S["plus"], "Create")
  + rail_item("ai", S["sparkle"], "AI AutoPilot", badge='<span class="qi-badge">NEW</span>')
  + rail_item("dash", S["home"], "Dashboard")
  + rail_item("crm", S["users"], "CRM", sub=CRM_SUB, chev=True)
  + rail_item("tools", S["briefcase"], "Tools", chev=True)
  + rail_item("inbox", S["inbox"], "Inbox", badge='<span class="qi-badge count">2</span>', chev=True)
  + rail_item("phone", S["phone"], "Phone", chev=True)
  + rail_item("emp", S["users"], "Employees", chev=True)
  + rail_item("mkt", S["megaphone"], "Marketing")
  + rail_item("academy", S["book"], "Academy")
)
RAIL_FOOT = (
  rail_item("logout", S["logout"], "Log out")
  + rail_item("support", S["help"], "Contact Support")
)

NAVBAR = [("Home",S["home"]),("Calendar",S["calendar"]),("Jobs",S["clipboard"]),("Estimates",S["filetext"]),
          ("Invoices",S["receipt"]),("Map",S["map"]),("Cam",S["cam"])]
nav_html = "".join(
  '<a class="' + ("active" if n=="Map" else "") + '" onclick="qiqNav(\'' + n + '\')">' + ic + n + '</a>'
  for n,ic in NAVBAR)

SHELL_OPEN = (
'<div class="qiq-shell">\n'
'  <aside class="qiq-rail" id="qiqRail">\n'
'    <div class="qiq-rail-head">\n'
'      <span class="qiq-elite">' + S["sparkle"] + 'ELITE</span>\n'
'      <button class="qiq-burger" onclick="qiqToggleRail()" aria-label="Toggle menu">' + S["burger"] + '</button>\n'
'    </div>\n'
'    <div class="qiq-company">\n'
'      <span class="co-logo">AA</span>\n'
'      <span class="co-name"><b>All American Clean</b><span>cleansavannah.com</span></span>\n'
'      <button class="co-gear" onclick="qiqStub(\'Settings\')">' + S["gear"] + '</button>\n'
'    </div>\n'
'    <button class="qiq-addco" onclick="qiqStub(\'Add Company\')">' + S["plus"] + ' Add Company</button>\n'
'    <div class="qiq-rail-nav">' + RAIL_NAV + '</div>\n'
'    <div class="qiq-rail-foot">' + RAIL_FOOT + '</div>\n'
'  </aside>\n'
'  <div class="qiq-body">\n'
'    <header class="qiq-header">\n'
'      <nav class="qiq-nav">' + nav_html + '</nav>\n'
'      <div class="qiq-head-right">\n'
'        <div class="credits-chip" id="creditsChip" title="IQ Credits"><span id="creditsBalance">5000</span><span class="cred-boost">' + S["sparkle"] + '</span></div>\n'
'        <button class="qiq-iconbtn" onclick="qiqStub(\'Notifications\')" aria-label="Notifications">' + S["bell"] + '<span class="qiq-badge">99+</span></button>\n'
'        <button class="qiq-iconbtn" onclick="qiqStub(\'Account\')" aria-label="Account">' + S["account"] + '</button>\n'
'      </div>\n'
'    </header>\n'
)

sub("<!-- TOP BAR -->", SHELL_OPEN + "\n<!-- TOP BAR -->", 1, "shell-open")
sub("\n<!-- TOAST -->", "\n  </div><!-- /qiq-body -->\n</div><!-- /qiq-shell -->\n\n<!-- TOAST -->", 1, "shell-close")

QIQ_SCRIPT = r'''
<script id="qiq-shell-js">
function qiqToggleRail(){
  var r = document.getElementById('qiqRail'); if (!r) return;
  r.classList.toggle('expanded');
  setTimeout(function(){ if (typeof map !== 'undefined' && map) map.invalidateSize(); }, 260);
}
function qiqNav(name){
  if (name === 'Map') return;                 // Atlas IS the Map section
  if (typeof showToast === 'function') showToast('Demo — this is Atlas, the Map section of QuoteIQ');
}
function qiqStub(name){
  if (typeof showToast === 'function') showToast(name + ' lives in the full QuoteIQ app — this demo is the Map (Atlas) section');
}
// keep Leaflet correctly sized inside the shell
setTimeout(function(){ if (typeof map !== 'undefined' && map) map.invalidateSize(); }, 450);
window.addEventListener('resize', function(){ if (typeof map !== 'undefined' && map) map.invalidateSize(); });
</script>
'''
sub("\n</body>", QIQ_SCRIPT + "\n</body>", 1, "shell-js")

OUT.write_text(html)
print(f"built -> {OUT}  ({len(html)} bytes)")
