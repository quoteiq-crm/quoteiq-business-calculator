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

# customer map pin — person icon (blue via CSS) + hover name tag (Section 7)
sub('class="pin-customer" data-idx="${idx}" style="${isSelected ? \'transform:scale(1.2);box-shadow:0 4px 16px rgba(16,185,129,.6);\' : \'\'}">${ICONS.check}</div>',
    'class="pin-customer" data-idx="${idx}" style="${isSelected ? \'transform:scale(1.2);box-shadow:0 4px 16px rgba(16,185,129,.6);\' : \'\'}">${ICONS.person}<span class="pin-name-tag">${escapeHtml(c.name)}</span></div>',
    1, "customer-pin-person")

# legend (Section 1): Customers (blue), Active Jobs (green), High opp (orange), Medium (amber), Lower (gray)
sub('      <span class="ll-item"><span class="ll-dot ll-cust"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg></span> Your customers</span>\n'
    '      <span class="ll-item"><span class="ll-dot ll-high"></span> High opp</span>\n'
    '      <span class="ll-item"><span class="ll-dot ll-med"></span> Medium</span>\n'
    '      <span class="ll-item"><span class="ll-dot ll-low"></span> Lower</span>',
    '      <span class="ll-item"><span class="ll-dot ll-custD"></span> Customers</span>\n'
    '      <span class="ll-item"><span class="ll-dot ll-job"></span> Active Jobs</span>\n'
    '      <span class="ll-item"><span class="ll-dot ll-high"></span> High opp</span>\n'
    '      <span class="ll-item"><span class="ll-dot ll-med"></span> Medium</span>\n'
    '      <span class="ll-item"><span class="ll-dot ll-low"></span> Lower</span>',
    1, "legend-5")

# customer detail strip — person icon + blue disc
sub('color:#fff;"><div style="width:20px;height:20px;">${ICONS.check}</div></div>',
    'color:#fff;"><div style="width:20px;height:20px;">${ICONS.person}</div></div>',
    1, "customer-strip-person")
sub('width:42px;height:42px;border-radius:50%;background:#10b981;display:flex;align-items:center;justify-content:center;flex:none;color:#fff;',
    'width:42px;height:42px;border-radius:50%;background:#2f74f0;display:flex;align-items:center;justify-content:center;flex:none;color:#fff;',
    1, "customer-strip-blue")

# Section 7: remove the QuoteIQ wordmark + "NEW" badge (app already has its own header)
sub('  <div class="logo">\n'
    '    <div class="logo-mark">Q</div>\n'
    '    <span>QuoteIQ</span>\n'
    '    <span class="logo-sub">ATLAS<span class="badge-new">NEW</span></span>\n'
    '  </div>',
    '  <div class="logo"><span class="logo-sub" style="border:none;padding:0;margin:0;letter-spacing:.14em;color:var(--ink-2);">Atlas</span></div>',
    1, "remove-wordmark")

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
          '<li><span class="hcost">50 IQC</span> &nbsp;<strong>Pull a category</strong> — a one-time charge that loads every business of that type in view and keeps the category yours all session.</li>'
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
          'A pull is bounded to the <strong>map area you’re viewing</strong>, and it loads <strong>every business of that type '
          'in that area</strong> — 100% of what Google lists there, not a sample. Pan / zoom to the neighbourhood you want, then pull.</div>'
          '<ul>'
          '<li><strong>Tap a locked chip</strong> to pull it — every in-view business of that type drops as pins and the list fills with ranked results.</li>'
          '<li>Pay <strong>once</strong> — after that the category is <strong>yours for the whole session</strong>. Its chip becomes a free show/hide toggle (marked <strong>Saved</strong>) and is never charged again.</li>'
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

# owned category chip: no price, show a free show/hide "Saved" tag (replaces load-more)
sub('    else                  extra = `<span class="chip-loadmore" title="Load more — next 60 results (25 IQC)" onclick="loadMoreCategory(\'${name}\', event)">+25 IQC</span>`;',
    '    else                  extra = `<span class="chip-saved">${ICONS.eye} Saved</span>`;',
    1, "owned-chip-saved")

