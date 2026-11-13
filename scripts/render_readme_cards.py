#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.

Design: "Bruce Wayne" -- paper white and ink black only, slim cards, in the
spirit of Avi Vashishta's animated-SVG-card README (avivashishta.com/blog/
github-profile-readme-animated-svg-cards). No colour, no terminal: the hero
carries a dot-only portrait (data/portrait_dots.json, built by
scripts/make_dot_portrait.py from a photo the user supplied) that prints in
row by row beside the name.

Every card is a standalone SVG shown through <img>, so it uses only what
GitHub allows there: an inline <style> block with CSS keyframes, SMIL, and
system font stacks (no JS, no external requests, nothing to break).

Live numbers come from data/contributions.json (fetch_contributions.py).
Run by .github/workflows/update-profile-art.yml after the fetch step.
STATIC=1 renders every animation at its end state, for screenshots.
"""
import datetime, json, os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
PORTRAIT = os.path.join(ROOT, "data", "portrait_dots.json")
OUT = os.path.join(ROOT, "cards")

with open(DATA) as f:
    D = json.load(f)
with open(PORTRAIT) as f:
    P = json.load(f)

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

# ---- brand tokens: paper & ink only -----------------------------------------
PAPER = "#fafaf8"
PAPER_DEEP = "#e8e8e3"
INK = "#111111"
SOFT = "#3a3a3c"
MUTED = "#6e6e73"
RULE = "#dcdcd7"
GREY_BAR = "#cfcfca"
W = 880

SERIF = "Georgia, 'Times New Roman', serif"
SANS = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
@keyframes tilein{0%{opacity:0;transform:translateY(56px) scale(.72) rotate(-6deg)}55%{opacity:1;transform:translateY(-6px) scale(1.03) rotate(1.4deg)}75%{transform:translateY(2px) scale(.99) rotate(-.5deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-20px)}to{opacity:1;transform:none}}
@keyframes sheen{0%{transform:translateX(-240px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.6;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
.r{opacity:0;animation:rise .75s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .85s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .75s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .35s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .55s cubic-bezier(.2,.7,.2,1) both}
.sh{animation:sheen 5.5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.p,.ti,.sl{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}.live,.nu{animation:none!important}}
"""

GAP = 12
BOTTOM = 12
STATIC = bool(os.environ.get("STATIC"))

def svg(w, h, body, label, left=0, right=0, bottom=BOTTOM):
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w2, h2 = w + left + right, h + bottom
    css = BASE_CSS
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

def count_up(num, x, y, attrs, begin, dur=1.0, frames=18):
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

def sheen_block(w, h, delay, dark=False):
    col = "#111111" if dark else "#ffffff"
    return (f'<clipPath id="clip"><rect width="{w}" height="{h}" rx="14"/></clipPath>'
            f'<g clip-path="url(#clip)"><rect class="sh" style="animation-delay:{delay}s" x="0" y="-20" width="80" height="{h+40}" fill="{col}" opacity="0.10"/></g>')

def frame(w, h):
    return (f'<rect width="{w}" height="{h}" rx="14" fill="{PAPER}"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="13" fill="none" stroke="{RULE}"/>')

# ---- 1 · hero: name + dot portrait, no terminal -------------------------------
def hero():
    h = 336
    # dot portrait, right side: 42 cols over 252px -> cell 6, 52 rows -> 312 tall
    cell = 6.0
    px0, py0 = 880 - 48 - P["cols"] * cell, 12
    dots = []
    for c, r, f in P["dots"]:
        cx = px0 + c * cell + cell / 2
        cy = py0 + r * cell + cell / 2
        rad = max(0.5, f * cell * 0.46)
        delay = 0.30 + r * 0.018
        dots.append(f'<circle class="f" style="animation-delay:{delay:.2f}s;animation-duration:.35s" cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.2f}" fill="{INK}"/>')
    body = f"""
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="560" y2="0">
    <stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/>
    <stop offset=".5" stop-color="#9a9a94"/><stop offset=".58" stop-color="{INK}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-560 0;560 0;560 0" keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
{frame(W, h)}
<g class="f" {d(0)}>
  <circle class="live" cx="52" cy="46" r="4.5" fill="{INK}"/>
  <text x="66" y="51" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{MUTED}">BUILDING VOICE AI &amp; AUTONOMOUS AGENTS</text>
</g>
<text class="r" {d(0.12)} x="44" y="138" font-family="{SERIF}" font-size="64" letter-spacing="-1" fill="url(#shine)">Nithinkrishna</text>
<text class="r" {d(0.26)} x="44" y="200" font-family="{SERIF}" font-style="italic" font-size="52" fill="{INK}">T D</text>
<g class="r" {d(0.45)}>
  <text x="48" y="240" font-family="{SANS}" font-size="16.5" fill="{SOFT}">Agents that actually do things -- voice AI, multi-agent</text>
  <text x="48" y="263" font-family="{SANS}" font-size="16.5" fill="{SOFT}">systems &amp; verified RAG, shipped solo on a free stack.</text>
</g>
<g class="f" {d(0.65)}>
  <line x1="48" y1="288" x2="560" y2="288" stroke="{RULE}"/>
  <text x="48" y="312" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{INK}">CS STUDENT · KERALA, INDIA</text>
  <text x="560" y="312" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">github.com/nithincodesx</text>
</g>
<g>{''.join(dots)}</g>
"""
    write("hero.svg", svg(W, h, body, "Nithinkrishna T D. Building voice AI and autonomous agents. Computer Science student from Kerala, India. Portrait in dots."))

