#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.

Design: "Agent Worlds" -- a dark, violet-led stack matched to nithincodesx's
tokyonight streak card: violet BUILD, cyan AGENTS, amber VOICE AI.
Inspired by Avi Vashishta's animated-SVG-card README (avivashishta.com/blog/
github-profile-readme-animated-svg-cards), rebuilt for Nithinkrishna T D.

Every card is a standalone SVG shown through <img>, so it uses only what
GitHub allows there: an inline <style> block with CSS keyframes, SMIL, and
system font stacks (no JS, no external requests, nothing to break).

Live numbers come from data/contributions.json (fetch_contributions.py).
Run by .github/workflows/update-profile-art.yml after the fetch step.
STATIC=1 renders every animation at its end state, for screenshots.
"""
import datetime, json, os, re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")

with open(DATA) as f:
    D = json.load(f)

TOTAL = D["total_contributions"]
ACTIVE = D["active_days"]
CUR_STREAK = D["current_streak"]["length"]
LONG_STREAK = D["longest_streak"]["length"]
BEST = D["best_day"]
MONTHLY = D["monthly"][-12:]
DAYS = D["days"]
PROFILE = D.get("profile") or {}
REPOS = D.get("repos") or {}
PUBLIC_REPOS = PROFILE.get("public_repos", 48)
FOLLOWERS = PROFILE.get("followers", 10)

# ---- brand tokens -----------------------------------------------------------
BG = "#0b0f1a"
BG2 = "#111827"
INK = "#f1f5f9"
SOFT = "#cbd5e1"
MUTED = "#8b98b8"
RULE = "#26314d"
VIOLET = "#8b5cf6"
VIOLET_DEEP = "#6d28d9"
CYAN = "#22d3ee"
AMBER = "#fbbf24"
GREEN = "#34d399"
W = 880

SERIF = "Georgia, 'Times New Roman', serif"
SANS = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.2}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
@keyframes tilein{0%{opacity:0;transform:translateY(70px) scale(.7) rotate(-7deg)}55%{opacity:1;transform:translateY(-8px) scale(1.04) rotate(1.6deg)}75%{transform:translateY(2px) scale(.99) rotate(-.6deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-22px)}to{opacity:1;transform:none}}
@keyframes sheen{0%{transform:translateX(-280px) skewX(-20deg)}22%,100%{transform:translateX(460px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .35s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.2,.7,.2,1) both}
.sh{animation:sheen 5.5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
.blink{animation:blink 1.1s step-end infinite}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.p,.ti,.sl{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}.live,.nu,.blink{animation:none!important}}
"""

GAP = 12
BOTTOM = 12
STATIC = bool(os.environ.get("STATIC"))

def svg(w, h, body, label, extra_css="", left=0, right=0, bottom=BOTTOM):
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w2, h2 = w + left + right, h + bottom
    css = BASE_CSS + extra_css
    if STATIC:
        css += ".r,.f,.g,.p,.ti,.sl{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w2:.3f}" height="{h2}" viewBox="0 0 {w2:.3f} {h2}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f"<style>{css}</style>{body}</svg>")

def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content)//1024} KB)")

def d(s):
    return f'style="animation-delay:{s:.2f}s"'

