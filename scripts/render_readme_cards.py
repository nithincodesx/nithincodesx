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
import base64, datetime, json, os
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

# ---- 1 · hero: name + the exact silhouette image the user supplied -------------
def hero():
    h = 336
    jpg = os.path.join(ROOT, "assets", "batman.jpg")
    if os.path.exists(jpg):
        with open(jpg, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
    else:
        # the repo stores the image as base64 text (assets/batman-base64.txt):
        # the GitHub snapshot push only carries UTF-8 files, no binaries
        with open(os.path.join(ROOT, "assets", "batman-base64.txt")) as fh:
            b64 = "".join(fh.read().split())
    # exact image, embedded as a data URI (SVG <img> sandboxes block external
    # requests, data URIs are fine). White background in the photo blends into
    # the paper card via mix-blend-mode: multiply.
    img_w = 235  # 735x1050 source at hero height
    img_x = W - 36 - img_w
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
<g class="f" {d(0.35)}>
  <image href="data:image/jpeg;base64,{b64}" x="{img_x}" y="0" width="{img_w}" height="{h}" preserveAspectRatio="xMidYMid meet" style="mix-blend-mode:multiply"/>
</g>
"""
    write("hero.svg", svg(W, h, body, "Nithinkrishna T D. Building voice AI and autonomous agents. Computer Science student from Kerala, India. Batman silhouette."))

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

# ---- 3 · activity: Avi's layout -- big serif total, bars, right-hand stats -------
BLUE = "#2f55ff"  # the one accent, on the best month only -- same as Avi's card
def activity():
    h = 316
    total_days = len(DAYS)
    maxv = max(m["total"] for m in MONTHLY) or 1
    best_month = max(MONTHLY, key=lambda m: m["total"])
    chart_x, base_y, chart_w, chart_h = 48, 258, 536, 110
    step = chart_w / len(MONTHLY)
    bars = []
    for i, m in enumerate(MONTHLY):
        bh = max(4, chart_h * m["total"] / maxv)
        is_best = m is best_month
        x = chart_x + i * step + 6
        bw = step - 12
        bars.append(f'<rect class="g" style="animation-delay:{0.5 + i*0.06:.2f}s" x="{x:.1f}" y="{base_y - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="5" fill="{BLUE if is_best else INK}"><title>{m["month"]}: {m["total"]}</title></rect>')
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(f'<text class="f" style="animation-delay:{0.6 + i*0.06:.2f}s" x="{x + bw/2:.1f}" y="{base_y + 24}" text-anchor="middle" font-family="{SANS}" font-size="12" fill="{MUTED}">{label}</text>')
        if is_best:
            bars.append(f'<text class="p" style="animation-delay:{0.5 + i*0.06 + 0.5:.2f}s" x="{x + bw/2:.1f}" y="{base_y - bh - 10:.1f}" text-anchor="middle" font-family="{SANS}" font-size="13" font-weight="600" fill="{BLUE}">{m["total"]:,}</text>')
    stats = [
        (f"{LONG_STREAK} days", "longest streak"),
        (f"{ACTIVE} / {total_days}", "days with a contribution"),
        (f"{BEST['count']}", f"on the busiest day · {datetime.date.fromisoformat(BEST['date']).strftime('%d %b')}"),
    ]
    stat_svg, sy = "", 108
    for i, (val, lab) in enumerate(stats):
        stat_svg += (f'<g class="sl" style="animation-delay:{0.85 + i*0.16:.2f}s">'
                     f'<text x="640" y="{sy}" font-family="{SERIF}" font-size="38" fill="{INK}">{val}</text>'
                     f'<text x="642" y="{sy+26}" font-family="{SANS}" font-size="13.5" fill="{SOFT}">{lab}</text></g>')
        sy += 84
    body = f"""
{frame(W, h)}
<text class="f" {d(0.05)} x="48" y="42" font-family="{MONO}" font-size="12" letter-spacing="2.5" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<g class="r" {d(0.2)}>
  <text x="46" y="112" font-family="{SERIF}" font-size="58" fill="{INK}">{TOTAL:,}<tspan font-family="{SANS}" font-weight="300" font-size="38" fill="{SOFT}"> contributions</tspan></text>
</g>
<text class="f" {d(0.3)} x="640" y="52" font-family="{SANS}" font-size="13.5" fill="{SOFT}">current streak {CUR_STREAK} days</text>
{''.join(bars)}
{stat_svg}
"""
    write("activity.svg", svg(W, h, body, f"The last 12 months on GitHub: {TOTAL} contributions. Longest streak {LONG_STREAK} days, {ACTIVE} of {total_days} days with a contribution, busiest day {BEST['count']}."))

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


# ---- 8 · skills & stack (two-column, after the screenshot the user sent) ---------
# Left column is icon-only tiles: brand glyphs from Simple Icons, stored as
# assets/icons/<slug>.svg (CC0) and embedded as paths -- an SVG shown through
# <img> cannot load external images, so the glyphs must live inside the card.
import re as _re
def _icon_path(slug):
    with open(os.path.join(ROOT, "assets", "icons", slug + ".svg")) as fh:
        m = _re.search(r'<path d="([^"]+)"', fh.read())
    return m.group(1) if m else ""

def _icon_tile(x, y, slug, name, delay):
    dpath = _icon_path(slug)
    return (f'<g class="p" style="animation-delay:{delay:.2f}s"><title>{escape(name)}</title>'
            f'<rect x="{x}" y="{y}" width="46" height="46" rx="10" fill="{PAPER}" stroke="{RULE}"/>'
            f'<svg x="{x+9}" y="{y+9}" width="28" height="28" viewBox="0 0 24 24"><path d="{dpath}" fill="{INK}"/></svg></g>')

def _text_tile(x, y, delay):
    return (f'<g class="p" style="animation-delay:{delay:.2f}s"><title>VS Code</title>'
            f'<rect x="{x}" y="{y}" width="46" height="46" rx="10" fill="{PAPER}" stroke="{RULE}"/>'
            f'<text x="{x+23}" y="{y+24}" text-anchor="middle" font-family="{SERIF}" font-weight="bold" font-size="15" fill="{INK}">VS</text>'
            f'<text x="{x+23}" y="{y+37}" text-anchor="middle" font-family="{MONO}" font-size="7.5" letter-spacing="1" fill="{MUTED}">CODE</text></g>')

def _badge(x, y, text, delay, small=False):
    fs = 10 if small else 11
    cw = 6.6 if small else 7.6
    hh = 22 if small else 24
    wch = 16 + len(text) * cw
    return (f'<g class="p" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{wch:.0f}" height="{hh}" rx="4" fill="{INK}"/>'
            f'<text x="{x + wch/2:.0f}" y="{y + hh/2 + fs*0.36:.0f}" text-anchor="middle" font-family="{MONO}" font-size="{fs}" letter-spacing="1" fill="{PAPER}">{text}</text></g>', x + wch + 8)

def skills():
    left = [
        ("Languages", [("python", "Python"), ("typescript", "TypeScript"), ("javascript", "JavaScript"), ("html5", "HTML5"), ("css", "CSS")]),
        ("Frontend", [("react", "React"), ("nextdotjs", "Next.js"), ("tailwindcss", "Tailwind CSS")]),
        ("Backend", [("fastapi", "FastAPI"), ("nodedotjs", "Node.js")]),
        ("Databases", [("postgresql", "PostgreSQL"), ("supabase", "Supabase"), ("firebase", "Firebase")]),
        ("AI Frameworks", [("crewai", "CrewAI"), ("langgraph", "LangGraph"), ("huggingface", "Hugging Face")]),
        ("Cloud & DevOps", [("git", "Git"), ("github", "GitHub"), ("githubactions", "GitHub Actions"), ("vscode", "VS Code")]),
    ]
    right = [
        ("Artificial Intelligence", [["AI AGENTS", "VOICE AI"], ["CREWAI", "LANGGRAPH", "LANGSMITH", "HUGGING FACE"]],
         ["Multi-Agent Systems · RAG Pipelines · Prompt",
          "Engineering · Agent Verification · Research",
          "Agents · Cited Reports · AI Chatbots"]),
        ("Automation & Scraping", [["PLAYWRIGHT", "BROWSER AGENTS"]],
         ["Web Scraping · HLS / MP4 Stream Sniffing",
          "Series Crawlers · Flow Automation · yt-dlp"]),
        ("Data & Search", [["HYBRID RAG"]],
         ["BM25 + Vector Search · Source Cross-Checking",
          "Hallucination Checks · Document Q&A"]),
        ("Workflow & Delivery", [["GITHUB ACTIONS", "CLI HARNESS"]],
         ["API Integration · JSON Pipelines · Approval",
          "Dashboards · Daily Auto-Refresh · Free Stack"]),
    ]
    # layout: left sections are heading + one 46px icon row (advance 82);
    # right sections are heading + badge rows + text lines. Height fits both.
    left_end = 92 + (len(left) - 1) * 82 + 56
    h = left_end + 30
    out = [frame(W, h)]
    out.append(f'<text class="f" {d(2.5)} x="48" y="40" font-family="{MONO}" font-size="11.5" letter-spacing="2" fill="{MUTED}">SKILLS &amp; STACK</text>')
    out.append(f'<line x1="48" y1="54" x2="832" y2="54" stroke="{RULE}"/>')
    out.append(f'<line x1="452" y1="70" x2="452" y2="{h-24}" stroke="{RULE}"/>')
    y = 92
    for si, (title, items) in enumerate(left):
        out.append(f'<g class="sl" style="animation-delay:{2.55 + si*0.1:.2f}s"><rect x="48" y="{y-11}" width="9" height="9" fill="{INK}"/><text x="66" y="{y}" font-family="{SERIF}" font-weight="bold" font-size="16.5" fill="{INK}">{escape(title)}</text></g>')
        x = 48
        for ii, (slug, name) in enumerate(items):
            if slug == "vscode":
                out.append(_text_tile(x, y + 10, 2.65 + si*0.1 + ii*0.05))
            else:
                out.append(_icon_tile(x, y + 10, slug, name, 2.65 + si*0.1 + ii*0.05))
            x += 56
        y += 82
    y = 92
    for si, (title, badge_rows, lines) in enumerate(right):
        out.append(f'<g class="sl" style="animation-delay:{2.6 + si*0.14:.2f}s"><rect x="478" y="{y-11}" width="9" height="9" fill="{INK}"/><text x="496" y="{y}" font-family="{SERIF}" font-weight="bold" font-size="16.5" fill="{INK}">{escape(title)}</text></g>')
        by = y + 10
        for ri, row in enumerate(badge_rows):
            x = 478
            for bi, b in enumerate(row):
                chip, x = _badge(x, by, b, 2.7 + si*0.14 + ri*0.08 + bi*0.05, small=(ri > 0))
                out.append(chip)
            by += 24 + 6 if ri == 0 else 22 + 6
        ty = by + 20
        for li, ln in enumerate(lines):
            out.append(f'<text class="f" style="animation-delay:{2.85 + si*0.14 + li*0.07:.2f}s" x="478" y="{ty}" font-family="{SANS}" font-size="13.5" fill="{SOFT}">{escape(ln)}</text>')
            ty += 20
        y = ty + 18
    write("skills.svg", svg(W, h, "".join(out), "Skills and stack, as icons: Python, TypeScript, JavaScript, HTML5, CSS, React, Next.js, Tailwind CSS, FastAPI, Node.js, PostgreSQL, Supabase, Firebase, CrewAI, LangGraph, Hugging Face, Git, GitHub, GitHub Actions, VS Code. Plus AI agents, voice AI, automation and RAG."))

if __name__ == "__main__":
    hero(); heatmap(); activity(); tiles(); title_building(); repos(); tech(); skills()