# ---- 2 · contribution heatmap (ink) --------------------------------------------
LEVEL_FILL = ["#e9e9e6", "#c9c9c4", "#8f8f89", "#4a4a46", "#111111"]
def heatmap():
    first = datetime.date.fromisoformat(DAYS[0]["date"])
    start = first - datetime.timedelta(days=(first.weekday() + 1) % 7)
    by_date = {x["date"]: x for x in DAYS}
    total_days = (datetime.date.fromisoformat(DAYS[-1]["date"]) - start).days + 1
    weeks = (total_days + 6) // 7
    cell, gapc = 11, 3.4
    grid_w = weeks * (cell + gapc)
    x0 = (W - grid_w) / 2
    y0 = 54
    squares, month_labels, seen_months = [], [], set()
    for wi in range(weeks):
        for wd in range(7):
            day = start + datetime.timedelta(days=wi * 7 + wd)
            key = day.isoformat()
            if key > DAYS[-1]["date"]:
                continue
            info = by_date.get(key, {"level": 0, "count": 0})
            squares.append(f'<rect class="p" style="animation-delay:{0.35 + wi*0.02:.2f}s" x="{x0 + wi*(cell+gapc):.1f}" y="{y0 + wd*(cell+gapc)}" width="{cell}" height="{cell}" rx="2.5" fill="{LEVEL_FILL[info["level"]]}"><title>{key}: {info["count"]} contributions</title></rect>')
            if wd == 0 and day.month not in seen_months and key >= DAYS[0]["date"]:
                seen_months.add(day.month)
                month_labels.append(f'<text x="{x0 + wi*(cell+gapc):.1f}" y="{y0-9}" font-family="{MONO}" font-size="10.5" fill="{MUTED}">{day.strftime("%b")}</text>')
    h = int(y0 + 7 * (cell + gapc) + 24)
    body = f"""
{frame(W, h)}
<text class="f" {d(0.05)} x="48" y="34" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{MUTED}">CONTRIBUTIONS · LAST 12 MONTHS</text>
<text class="f" {d(0.05)} x="832" y="34" text-anchor="end" font-family="{MONO}" font-size="12" fill="{INK}">{TOTAL:,} total</text>
{''.join(month_labels)}
{''.join(squares)}
<text x="{x0}" y="{h-7}" font-family="{MONO}" font-size="10.5" fill="{MUTED}">Less</text>
{''.join(f'<rect x="{x0+34+i*15}" y="{h-16}" width="11" height="11" rx="2.5" fill="{LEVEL_FILL[i]}"/>' for i in range(5))}
<text x="{x0+34+5*15+4}" y="{h-7}" font-family="{MONO}" font-size="10.5" fill="{MUTED}">More</text>
"""
    write("heatmap.svg", svg(W, h, body, f"Contribution graph for the last 12 months: {TOTAL} contributions."))

