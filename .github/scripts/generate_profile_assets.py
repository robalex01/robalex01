#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse, html
from pathlib import Path
from datetime import datetime, timezone

USER = "robalex01"
TOKEN = os.environ["GITHUB_TOKEN"]
ROOT = Path("assets")
ROOT.mkdir(exist_ok=True)

def request(url, method="GET", data=None, headers=None):
    h = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "robalex01-profile-assets",
    }
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=h, method=method), timeout=30) as r:
        return json.loads(r.read().decode())

def graphql(query, variables=None):
    return request("https://api.github.com/graphql", "POST", {"query": query, "variables": variables or {}})

user = request(f"https://api.github.com/users/{USER}")
repos = request(f"https://api.github.com/users/{USER}/repos?per_page=100&type=all&sort=updated")

q = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount contributionLevel }
        }
      }
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalRepositoryContributions
    }
  }
}
"""
g = graphql(q, {"login": USER})["data"]["user"]["contributionsCollection"]
calendar = g["contributionCalendar"]
days = [d for w in calendar["weeks"] for d in w["contributionDays"]]

def esc(v):
    return html.escape(str(v), quote=True)

def svg_start(w, h, title=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'

def write(name, content):
    (ROOT / name).write_text(content, encoding="utf-8")

# ---------- statistics ----------
stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
forks = sum(int(r.get("forks_count", 0)) for r in repos)
public_repos = int(user.get("public_repos", 0))
private_repos = sum(1 for r in repos if r.get("private"))
total_repos = public_repos + private_repos
contrib = int(calendar["totalContributions"])
prs = int(g["totalPullRequestContributions"])
issues = int(g["totalIssueContributions"])
commits = int(g["totalCommitContributions"])

cards = [
    ("REPOSITORIES", total_repos),
    ("FOLLOWERS", user.get("followers", 0)),
    ("STARS", stars),
    ("FORKS", forks),
    ("COMMITS", commits),
    ("PULL REQUESTS", prs),
    ("ISSUES", issues),
    ("CONTRIBUTIONS", contrib),
]
W, H = 900, 300
s = svg_start(W, H, "Voldemort GitHub statistics")
s += '<rect width="900" height="300" rx="18" fill="#0d1117" stroke="#30363d"/>'
s += '<text x="36" y="45" fill="#ffffff" font-family="Arial,sans-serif" font-size="24" font-weight="700">VOLDEMORT · GITHUB STATISTICS</text>'
s += '<text x="36" y="70" fill="#8b949e" font-family="Arial,sans-serif" font-size="13">Generated locally by GitHub Actions · no external image service</text>'
for i, (label, value) in enumerate(cards):
    col, row = i % 4, i // 4
    x, y = 28 + col*218, 95 + row*95
    s += f'<rect x="{x}" y="{y}" width="200" height="75" rx="12" fill="#161b22" stroke="#30363d"/>'
    s += f'<text x="{x+14}" y="{y+28}" fill="#a855f7" font-family="Arial,sans-serif" font-size="25" font-weight="700">{esc(value)}</text>'
    s += f'<text x="{x+14}" y="{y+53}" fill="#8b949e" font-family="Arial,sans-serif" font-size="11">{esc(label)}</text>'
s += '</svg>'
write("github-stats.svg", s)

# ---------- trophies ----------
trophy_data = [
    ("🏆", "CONTRIBUTOR", contrib),
    ("⭐", "STARS", stars),
    ("🚀", "PULL REQUESTS", prs),
    ("🐛", "ISSUES", issues),
    ("💻", "COMMITS", commits),
    ("📦", "REPOSITORIES", total_repos),
]
W, H = 900, 220
s = svg_start(W, H, "Voldemort GitHub trophies")
s += '<rect width="900" height="220" rx="18" fill="#0d1117" stroke="#30363d"/>'
s += '<text x="36" y="42" fill="#ffffff" font-family="Arial,sans-serif" font-size="23" font-weight="700">🏆 VOLDEMORT · TROPHIES</text>'
for i, (icon, label, value) in enumerate(trophy_data):
    x = 25 + i*145
    s += f'<rect x="{x}" y="68" width="130" height="125" rx="14" fill="#161b22" stroke="#30363d"/>'
    s += f'<text x="{x+65}" y="105" text-anchor="middle" font-size="27">{icon}</text>'
    s += f'<text x="{x+65}" y="138" text-anchor="middle" fill="#a855f7" font-family="Arial,sans-serif" font-size="22" font-weight="700">{esc(value)}</text>'
    s += f'<text x="{x+65}" y="160" text-anchor="middle" fill="#8b949e" font-family="Arial,sans-serif" font-size="9">{esc(label)}</text>'
s += '</svg>'
write("github-trophies.svg", s)

# ---------- contribution heatmap ----------
levels = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
W, H = 900, 190
cell = 11
gap = 3
left, top = 36, 62
s = svg_start(W, H, "Voldemort GitHub contributions")
s += '<rect width="900" height="190" rx="18" fill="#0d1117" stroke="#30363d"/>'
s += f'<text x="{left}" y="35" fill="#ffffff" font-family="Arial,sans-serif" font-size="20" font-weight="700">📈 CONTRIBUTIONS · LAST 12 MONTHS</text>'
s += f'<text x="{left+350}" y="35" fill="#8b949e" font-family="Arial,sans-serif" font-size="12">{contrib} contributions</text>'
# GitHub returns weeks in calendar order; draw them in columns.
for wi, week in enumerate(calendar["weeks"][-53:]):
    x = left + wi*(cell+gap)
    for di, day in enumerate(week["contributionDays"]):
        y = top + di*(cell+gap)
        lvl = levels.get(day["contributionLevel"], 0)
        fills = ["#161b22", "#3b0764", "#6d28d9", "#9333ea", "#c084fc"]
        s += f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fills[lvl]}"><title>{esc(day["date"])} · {esc(day["contributionCount"])} contributions</title></rect>'
s += '</svg>'
write("github-contributions.svg", s)

# ---------- top languages ----------
langs = {}
for r in repos:
    lang = r.get("language")
    if lang:
        langs[lang] = langs.get(lang, 0) + 1
top = sorted(langs.items(), key=lambda x: (-x[1], x[0]))[:6]
W, H = 900, 180
s = svg_start(W, H, "Voldemort top languages")
s += '<rect width="900" height="180" rx="18" fill="#0d1117" stroke="#30363d"/>'
s += '<text x="36" y="40" fill="#ffffff" font-family="Arial,sans-serif" font-size="22" font-weight="700">🧠 TOP LANGUAGES</text>'
if top:
    total = sum(v for _, v in top)
    x = 36
    colors = ["#a855f7", "#c084fc", "#7c3aed", "#9333ea", "#6d28d9", "#4c1d95"]
    for i, (lang, count) in enumerate(top):
        width = max(70, int(820 * count / total))
        s += f'<rect x="{x}" y="65" width="{width}" height="16" rx="8" fill="{colors[i % len(colors)]}"/>'
        s += f'<text x="{x}" y="112" fill="#ffffff" font-family="Arial,sans-serif" font-size="13" font-weight="700">{esc(lang)}</text>'
        s += f'<text x="{x}" y="132" fill="#8b949e" font-family="Arial,sans-serif" font-size="11">{count} repos</text>'
        x += width + 12
s += '</svg>'
write("github-languages.svg", s)

print("Generated local GitHub profile assets.")