# empty-state hint: a pull loads 100% of the category in-area (not "up to 60")
sub("Each category pull costs 50 IQC and loads up to 60 businesses in this area.",
    "Each category pull loads every business of that type in the current map area — 100% of what Google lists there, not a sample.",
    1, "empty-hint-100")

# nothing expires — drop the 30-day expiry line from the prospect action hint
sub("Prospect data expires in 30 days unless saved. Saving creates a contact record — it becomes your data.",
    "Saving creates a contact record — it becomes your data, yours to keep.",
    1, "no-expiry-copy")

# remove the original loadMoreCategory (load-more is gone entirely)
sub("function loadMoreCategory(name, ev) {\n"
    "  if (ev) ev.stopPropagation();\n"
    "  if (atlasCredits < 25) { creditFail(); return; }\n"
    "  atlasCredits -= 25;\n"
    "  updateCreditsChip();\n"
    "  showToast('Demo: full version pulls the next 60 results');\n"
    "}",
    "// (load-more removed — a pull now loads 100% of the category in-area, nothing left to load)",
    1, "remove-loadmore-orig")

PULL_SCRIPT = r'''
<script id="atlas-pull-spec">
/* ============================================================
   PULL OPERATING SPEC — front-end-observable behaviour.
   A category pull is viewport-bounded and loads EVERY business of
   that type in the current map area (100% of what Google lists
   there, not a sample). Pay 50 IQC ONCE and you OWN that category
   for the whole session — toggling its chip only shows/hides pins,
   it is never charged or re-pulled. Backend concerns (real Places
   API, server-side key, Firestore, audit ledger, name+address
   dedupe) live on the server — see ATLASPULLSPEC.md; they cannot
   run in a static demo.
   ============================================================ */
const PULL_PRICE = 50;               // §1 one-time charge to own a category
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

// EVERY in-bounds, not-yet-loaded prospect of a category (100% — no cap)
// ordered by opportunity as a stand-in for Places text-search relevance
function pickPullBatch(cat){
  return PROSPECTS
    .map(function(p, idx){ return { p: p, idx: idx }; })
    .filter(function(x){ return x.p.category === cat && !x.p._loaded && inCurrentBounds(x.p); })
    .sort(function(a, b){ return b.p.opportunity_score - a.p.opportunity_score; })
    .map(function(x){ return x.idx; });
}

// §1 a pull is viewport-bounded and loads 100% of the category; pay 50 IQC ONCE.
// §5 check balance first; never partially unlock; deduct then "fetch".
function handleCategoryChipClick(name, chipEl){
  if (pullingCategories.has(name)) return;
  if (!unlockedCategories.has(name)){                              // not yet owned
    if (atlasCredits < PULL_PRICE){ creditFail(); return; }        // §5 not-enough-credits
    var batch = pickPullBatch(name);
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
    // OWNED for good -> free show/hide toggle. Never charge, re-pull, or show "Pulling…".
    if (activeFilters.has(name)) activeFilters.delete(name); else activeFilters.add(name);
    renderChips(); renderList();
  }
}

// §3 Full City Sweep — all 11 categories in the CURRENT viewport at once, 400 IQC
function fullCitySweep(){
  if (atlasCredits < SWEEP_PRICE){ creditFail(); return; }
  atlasCredits -= SWEEP_PRICE; updateCreditsChip();
  var total = 0;
  Object.keys(CATEGORIES).forEach(function(name){
    var batch = pickPullBatch(name);
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

# ---------------------------------------------------------------------------
# 12) REDESIGN PASS (Sections 2–7 behavior): compact Prospects panel, collapsible
#     panel, lead detail card, Active-Job pins, Create Deal / Task / Reminder modals.
REDESIGN = r'''
<!-- REDESIGN modal shells (filled in JS) -->
<div class="modal-overlay lead-card" id="leadCardModal" onclick="if(event.target===this)closeOverlay('leadCardModal')"><div class="modal" id="leadCardInner"></div></div>
<div class="modal-overlay" id="createDealModal" onclick="if(event.target===this)closeOverlay('createDealModal')"><div class="modal" id="createDealInner"></div></div>
<div class="modal-overlay" id="createTaskModal" onclick="if(event.target===this)closeOverlay('createTaskModal')"><div class="modal" id="createTaskInner"></div></div>
<div class="modal-overlay" id="reminderModal2" onclick="if(event.target===this)closeOverlay('reminderModal2')"><div class="modal" id="reminderInner"></div></div>