# ---- 3 · activity -----------------------------------------------------------------
def activity():
    h = 252
    maxv = max(m["total"] for m in MONTHLY) or 1
    best_month = max(MONTHLY, key=lambda m: m["total"])
    chart_x, chart_y, chart_w, chart_h = 48, 62, 520, 138
    bars = []
    for i, m in enumerate(MONTHLY):
        bh = max(4, chart_h * m["total"] / maxv)
        is_best = m is best_month
        x = chart_x + i * (chart_w / len(MONTHLY)) + 5
        bw = chart_w / len(MONTHLY) - 10
        bars.append(f'<rect class="g" style="animation-delay:{0.45 + i*0.06:.2f}s" x="{x:.1f}" y="{chart_y + chart_h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{INK if is_best else GREY_BAR}"><title>{m["month"]}: {m["total"]}</title></rect>')
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(f'<text class="f" style="animation-delay:{0.55 + i*0.06:.2f}s" x="{x + bw/2:.1f}" y="{chart_y + chart_h + 21}" text-anchor="middle" font-family="{MONO}" font-size="10.5" fill="{MUTED}">{label}</text>')
        if is_best:
            bars.append(f'<text class="p" style="animation-delay:{0.45 + i*0.06 + 0.5:.2f}s" x="{x + bw/2:.1f}" y="{chart_y + chart_h - bh - 9:.1f}" text-anchor="middle" font-family="{SANS}" font-weight="bold" font-size="15" fill="{INK}">{m["total"]}</text>')
    stats = [
        (f"{TOTAL:,}", "contributions · last year"),
        (f"{LONG_STREAK} days", "longest streak"),
        (f"{ACTIVE} days", "active days"),
        (f"{BEST['count']} · {datetime.date.fromisoformat(BEST['date']).strftime('%d %b')}", "busiest day"),
    ]
    stat_svg, sy = "", 76
    for i, (val, lab) in enumerate(stats):
        stat_svg += (f'<g class="sl" style="animation-delay:{0.8 + i*0.13:.2f}s">'
                     f'<rect x="616" y="{sy-21}" width="4" height="30" rx="2" fill="{INK}"/>'
                     f'<text x="634" y="{sy}" font-family="{SERIF}" font-size="24" fill="{INK}">{val}</text>'
                     f'<text x="634" y="{sy+18}" font-family="{MONO}" font-size="10" letter-spacing="1" fill="{MUTED}">{lab.upper()}</text></g>')
        sy += 50
    body = f"""
{frame(W, h)}
<text class="f" {d(0.05)} x="48" y="36" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{MUTED}">ACTIVITY · BY MONTH</text>
<text class="f" {d(0.05)} x="832" y="36" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">CURRENT STREAK {CUR_STREAK} DAYS</text>
<line x1="{chart_x}" y1="{chart_y+chart_h}" x2="{chart_x+chart_w}" y2="{chart_y+chart_h}" stroke="{RULE}"/>
{''.join(bars)}
<line x1="592" y1="56" x2="592" y2="{h-24}" stroke="{RULE}"/>
{stat_svg}
"""
    write("activity.svg", svg(W, h, body, f"Contributions by month. {TOTAL} in the last year, longest streak {LONG_STREAK} days, busiest day {BEST['count']}."))

# ---- 4 · world tiles: white / grey / black -----------------------------------------
TILE_W = W / 3 - 8
TILE_H = 182
def tile(name, label, bg, fg, border, big_html, sub1, sub2, delay, left=0):
    body = f"""
<rect width="{TILE_W:.3f}" height="{TILE_H}" rx="14" fill="{bg}"/>
{'<rect x="1" y="1" width="' + f'{TILE_W-2:.3f}' + '" height="' + f'{TILE_H-2}' + '" rx="13" fill="none" stroke="' + RULE + '"/>' if border else ''}
<g class="ti" style="animation-delay:{delay}s">
  <circle class="rg" style="animation-delay:{delay+0.85}s" cx="{TILE_W-40:.0f}" cy="40" r="14" fill="none" stroke="{fg}" stroke-width="2"/>
  <circle cx="{TILE_W-40:.0f}" cy="40" r="6" fill="{fg}" opacity="0.9"/>
  <text x="24" y="42" font-family="{MONO}" font-size="12.5" letter-spacing="3" fill="{fg}" opacity="0.8">{label}</text>
  {big_html}
  <text x="24" y="140" font-family="{SANS}" font-size="13.5" fill="{fg}">{sub1}</text>
  <text x="24" y="160" font-family="{SANS}" font-size="13.5" fill="{fg}">{sub2}</text>
  <text class="nu" x="{TILE_W-42:.0f}" y="161" font-family="{SANS}" font-size="20" fill="{fg}">&#8599;</text>
</g>
{sheen_block(TILE_W, TILE_H, delay+2, dark=(bg==PAPER))}
"""
    write(name, svg(TILE_W, TILE_H, body, label, left=left))

def tiles():
    tile("build.svg", "BUILD", PAPER, INK, True,
         count_up(PUBLIC_REPOS, 24, 104, f'font-family="{SERIF}" font-size="56" fill="{INK}"', 1.35) +
         f'<text x="{24 + 33*len(str(PUBLIC_REPOS)) + 8}" y="104" font-family="{SERIF}" font-style="italic" font-size="26" fill="{INK}"> repos</text>',
         "public repos shipped, solo,", "on an entirely free stack", 1.3)
    tile("agents.svg", "AGENTS", PAPER_DEEP, INK, False,
         count_up(4, 24, 104, f'font-family="{SERIF}" font-size="56" fill="{INK}"', 1.5) +
         f'<text x="64" y="104" font-family="{SERIF}" font-style="italic" font-size="26" fill="{INK}"> agents</text>',
         "in Coraxis -- researching live,", "cross-checking &amp; citing sources", 1.45, left=GAP)
    tile("voice.svg", "VOICE AI", INK, PAPER, False,
         f'<text x="24" y="104" font-family="{SERIF}" font-size="56" fill="{PAPER}">2<tspan font-style="italic" font-size="26"> languages</tspan></text>',
         "Malayalam-first AmmaCare,", "for parents living alone in Kerala", 1.6, left=GAP)