def count_up(num, x, y, attrs, begin, dur=1.1, frames=18):
    """Integer counts up from 0 with SMIL <set> frames (CSS can't change text)."""
    if STATIC:
        return f'<text x="{x}" y="{y}" {attrs}>{num}</text>'
    out = []
    for i in range(frames + 1):
        e = 1 - (1 - i / frames) ** 3
        txt = str(num) if i == frames else str(round(num * e))
        on = begin + dur * i / frames
        off = "" if i == frames else f'<set attributeName="opacity" to="0" begin="{begin + dur*(i+1)/frames:.3f}s"/>'
        out.append(f'<text x="{x}" y="{y}" {attrs} opacity="0">{txt}'
                   f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>{off}</text>')
    return "".join(out)

def sheen_block(w, h, delay):
    return (f'<clipPath id="clip"><rect width="{w}" height="{h}" rx="14"/></clipPath>'
            f'<g clip-path="url(#clip)"><rect class="sh" style="animation-delay:{delay}s" x="0" y="-20" width="90" height="{h+40}" fill="#ffffff" opacity="0.07"/></g>')

# ---- 1 · hero -----------------------------------------------------------------
def hero():
    h = 470
    term_lines = [
        ("$ whoami", "nithinkrishna · cs student · kerala, india", MUTED),
        ("$ ./run coraxis --live", "4 agents research, cross-check &amp; cite", CYAN),
        ("$ ./run ammacare", "malayalam-first care agent for parents", AMBER),
    ]
    term = ""
    y = 350
    for i, (cmd, out, col) in enumerate(term_lines):
        term += (f'<g class="f" {d(1.0 + i*0.45)}>'
                 f'<text x="66" y="{y}" font-family="{MONO}" font-size="13.5" fill="{GREEN}">{cmd}</text>'
                 f'<text x="330" y="{y}" font-family="{MONO}" font-size="13.5" fill="{col}">&#8594; {out}</text></g>')
        y += 27
    term += f'<text class="f" {d(2.4)} x="66" y="{y}" font-family="{MONO}" font-size="13.5" fill="{GREEN}">$ <tspan class="blink" fill="{INK}">&#9612;</tspan></text>'
    body = f"""
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#131a2e"/><stop offset=".55" stop-color="{BG}"/><stop offset="1" stop-color="#1b1035"/>
  </linearGradient>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="700" y2="0">
    <stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/>
    <stop offset=".5" stop-color="{VIOLET}"/><stop offset=".58" stop-color="{INK}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-700 0;700 0;700 0" keyTimes="0;.45;1" dur="7s" begin="1.8s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="url(#bg)"/>
<rect x="1" y="1" width="{W-2}" height="{h-2}" rx="13" fill="none" stroke="{RULE}"/>
<g class="f" {d(0)}>
  <circle class="live" cx="52" cy="52" r="5" fill="{GREEN}"/>
  <text x="68" y="57" font-family="{MONO}" font-size="12.5" letter-spacing="2" fill="{MUTED}">BUILDING VOICE AI &amp; AUTONOMOUS AGENTS</text>
  <text x="832" y="57" text-anchor="end" font-family="{MONO}" font-size="12.5" letter-spacing="2" fill="{MUTED}">KERALA, INDIA</text>
</g>
<text class="r" {d(0.15)} x="46" y="168" font-family="{SERIF}" font-size="82" letter-spacing="-1" fill="url(#shine)">Nithinkrishna T D</text>
<text class="r" {d(0.35)} x="48" y="228" font-family="{SERIF}" font-style="italic" font-size="42" fill="{VIOLET}">agents that actually do things.</text>
<g class="r" {d(0.55)}>
  <text x="48" y="268" font-family="{SANS}" font-size="17.5" fill="{SOFT}">Computer Science student building voice AI, multi-agent systems &amp; verified RAG --</text>
  <text x="48" y="292" font-family="{SANS}" font-size="17.5" fill="{SOFT}">solo, on an entirely free stack. Ship it, then make it smarter.</text>
</g>

<g class="f" {d(0.9)}>
  <rect x="48" y="304" width="784" height="134" rx="10" fill="#070a12" stroke="{RULE}"/>
  <circle cx="66" cy="320" r="5" fill="#ef4444"/><circle cx="84" cy="320" r="5" fill="{AMBER}"/><circle cx="102" cy="320" r="5" fill="{GREEN}"/>
  <text x="816" y="324" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">~/agents -- zsh</text>
</g>
{term}
"""
    write("hero.svg", svg(W, h, body, "Nithinkrishna T D. Building voice AI and autonomous agents. Computer Science student from Kerala, India."))

# ---- 2 · contribution heatmap (violet) ----------------------------------------
LEVEL_FILL = ["#171e30", "#3b1470", "#5b21b6", "#8b5cf6", "#d8b4fe"]
def heatmap():
    # build week columns: GitHub days already run Sun..Sat in calendar order
    first = datetime.date.fromisoformat(DAYS[0]["date"])
    # pad back to the Sunday of the first week
    start = first - datetime.timedelta(days=(first.weekday() + 1) % 7)
    by_date = {x["date"]: x for x in DAYS}
    total_days = (datetime.date.fromisoformat(DAYS[-1]["date"]) - start).days + 1
    weeks = (total_days + 6) // 7
    cell, gapc = 11, 3.4
    grid_w = weeks * (cell + gapc)
    x0 = (W - grid_w) / 2
    y0 = 58
    squares = []
    month_labels = []
    seen_months = set()
    for wi in range(weeks):
        for wd in range(7):
            day = start + datetime.timedelta(days=wi * 7 + wd)
            key = day.isoformat()
            if key > DAYS[-1]["date"]:
                continue
            info = by_date.get(key, {"level": 0, "count": 0})
            col_delay = 0.4 + wi * 0.022
            squares.append(f'<rect class="p" style="animation-delay:{col_delay:.2f}s" x="{x0 + wi*(cell+gapc):.1f}" y="{y0 + wd*(cell+gapc)}" width="{cell}" height="{cell}" rx="2.5" fill="{LEVEL_FILL[info["level"]]}"><title>{key}: {info["count"]} contributions</title></rect>')
            if wd == 0 and day.month not in seen_months and key >= DAYS[0]["date"]:
                seen_months.add(day.month)
                month_labels.append(f'<text x="{x0 + wi*(cell+gapc):.1f}" y="{y0-10}" font-family="{MONO}" font-size="10.5" fill="{MUTED}">{day.strftime("%b")}</text>')
    h = int(y0 + 7 * (cell + gapc) + 26)
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{BG}"/>
<rect x="1" y="1" width="{W-2}" height="{h-2}" rx="13" fill="none" stroke="{RULE}"/>
<text class="f" {d(0.1)} x="48" y="36" font-family="{MONO}" font-size="12.5" letter-spacing="2" fill="{MUTED}">CONTRIBUTIONS · LAST 12 MONTHS</text>
<text class="f" {d(0.1)} x="832" y="36" text-anchor="end" font-family="{MONO}" font-size="12.5" fill="{VIOLET}">{TOTAL:,} total</text>
{''.join(month_labels)}
{''.join(squares)}
<text x="{x0}" y="{h-8}" font-family="{MONO}" font-size="10.5" fill="{MUTED}">Less</text>
{''.join(f'<rect x="{x0+34+i*15}" y="{h-17}" width="11" height="11" rx="2.5" fill="{LEVEL_FILL[i]}"/>' for i in range(5))}
<text x="{x0+34+5*15+4}" y="{h-8}" font-family="{MONO}" font-size="10.5" fill="{MUTED}">More</text>
"""
    write("heatmap.svg", svg(W, h, body, f"Contribution graph for the last 12 months: {TOTAL} contributions."))

# ---- 3 · activity: monthly bars + streak stats ---------------------------------
def activity():
    h = 300
    maxv = max(m["total"] for m in MONTHLY) or 1
    best_month = max(MONTHLY, key=lambda m: m["total"])
    chart_x, chart_y, chart_w, chart_h = 48, 70, 520, 170
    bw = chart_w / len(MONTHLY)
    bars = []
    for i, m in enumerate(MONTHLY):
        bh = max(4, chart_h * m["total"] / maxv)
        is_best = m is best_month
        col = CYAN if is_best else VIOLET_DEEP
        x = chart_x + i * bw + 5
        bars.append(f'<rect class="g" style="animation-delay:{0.5 + i*0.07:.2f}s" x="{x:.1f}" y="{chart_y + chart_h - bh:.1f}" width="{bw-10:.1f}" height="{bh:.1f}" rx="4" fill="{col}"><title>{m["month"]}: {m["total"]}</title></rect>')
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(f'<text class="f" style="animation-delay:{0.6 + i*0.07:.2f}s" x="{x + (bw-10)/2:.1f}" y="{chart_y + chart_h + 22}" text-anchor="middle" font-family="{MONO}" font-size="10.5" fill="{MUTED}">{label}</text>')
        if is_best:
            bars.append(f'<text class="p" style="animation-delay:{0.5 + i*0.07 + 0.55:.2f}s" x="{x + (bw-10)/2:.1f}" y="{chart_y + chart_h - bh - 10:.1f}" text-anchor="middle" font-family="{SANS}" font-weight="bold" font-size="16" fill="{CYAN}">{m["total"]}</text>')
    stats = [
        (f"{TOTAL:,}", "contributions · last year", VIOLET),
        (f"{LONG_STREAK} days", "longest streak", CYAN),
        (f"{ACTIVE} days", "active days", GREEN),
        (f"{BEST['count']} · {datetime.date.fromisoformat(BEST['date']).strftime('%d %b')}", "busiest day", AMBER),
    ]
    stat_svg = ""
    sy = 84
    for i, (val, lab, col) in enumerate(stats):
        stat_svg += (f'<g class="sl" style="animation-delay:{0.9 + i*0.15:.2f}s">'
                     f'<rect x="616" y="{sy-24}" width="4" height="34" rx="2" fill="{col}"/>'
                     f'<text x="634" y="{sy}" font-family="{SERIF}" font-size="27" fill="{INK}">{val}</text>'
                     f'<text x="634" y="{sy+20}" font-family="{MONO}" font-size="10.5" letter-spacing="1" fill="{MUTED}">{lab.upper()}</text></g>')
        sy += 58
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{BG}"/>
<rect x="1" y="1" width="{W-2}" height="{h-2}" rx="13" fill="none" stroke="{RULE}"/>
<text class="f" {d(0.1)} x="48" y="40" font-family="{MONO}" font-size="12.5" letter-spacing="2" fill="{MUTED}">ACTIVITY · BY MONTH</text>
<text class="f" {d(0.1)} x="832" y="40" text-anchor="end" font-family="{MONO}" font-size="12.5" fill="{MUTED}">CURRENT STREAK {CUR_STREAK} DAYS</text>
<line x1="{chart_x}" y1="{chart_y+chart_h}" x2="{chart_x+chart_w}" y2="{chart_y+chart_h}" stroke="{RULE}"/>
{''.join(bars)}
<line x1="592" y1="64" x2="592" y2="{h-30}" stroke="{RULE}"/>
{stat_svg}
"""
    write("activity.svg", svg(W, h, body, f"Contributions by month. {TOTAL} in the last year, longest streak {LONG_STREAK} days, busiest day {BEST['count']}."))

# ---- 4 · world tiles -------------------------------------------------------------
TILE_W = W / 3 - 8
TILE_H = 216
def tile(name, label, colour, dark_text, big_html, sub1, sub2, delay, left=0, right=0):
    body = f"""
<rect width="{TILE_W:.3f}" height="{TILE_H}" rx="14" fill="{colour}"/>
<g class="ti" style="animation-delay:{delay}s">
  <circle class="rg" style="animation-delay:{delay+0.9}s" cx="{TILE_W-44:.0f}" cy="44" r="16" fill="none" stroke="{dark_text}" stroke-width="2"/>
  <circle cx="{TILE_W-44:.0f}" cy="44" r="7" fill="{dark_text}" opacity="0.85"/>
  <text class="nu" x="{TILE_W-46:.0f}" y="182" font-family="{SANS}" font-size="24" fill="{dark_text}">&#8599;</text>
  <text x="24" y="46" font-family="{MONO}" font-size="13" letter-spacing="3" fill="{dark_text}" opacity="0.85">{label}</text>
  {big_html}
  <text x="24" y="158" font-family="{SANS}" font-size="14.5" fill="{dark_text}">{sub1}</text>
  <text x="24" y="179" font-family="{SANS}" font-size="14.5" fill="{dark_text}">{sub2}</text>
</g>
{sheen_block(TILE_W, TILE_H, delay+2)}
"""
    write(name, svg(TILE_W, TILE_H, body, label, left=left, right=right))

def tiles():
    big_attrs = f'font-family="{SERIF}" font-size="64" fill="#0b0f1a"'
    # BUILD (violet tile, dark text reads on the bright violet)
    tile("build.svg", "BUILD", VIOLET, "#160b2e",
         count_up(PUBLIC_REPOS, 24, 118, f'font-family="{SERIF}" font-size="64" fill="#160b2e"', 1.6) +
         f'<text x="{24 + 37*len(str(PUBLIC_REPOS)) + 8}" y="118" font-family="{SERIF}" font-style="italic" font-size="30" fill="#160b2e"> repos</text>',
         "public repos shipped, solo,", "on an entirely free stack", 1.5)
    tile("agents.svg", "AGENTS", CYAN, "#062a33",
         count_up(4, 24, 118, f'font-family="{SERIF}" font-size="64" fill="#062a33"', 1.75) +
         f'<text x="70" y="118" font-family="{SERIF}" font-style="italic" font-size="30" fill="#062a33"> agents</text>',
         "in Coraxis -- researching live,", "cross-checking &amp; citing sources", 1.65, left=GAP)
    tile("voice.svg", "VOICE AI", AMBER, "#33230a",
         f'<text x="24" y="118" font-family="{SERIF}" font-size="64" fill="#33230a">2<tspan font-style="italic" font-size="30"> languages</tspan></text>',
         "Malayalam-first AmmaCare,", "for parents living alone in Kerala", 1.8, left=GAP)

# ---- 5 · section title -----------------------------------------------------------
def title_building():
    h = 66
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{BG}"/>
<rect x="1" y="1" width="{W-2}" height="{h-2}" rx="13" fill="none" stroke="{RULE}"/>
<text class="sl" {d(2.0)} x="48" y="43" font-family="{SERIF}" font-size="30" fill="{INK}">What I'm <tspan font-style="italic" fill="{VIOLET}">building</tspan></text>
<text class="f" {d(2.15)} x="832" y="41" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">CLICK A CARD TO OPEN IT &#8599;</text>
"""
    write("title-building.svg", svg(W, h, body, "What I'm building"))

# ---- 6 · repo cards ----------------------------------------------------------------
def repo_card(name, repo_key, title, desc1, desc2, colour, delay, left=0):
    info = REPOS.get(repo_key) or {}
    lang = info.get("language") or "Python"
    stars = info.get("stars", 0)
    lang_col = {"Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6"}.get(lang, MUTED)
    body = f"""
<rect width="{TILE_W:.3f}" height="{TILE_H}" rx="14" fill="{BG2}"/>
<rect x="1" y="1" width="{TILE_W-2:.3f}" height="{TILE_H-2}" rx="13" fill="none" stroke="{RULE}"/>
<g class="ti" style="animation-delay:{delay}s">
  <rect x="24" y="26" width="34" height="5" rx="2.5" fill="{colour}"/>
  <text x="24" y="76" font-family="{SERIF}" font-size="25" fill="{INK}">{escape(title)}</text>
  <text x="24" y="106" font-family="{SANS}" font-size="14" fill="{SOFT}">{desc1}</text>
  <text x="24" y="127" font-family="{SANS}" font-size="14" fill="{SOFT}">{desc2}</text>
  <circle cx="29" cy="188" r="5.5" fill="{lang_col}"/>
  <text x="42" y="193" font-family="{MONO}" font-size="12.5" fill="{MUTED}">{escape(lang)}</text>
  <text x="{42 + len(lang)*7.8 + 16:.0f}" y="193" font-family="{MONO}" font-size="12.5" fill="{MUTED}">&#9733; {stars}</text>
  <text class="nu" x="{TILE_W-46:.0f}" y="193" font-family="{SANS}" font-size="20" fill="{colour}">&#8599;</text>
</g>
"""
    write(name, svg(TILE_W, TILE_H, body, title, left=left))

def repos():
    repo_card("repo-coraxis.svg", "Coraxis", "Coraxis",
              "Four AI agents research a topic", "live and hand back a cited report.", VIOLET, 2.2)
    repo_card("repo-ammacare.svg", "ammacare", "AmmaCare",
              "Malayalam-first care agent for", "parents living alone in Kerala.", CYAN, 2.35, left=GAP)
    repo_card("repo-rag.svg", "Verified-Hybrid-Multi-Agent-RAG-System-v1", "Verified RAG",
              "Hybrid search + a verification", "agent checking every claim.", AMBER, 2.5, left=GAP)

# ---- 7 · tech stack ------------------------------------------------------------------
def tech():
    h = 118
    items = ["Python", "TypeScript", "React", "Next.js", "FastAPI", "Node.js", "Supabase", "PostgreSQL", "Firebase", "Git"]
    chips = ""
    x = 48
    y = 62
    for i, it in enumerate(items):
        wch = 26 + len(it) * 8.6
        if x + wch > W - 40:
            x = 48; y += 40
        chips += (f'<g class="p" style="animation-delay:{2.7 + i*0.08:.2f}s">'
                  f'<rect x="{x}" y="{y-22}" width="{wch:.0f}" height="32" rx="16" fill="#131c33" stroke="{RULE}"/>'
                  f'<text x="{x + wch/2:.0f}" y="{y}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{SOFT}">{it}</text></g>')
        x += wch + 10
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{BG}"/>
<rect x="1" y="1" width="{W-2}" height="{h-2}" rx="13" fill="none" stroke="{RULE}"/>
<text class="f" {d(2.6)} x="48" y="36" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{MUTED}">TECH I BUILD WITH</text>
{chips}
"""
    write("tech.svg", svg(W, h, body, "Tech stack: Python, TypeScript, React, Next.js, FastAPI, Node.js, Supabase, PostgreSQL, Firebase, Git"))

if __name__ == "__main__":
    hero(); heatmap(); activity(); tiles(); title_building(); repos(); tech()