<script id="atlas-redesign">
(function(){
const ICO={
 x:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
 nav:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>',
 brief:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
 trash:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m5 0V4a2 2 0 0 1 2-2h0a2 2 0 0 1 2 2v2"/></svg>',
 task:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
 deal:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
 bell:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>',
};

// ---------- Active Jobs (green) ----------
const JOBS=[
 {name:'Bay Street Office Tower — pressure wash', lat:32.0668, lng:-81.0907, when:'Today · 2:00 PM'},
 {name:'Forsyth Park Plaza — monthly', lat:32.0762, lng:-81.0889, when:'Tomorrow · 9:00 AM'},
 {name:'Oglethorpe Mall — lot striping', lat:32.0246, lng:-81.1122, when:'Wed · 7:30 AM'},
 {name:'River Street Group — exterior', lat:32.0811, lng:-81.0902, when:'Thu · 11:00 AM'},
 {name:'Historic Inn at Telfair', lat:32.0803, lng:-81.0925, when:'Fri · 1:00 PM'},
 {name:'Abercorn Commerce Center', lat:32.0146, lng:-81.1098, when:'Mon · 8:00 AM'},
];
window.showJobs=true; let jobMarkers=[];
function renderJobs(){
 jobMarkers.forEach(m=>map.removeLayer(m)); jobMarkers=[];
 if(!window.showJobs||!map) return;
 JOBS.forEach((j)=>{
  const html='<div class="pin-job">'+ICO.brief+'<span class="pin-name-tag">'+escapeHtml(j.name)+' · '+escapeHtml(j.when)+'</span></div>';
  const icon=L.divIcon({html,className:'',iconSize:[40,40],iconAnchor:[20,20]});
  const marker=L.marker([j.lat,j.lng],{icon,zIndexOffset:150});
  marker.on('click',()=>showToast('Active job — '+j.name+' · '+j.when));
  marker.addTo(map); jobMarkers.push(marker);
 });
}
const _origRenderMarkers=renderMarkers;
renderMarkers=function(){ _origRenderMarkers(); renderJobs(); };

// ---------- overlays ----------
window.openOverlay=function(id){ const el=document.getElementById(id); if(el) el.classList.add('show'); };
window.closeOverlay=function(id){ const el=document.getElementById(id); if(el) el.classList.remove('show'); };

// ---------- Section 2: compact Prospects panel ----------
renderChips=function(){
 const wrap=document.getElementById('filterChips'); if(!wrap) return; wrap.innerHTML='';
 [{key:'all',label:'All',klass:''},{key:'high',label:'Excellent',klass:'tier-high'},{key:'medium',label:'Strong',klass:'tier-med'},{key:'low',label:'Skip',klass:'tier-low'}].forEach(t=>{
  const chip=document.createElement('button'); chip.className='chip '+t.klass+' '+(activeTier===t.key?'active':'');
  chip.textContent=t.label; chip.onclick=()=>{ activeTier=t.key; renderChips(); renderMarkers(); renderList(); };
  wrap.appendChild(chip);
 });
 wrap.appendChild(Object.assign(document.createElement('div'),{className:'chip-divider'}));
 const myMap=document.createElement('span'); myMap.className='layer-group';
 myMap.innerHTML='<span class="group-label">My Map</span>'+
  '<label class="layer-toggle"><input type="checkbox" id="tgCustomers" '+(showCustomers?'checked':'')+'/> Customers</label>'+
  '<label class="layer-toggle"><input type="checkbox" id="tgJobs" '+(window.showJobs?'checked':'')+'/> Active Jobs</label>'+
  '<label class="layer-toggle"><input type="checkbox" id="tgKnocks" '+(showDoorKnocks?'checked':'')+'/> Door Knocks</label>';
 wrap.appendChild(myMap);
 myMap.querySelector('#tgCustomers').addEventListener('change',e=>{ showCustomers=e.target.checked; const t=document.getElementById('showCustomersToggle'); if(t)t.checked=showCustomers; renderMarkers(); });
 myMap.querySelector('#tgJobs').addEventListener('change',e=>{ window.showJobs=e.target.checked; renderJobs(); });
 myMap.querySelector('#tgKnocks').addEventListener('change',e=>{ showDoorKnocks=e.target.checked; renderDoorKnocks(); });
 wrap.appendChild(Object.assign(document.createElement('div'),{className:'chip-divider'}));
 const lbl=document.createElement('span'); lbl.className='group-label'; lbl.textContent='Prospects'; wrap.appendChild(lbl);
 const row=document.createElement('span'); row.className='saved-row';
 const owned=Object.keys(CATEGORIES).filter(n=>unlockedCategories.has(n));
 if(!owned.length){ const e=document.createElement('span'); e.className='addbiz-empty'; e.textContent='No businesses pulled yet.'; row.appendChild(e); }
 owned.forEach(name=>{
  const cfg=CATEGORIES[name]; const chip=document.createElement('button');
  chip.className='chip'+(activeFilters.has(name)?' active':'');
  chip.innerHTML='<span style="width:8px;height:8px;border-radius:50%;background:'+cfg.color+';display:inline-block;"></span>'+name+'<span class="chip-saved">'+ICONS.eye+' Saved</span>';
  chip.onclick=()=>handleCategoryChipClick(name,chip); row.appendChild(chip);
 });
 const awrap=document.createElement('span'); awrap.className='addbiz-wrap';
 const btn=document.createElement('button'); btn.className='addbiz-btn'; btn.innerHTML=ICONS.plus+' Add businesses';
 btn.onclick=(ev)=>{ ev.stopPropagation(); const p=awrap.querySelector('.addbiz-pop'); closeAddBiz(); if(p) p.classList.add('show'); };
 awrap.appendChild(btn); awrap.appendChild(buildAddBizPop()); row.appendChild(awrap);
 wrap.appendChild(row);
};
function buildAddBizPop(){
 const pop=document.createElement('div'); pop.className='addbiz-pop';
 let h='<h4>Pull businesses — 50 IQC each</h4><div class="addbiz-grid">';
 Object.entries(CATEGORIES).forEach(([name,cfg])=>{
  const owned=unlockedCategories.has(name);
  h+='<button class="addbiz-cat" data-owned="'+(owned?1:0)+'" data-cat="'+name+'"><span class="ac-dot" style="background:'+cfg.color+'"></span><span class="ac-name">'+name+'</span><span class="ac-price">'+(owned?'Saved':'50 IQC')+'</span></button>';
 });
 h+='</div><button class="btn btn-primary addbiz-sweep" id="addbizSweep">⚡ Full City Sweep <span style="opacity:.85;font-family:var(--mono);font-size:11px;margin-left:6px;">400 IQC</span></button>';
 pop.innerHTML=h;
 pop.querySelectorAll('.addbiz-cat').forEach(b=>{ b.onclick=()=>{ const nm=b.getAttribute('data-cat'); closeAddBiz(); if(!unlockedCategories.has(nm)) handleCategoryChipClick(nm,null); }; });
 pop.querySelector('#addbizSweep').onclick=()=>{ closeAddBiz(); fullCitySweep(); };
 return pop;
}
window.closeAddBiz=function(){ document.querySelectorAll('.addbiz-pop.show').forEach(p=>p.classList.remove('show')); };
document.addEventListener('click',e=>{ if(!e.target.closest('.addbiz-wrap')) closeAddBiz(); });

// ---------- Section 3: collapsible panel ----------
window.togglePanelCollapse=function(){
 const p=document.getElementById('leftPanel'); const pill=document.getElementById('livePill');
 const collapsed=p.classList.toggle('collapsed');
 if(pill) pill.classList.toggle('show',collapsed);
 setTimeout(()=>{ if(map) map.invalidateSize(); },210);
};
(function(){
 const live=document.querySelector('.deck-title .live');
 if(live){ live.style.cursor='pointer'; live.title='Collapse panel'; live.onclick=window.togglePanelCollapse;
  const c=document.createElement('span'); c.innerHTML='<svg class="live-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:12px;height:12px;margin-left:2px;"><polyline points="15 18 9 12 15 6"/></svg>'; live.appendChild(c); }
 const mw=document.querySelector('.map-wrap');
 if(mw && !document.getElementById('livePill')){
  const pill=document.createElement('button'); pill.id='livePill'; pill.className='live-pill'; pill.textContent='Live Map'; pill.onclick=window.togglePanelCollapse; mw.appendChild(pill);
 }
})();

// ---------- Section 4: lead detail card (door-knock leads) ----------
function knockPhone(k){ if(!k.phone){ const s=Math.abs(String(k.name||'').split('').reduce((a,c)=>a+c.charCodeAt(0),0)); k.phone='(912) 555-0'+String(100+(s%900)).slice(-3); } return k.phone; }
window.openLeadCard=function(ctx){
 const k=DOOR_KNOCKS[ctx.i]; if(!k) return;
 const phone=knockPhone(k); const digits=phone.replace(/\D/g,'');
 window.__leadCtx={name:k.name, phone, lat:k.lat, lng:k.lng};
 const opts=KNOCK_STATUSES.map(s=>'<option value="'+escapeHtml(s.key)+'" '+(s.key===k.status?'selected':'')+'>'+escapeHtml(s.key)+'</option>').join('');
 const nav='https://www.google.com/maps/dir/?api=1&destination='+k.lat+','+k.lng;
 document.getElementById('leadCardInner').innerHTML=
  '<div class="lead-head"><div class="lh-body"><div class="lh-title">'+escapeHtml(k.name)+'</div><div class="lh-sub">Door-knock lead · My Map</div></div>'+
  '<button class="lh-close" onclick="closeOverlay(\'leadCardModal\')">'+ICO.x+'</button></div>'+
  '<div class="lead-body"><label class="lead-label">Change status</label>'+
  '<select class="lead-status-sel" onchange="cardSetKnockStatus('+ctx.i+', this.value)">'+opts+'</select>'+
  '<div class="lead-actions">'+
   '<a class="lead-act call" href="tel:'+digits+'"><span class="la-ico">'+ICONS.phone+'</span>Call</a>'+
   '<a class="lead-act text" href="sms:'+digits+'"><span class="la-ico">'+ICONS.message+'</span>Text</a>'+
   '<a class="lead-act nav" href="'+nav+'" target="_blank" rel="noopener"><span class="la-ico">'+ICO.nav+'</span>Navigate</a>'+
   '<button class="lead-act task" onclick="openCreateTask()"><span class="la-ico">'+ICO.task+'</span>Create Task</button>'+
   '<button class="lead-act deal" onclick="openCreateDeal()"><span class="la-ico">'+ICO.deal+'</span>Create Deal</button>'+
   '<button class="lead-act rem" onclick="openReminder()"><span class="la-ico">'+ICO.bell+'</span>Reminder</button>'+
  '</div>'+
  '<div class="lead-note">Manual pins create a lightweight contact record in QuoteIQ — not an orphan map object.</div>'+
  '<button class="lead-delete" onclick="deleteKnock('+ctx.i+')">'+ICO.trash+' Delete pin</button></div>';
 openOverlay('leadCardModal');
};
window.cardSetKnockStatus=function(i,val){ DOOR_KNOCKS[i].status=val; renderDoorKnocks(); };
window.deleteKnock=function(i){ DOOR_KNOCKS.splice(i,1); renderDoorKnocks(); closeOverlay('leadCardModal'); showToast('Pin deleted'); };

// door-knock pins now open the card (no popup); dropped pins too
renderDoorKnocks=function(){
 knockMarkers.forEach(m=>map.removeLayer(m)); knockMarkers=[];
 if(!showDoorKnocks||!map) return;
 DOOR_KNOCKS.forEach((k,i)=>{
  const isDNK=k.status==='Do Not Knock';
  const html='<div class="pin-knock" data-knock="'+i+'" style="--kc:'+knockColor(k.status)+'">'+(isDNK?'<span class="knock-x">✕</span>':'')+'</div>';
  const icon=L.divIcon({html,className:'',iconSize:[20,20],iconAnchor:[10,10]});
  const marker=L.marker([k.lat,k.lng],{icon,zIndexOffset:200});
  marker.on('click',()=>openLeadCard({i:i}));
  marker.addTo(map); knockMarkers.push(marker);
 });
};
handleDropPinClick=function(e){
 if(!dropPinMode) return;
 const lat=e.latlng.lat, lng=e.latlng.lng;
 DOOR_KNOCKS.push({ name:'Dropped pin · '+lat.toFixed(4)+', '+lng.toFixed(4), status:'Knocked — No Answer', lat:lat, lng:lng, manual:true });
 toggleDropPinMode(false);
 if(!showDoorKnocks){ showDoorKnocks=true; const cb=document.getElementById('tgKnocks'); if(cb) cb.checked=true; }
 renderDoorKnocks(); showToast('Pin dropped — contact record created');
 openLeadCard({i:DOOR_KNOCKS.length-1});
};

// saved-contact / prospect detail gets the same lead actions (non-destructive)
const _origSelectProspect=selectProspect;
selectProspect=function(idx,flyTo){
 _origSelectProspect(idx,flyTo);
 const p=PROSPECTS[idx]; if(!p) return;
 const rev=revealedContacts.get(idx);
 const phone=p.phone||(rev&&rev.phone)||knockPhone({name:p.name});
 window.__leadCtx={name:p.name, phone, lat:p.lat, lng:p.lng};
 const bar=document.querySelector('#detailContent .action-bar');
 if(bar && !bar.querySelector('.lead-actions')){
  const nav='https://www.google.com/maps/dir/?api=1&destination='+p.lat+','+p.lng;
  const row=document.createElement('div'); row.className='lead-actions'; row.style.marginTop='10px';
  row.innerHTML='<a class="lead-act text" href="sms:'+phone.replace(/\D/g,'')+'"><span class="la-ico">'+ICONS.message+'</span>Text</a>'+
   '<a class="lead-act nav" href="'+nav+'" target="_blank" rel="noopener"><span class="la-ico">'+ICO.nav+'</span>Navigate</a>'+
   '<button class="lead-act task" onclick="openCreateTask()"><span class="la-ico">'+ICO.task+'</span>Task</button>'+
   '<button class="lead-act deal" onclick="openCreateDeal()"><span class="la-ico">'+ICO.deal+'</span>Deal</button>'+
   '<button class="lead-act rem" onclick="openReminder()"><span class="la-ico">'+ICO.bell+'</span>Reminder</button>';
  bar.appendChild(row);
 }
};

// ---------- Section 5: Create Deal ----------
const PIPELINES={'Sales Pipeline':['New Lead','Contacted','Quoted','Won','Lost'],'Service Pipeline':['Request','Scheduled','In Progress','Complete']};
const EMPLOYEES=['emma1obiechina@gmail.com','mike@allamericanclean.com','crew@allamericanclean.com'];
const ESTIMATES=['EST #2664 · $537.00','EST #2662 · $500.00','EST #2652 · $410.00'];
function stageOpts(pipe){ return (PIPELINES[pipe]||[]).map(s=>'<option>'+s+'</option>').join(''); }
window.onDealPipelineChange=function(){ document.getElementById('dealStage').innerHTML=stageOpts(document.getElementById('dealPipeline').value); };
window.openCreateDeal=function(){
 const ctx=window.__leadCtx||{name:'Map lead'}; const today=new Date().toISOString().slice(0,10);
 const pipes=Object.keys(PIPELINES).map(p=>'<option>'+p+'</option>').join('');
 document.getElementById('createDealInner').innerHTML=
  '<div class="modal-header"><h3>Create Deal</h3><p>Add '+escapeHtml(ctx.name)+' to a pipeline.</p></div>'+
  '<div class="modal-body">'+
  '<div class="form-row"><div class="form-group req"><label>Pipeline</label><select id="dealPipeline" onchange="onDealPipelineChange()">'+pipes+'</select></div>'+
  '<div class="form-group req"><label>Stage</label><select id="dealStage">'+stageOpts(Object.keys(PIPELINES)[0])+'</select></div></div>'+
  '<div class="form-group req"><label>Deal name</label><input type="text" id="dealName" value="'+escapeHtml(ctx.name)+' — new deal"/></div>'+
  '<div class="form-row"><div class="form-group"><label>Amount</label><input type="text" id="dealAmount" placeholder="$0.00"/></div>'+
  '<div class="form-group"><label>Start date</label><input type="date" id="dealStart" value="'+today+'"/></div></div>'+
  '<div class="form-group"><label>Priority level</label><select id="dealPriority"><option>Low</option><option selected>Medium</option><option>High</option><option>Priority</option></select></div>'+
  '<div class="form-group"><label>Additional note</label><textarea id="dealNote" style="min-height:64px;font-family:inherit;font-size:13.5px;" placeholder="Context for this deal…"></textarea></div>'+
  '<div class="form-group"><label>Customer</label><div class="attached-cust"><span class="ac-ava">'+ICONS.person+'</span><b>'+escapeHtml(ctx.name)+'</b><button class="ac-change" onclick="showToast(\'Demo — change customer\')">Change</button></div></div>'+
  '<div class="form-group"><label>Estimate (optional)</label><select id="dealEstimate"><option value="">None</option>'+ESTIMATES.map(e=>'<option>'+e+'</option>').join('')+'</select><button class="mini-link" onclick="showToast(\'Demo — opens estimate builder\')">'+ICONS.plus+' Create New Estimate</button></div>'+
  '<div class="form-group"><label>Employee (optional)</label><select id="dealEmployee"><option value="">Unassigned</option>'+EMPLOYEES.map(e=>'<option>'+e+'</option>').join('')+'</select></div>'+
  '</div>'+
  '<div class="modal-footer"><button class="btn btn-secondary" onclick="closeOverlay(\'createDealModal\')">Cancel</button><button class="btn btn-primary" onclick="submitDeal()">Create Deal</button></div>';
 openOverlay('createDealModal');
};
window.submitDeal=function(){
 const name=document.getElementById('dealName').value.trim();
 const pipe=document.getElementById('dealPipeline').value, stage=document.getElementById('dealStage').value;
 if(!name){ showToast('Deal name is required'); return; }
 if(!pipe||!stage){ showToast('Pick a pipeline and stage'); return; }
 closeOverlay('createDealModal'); showToast('Deal created in '+pipe+' · '+stage);
};

// ---------- Section 6a: Create Task ----------
window.pickPri=function(btn){ btn.parentElement.querySelectorAll('.pri-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); };
window.openCreateTask=function(){
 const ctx=window.__leadCtx||{name:'Lead'};
 const el=document.getElementById('createTaskInner'); el.style.maxWidth='680px';
 el.innerHTML=
  '<div class="modal-header"><h3>New Task</h3></div>'+
  '<div class="modal-body"><div class="form-row" style="grid-template-columns:1.15fr 1fr;">'+
  '<div><div class="form-group req"><label>Title</label><input type="text" id="taskTitle" value="Follow up: '+escapeHtml(ctx.name)+'"/></div>'+
  '<div class="form-group"><label>Notes</label><textarea id="taskNotes" style="min-height:64px;font-family:inherit;font-size:13.5px;" placeholder="Additional details…"></textarea></div>'+
  '<div class="form-row"><div class="form-group"><label>Due date</label><input type="date" id="taskDue"/></div><div class="form-group"><label>Due time</label><input type="text" id="taskTime" placeholder="Select time"/></div></div>'+
  '<div class="form-group"><label>Priority</label><div class="pri-group"><button class="pri-btn active" onclick="pickPri(this)">None</button><button class="pri-btn" onclick="pickPri(this)">Low</button><button class="pri-btn" onclick="pickPri(this)">Medium</button><button class="pri-btn" onclick="pickPri(this)">High</button></div></div>'+
  '<div class="form-group"><label>Assign to</label><select id="taskAssign">'+EMPLOYEES.map(e=>'<option>'+e+'</option>').join('')+'</select></div>'+
  '<div class="form-group"><label>Reminder — when</label><select id="taskRemind"><option>No reminder</option><option>At time of task</option><option>10 minutes before</option><option>1 hour before</option><option>1 day before</option></select></div></div>'+
  '<div><div class="form-group"><label>Link to — Deal</label><select><option>Select Deal</option></select></div>'+
  '<div class="form-group"><label>Customer</label><select><option selected>'+escapeHtml(ctx.name)+'</option><option>Select Customer</option></select></div>'+
  '<div class="form-group"><label>Job / Schedule</label><select><option>Select Job</option></select></div>'+
  '<div class="form-group"><label>Estimate</label><select><option>Select Estimate</option>'+ESTIMATES.map(e=>'<option>'+e+'</option>').join('')+'</select></div>'+
  '<div class="form-group"><label>Invoice</label><select><option>Select Invoice</option></select></div></div>'+
  '</div></div>'+
  '<div class="modal-footer"><button class="btn btn-secondary" onclick="closeOverlay(\'createTaskModal\')">Cancel</button><button class="btn btn-primary" onclick="submitTask()">Create Task</button></div>';
 openOverlay('createTaskModal');
};
window.submitTask=function(){ const t=document.getElementById('taskTitle').value.trim(); if(!t){ showToast('Title is required'); return; } closeOverlay('createTaskModal'); showToast('Task created'); };

// ---------- Section 6b: Reminder ----------
window.openReminder=function(){
 const ctx=window.__leadCtx||{name:'Lead'};
 document.getElementById('reminderInner').innerHTML=
  '<div class="modal-header"><h3>New Reminder</h3><p>'+escapeHtml(ctx.name)+'</p></div>'+
  '<div class="modal-body">'+
  '<div class="form-group"><label>Note</label><textarea id="remNote" style="min-height:64px;font-family:inherit;font-size:13.5px;">Follow up with '+escapeHtml(ctx.name)+'</textarea></div>'+
  '<div class="form-row"><div class="form-group"><label>Remind me — date</label><input type="date" id="remDate"/></div><div class="form-group"><label>Time</label><input type="text" id="remTime" placeholder="Select time"/></div></div>'+
  '<div class="form-group"><label>Send to</label><select id="remSend"><option>Me</option>'+EMPLOYEES.map(e=>'<option>'+e+'</option>').join('')+'</select></div>'+
  '<div class="form-group"><label>Via</label><div class="pri-group" style="max-width:150px;"><button class="pri-btn active" onclick="event.preventDefault()">🔔 Push</button></div></div>'+
  '</div>'+
  '<div class="modal-footer"><button class="btn btn-secondary" onclick="closeOverlay(\'reminderModal2\')">Cancel</button><button class="btn btn-primary" onclick="submitReminder()">Set Reminder</button></div>';
 openOverlay('reminderModal2');
};
window.submitReminder=function(){ closeOverlay('reminderModal2'); showToast('Reminder set'); };

// ---------- boot: rebind + re-render with new logic ----------
if(map){ map.off('click'); map.on('click', handleDropPinClick); }
renderChips(); renderMarkers();
document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ ['leadCardModal','createDealModal','createTaskModal','reminderModal2'].forEach(closeOverlay); } });
})();
</script>
'''
sub("\n</body>", REDESIGN + "\n</body>", 1, "redesign-block")

OUT.write_text(html)
print(f"built -> {OUT}  ({len(html)} bytes)")