# ---- 5 · section title ----------------------------------------------------------------
def title_building():
    h = 58
    body = f"""
{frame(W, h)}
<text class="sl" {d(1.85)} x="48" y="38" font-family="{SERIF}" font-size="26" fill="{INK}">What I'm <tspan font-style="italic">building</tspan></text>
<text class="f" {d(2.0)} x="832" y="36" text-anchor="end" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{MUTED}">CLICK A CARD TO OPEN IT &#8599;</text>
"""
    write("title-building.svg", svg(W, h, body, "What I'm building"))

# ---- 6 · repo cards ----------------------------------------------------------------------
def repo_card(name, repo_key, title, desc1, desc2, delay, left=0):
    info = REPOS.get(repo_key) or {}
    lang = info.get("language") or "Python"
    stars = info.get("stars", 0)
    body = f"""
{frame(TILE_W, TILE_H)}
<g class="ti" style="animation-delay:{delay}s">
  <rect x="24" y="24" width="32" height="5" rx="2.5" fill="{INK}"/>
  <text x="24" y="66" font-family="{SERIF}" font-size="23" fill="{INK}">{escape(title)}</text>
  <text x="24" y="94" font-family="{SANS}" font-size="13.5" fill="{SOFT}">{desc1}</text>
  <text x="24" y="114" font-family="{SANS}" font-size="13.5" fill="{SOFT}">{desc2}</text>
  <circle cx="29" cy="156" r="5" fill="{INK}"/>
  <text x="42" y="160" font-family="{MONO}" font-size="12" fill="{MUTED}">{escape(lang)}</text>
  <text x="{42 + len(lang)*7.4 + 16:.0f}" y="160" font-family="{MONO}" font-size="12" fill="{MUTED}">&#9733; {stars}</text>
  <text class="nu" x="{TILE_W-42:.0f}" y="161" font-family="{SANS}" font-size="18" fill="{INK}">&#8599;</text>
</g>
"""
    write(name, svg(TILE_W, TILE_H, body, title, left=left))

def repos():
    repo_card("repo-coraxis.svg", "Coraxis", "Coraxis",
              "Four AI agents research a topic", "live and hand back a cited report.", 2.05)
    repo_card("repo-ammacare.svg", "ammacare", "AmmaCare",
              "Malayalam-first care agent for", "parents living alone in Kerala.", 2.2, left=GAP)
    repo_card("repo-rag.svg", "Verified-Hybrid-Multi-Agent-RAG-System-v1", "Verified RAG",
              "Hybrid search + a verification", "agent checking every claim.", 2.35, left=GAP)

# ---- 7 · tech stack ------------------------------------------------------------------------
def tech():
    h = 120
    items = ["Python", "TypeScript", "React", "Next.js", "FastAPI", "Node.js", "Supabase", "PostgreSQL", "Firebase", "Git"]
    chips, x, y = "", 48, 58
    for i, it in enumerate(items):
        wch = 26 + len(it) * 8.6
        if x + wch > W - 40:
            x = 48; y += 38
        chips += (f'<g class="p" style="animation-delay:{2.5 + i*0.07:.2f}s">'
                  f'<rect x="{x}" y="{y-21}" width="{wch:.0f}" height="30" rx="15" fill="{PAPER}" stroke="{RULE}"/>'
                  f'<text x="{x + wch/2:.0f}" y="{y}" text-anchor="middle" font-family="{MONO}" font-size="12.5" fill="{SOFT}">{it}</text></g>')
        x += wch + 10
    body = f"""
{frame(W, h)}
<text class="f" {d(2.4)} x="48" y="32" font-family="{MONO}" font-size="11.5" letter-spacing="2" fill="{MUTED}">TECH I BUILD WITH</text>
{chips}
"""
    write("tech.svg", svg(W, h, body, "Tech stack: Python, TypeScript, React, Next.js, FastAPI, Node.js, Supabase, PostgreSQL, Firebase, Git"))

if __name__ == "__main__":
    hero(); heatmap(); activity(); tiles(); title_building(); repos(); tech()
