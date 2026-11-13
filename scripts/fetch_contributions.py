#!/usr/bin/env python3
"""
Scrape real daily contribution counts from GitHub's public, unauthenticated
contributions endpoint (the same fragment the profile page itself uses) and
write data/contributions.json with the raw days plus derived stats
(current streak, longest streak, best day, monthly totals).

Stdlib only -- no token, no auth, no GraphQL, no pip installs.
Run daily by .github/workflows/update-profile-art.yml.
"""
import datetime, json, os, re, sys, urllib.request
from html.parser import HTMLParser

USERNAME = os.environ.get("GH_PROFILE_USER", "nithincodesx")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contributions.json")

class CalParser(HTMLParser):
    """Collect ContributionCalendar-day cells and their tool-tip texts."""
    def __init__(self):
        super().__init__()
        self.cells = {}          # id -> {date, level}
        self.tooltips = {}       # for-id -> text
        self._tip_for = None
        self._tip_text = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in (a.get("class") or ""):
            if a.get("data-date"):
                self.cells[a.get("id")] = {"date": a["data-date"], "level": int(a.get("data-level") or 0)}
        elif tag == "tool-tip" and a.get("for"):
            self._tip_for = a["for"]; self._tip_text = []
    def handle_data(self, data):
        if self._tip_for:
            self._tip_text.append(data)
    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._tip_for:
            self.tooltips[self._tip_for] = "".join(self._tip_text).strip()
            self._tip_for = None

def fetch_days():
    req = urllib.request.Request(URL, headers={"User-Agent": "profile-readme-bot/1.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    p = CalParser(); p.feed(html)
    if not p.cells:
        print("no calendar cells found -- github markup may have changed", file=sys.stderr); sys.exit(1)
    days = []
    for cid, cell in p.cells.items():
        text = p.tooltips.get(cid, "")
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.match(r"(\d+)", text)
            count = int(m.group(1)) if m else 0
        days.append({"date": cell["date"], "count": count, "level": cell["level"]})
    days.sort(key=lambda d: d["date"])
    return days

def current_streak(days):
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1
    streak = 0; end_idx = idx
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1; idx -= 1
    if streak == 0:
        return {"length": 0, "start": None, "end": None}
    return {"length": streak, "start": days[idx + 1]["date"], "end": days[end_idx]["date"]}

def longest_streak(days):
    longest = run = 0; ls = le = None; run_start = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0: run_start = i
            run += 1
            if run > longest:
                longest = run; ls = days[run_start]["date"]; le = d["date"]
        else:
            run = 0
    return {"length": longest, "start": ls, "end": le}

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-bot/1.0", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

FEATURED_REPOS = ["Coraxis", "ammacare", "Verified-Hybrid-Multi-Agent-RAG-System-v1"]

def fetch_profile():
    """Public profile + featured-repo numbers from the GitHub API (no auth)."""
    try:
        u = fetch_json(f"https://api.github.com/users/{USERNAME}")
        profile = {"public_repos": u.get("public_repos"), "followers": u.get("followers"), "following": u.get("following")}
    except Exception as e:
        print(f"profile fetch failed: {e}", file=sys.stderr); profile = {}
    repos = {}
    for name in FEATURED_REPOS:
        try:
            r = fetch_json(f"https://api.github.com/repos/{USERNAME}/{name}")
            repos[name] = {"stars": r.get("stargazers_count", 0), "language": r.get("language"), "forks": r.get("forks_count", 0)}
        except Exception as e:
            print(f"repo fetch failed for {name}: {e}", file=sys.stderr)
    return profile, repos

def build_data(days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"])
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    profile, repos = fetch_profile()
    return {
        "username": USERNAME,
        "profile": profile,
        "repos": repos,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": current_streak(days),
        "longest_streak": longest_streak(days),
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }

if __name__ == "__main__":
    data = build_data(fetch_days())
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT_PATH}: {data['total_contributions']} contributions, "
          f"current streak {data['current_streak']['length']}, longest {data['longest_streak']['length']}, "
          f"best day {data['best_day']['count']} on {data['best_day']['date']}")
