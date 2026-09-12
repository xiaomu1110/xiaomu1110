# -*- coding: utf-8 -*-
"""Generate Apple-minimal style SVG cards for GitHub profile README.

Outputs to dist/: header.svg, card.svg, footer.svg
Data: GitHub REST API. Fonts: Inter (latin) embedded as base64 woff2.
"""
import base64
import io
import json
import os
import urllib.request
from datetime import datetime, timezone

USER = "xiaomu1110"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = "dist"

BLUE = "#0071e3"
INK = "#1d1d1f"
GRAY = "#6e6e73"
LIGHT = "#86868b"
BORDER = "#e5e5ea"
BG_TOP = "#f5f5f7"
BG_BOT = "#e8e8ed"

LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "C#": "#178600",
    "C": "#555555", "C++": "#f34b7d", "Python": "#3572A5", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051", "PowerShell": "#012456",
    "Java": "#b07219", "Go": "#00ADD8", "Rust": "#dea584", "Vue": "#41b883",
    "Dockerfile": "#384d54", "Lua": "#000080", "MDX": "#fcb32c",
}

FONT_URLS = {
    400: "https://cdn.jsdelivr.net/npm/@fontsource/inter@5.1.0/files/inter-latin-400-normal.woff2",
    600: "https://cdn.jsdelivr.net/npm/@fontsource/inter@5.1.0/files/inter-latin-600-normal.woff2",
}


def get(url, raw=False):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "profile-card-gen",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        if raw:
            return data
        return json.loads(data)


def fetch_data():
    user = get(f"https://api.github.com/users/{USER}")
    repos, page = [], 1
    while True:
        batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    stars = sum(r["stargazers_count"] for r in repos)
    followers = user["followers"]
    n_repos = user["public_repos"]

    langs = {}
    for r in repos:
        if r["language"]:
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    langs = [(name, round(cnt / total * 100)) for name, cnt in top]

    commits = 0
    try:
        res = get(f"https://api.github.com/search/commits?q=author:{USER}&per_page=1")
        commits = res.get("total_count", 0)
    except Exception:
        pass

    active_days = 0
    try:
        days = set()
        for p in range(1, 4):
            for e in get(f"https://api.github.com/users/{USER}/events/public?per_page=100&page={p}"):
                if e["type"] in ("PushEvent", "CreateEvent", "PullRequestEvent"):
                    days.add(e["created_at"][:10])
            if len(days) < 100 * p:
                break
        active_days = len(days)
    except Exception:
        pass

    avatar = base64.b64encode(get(user["avatar_url"] + "&size=128", raw=True)).decode()
    created = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%b %Y")
    return dict(stars=stars, followers=followers, repos=n_repos, commits=commits,
                langs=langs, active=active_days, avatar=avatar, joined=created)


def load_fonts():
    faces = []
    for weight, url in FONT_URLS.items():
        b64 = base64.b64encode(get(url, raw=True)).decode()
        faces.append(
            "@font-face{font-family:'Inter';font-style:normal;font-weight:%d;"
            "src:url(data:font/woff2;base64,%s) format('woff2');}" % (weight, b64))
    return "\n".join(faces)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def stat_tile(x, y, w, value, label):
    cx = x + w / 2
    return f"""
  <text x="{cx}" y="{y+30}" text-anchor="middle" font-size="22" font-weight="600" fill="{INK}" font-feature-settings="'tnum'">{esc(value)}</text>
  <text x="{cx}" y="{y+50}" text-anchor="middle" font-size="11" fill="{LIGHT}">{esc(label)}</text>"""


def build_card(d):
    W, H = 480, 404
    tiles = [("Commits", d["commits"]), ("Stars", d["stars"]),
             ("Followers", d["followers"]), ("Repos", d["repos"])]
    tiles_svg = "".join(stat_tile(28 + i * 106, 124, 106, v, k) for i, (k, v) in enumerate(tiles))

    # language stacked bar
    bar_x, bar_w, bar_y = 28, 424, 246
    bar = []
    offset = 0.0
    for i, (name, pct) in enumerate(d["langs"] or [("None", 100)]):
        seg_w = max(bar_w * pct / 100 - (2 if i < len(d["langs"]) - 1 else 0), 4)
        color = LANG_COLORS.get(name, "#c7c7cc")
        r = 6 if offset == 0 or offset + seg_w >= bar_w - 1 else 0
        bar.append(f'<rect x="{bar_x+offset:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="12" rx="{r}" fill="{color}"/>')
        offset += bar_w * pct / 100
        if offset >= bar_w:
            break

    # legend, two columns
    legend = []
    for i, (name, pct) in enumerate(d["langs"] or [("None", 0)]):
        col, row = i % 2, i // 2
        lx, ly = 28 + col * 216, 286 + row * 26
        color = LANG_COLORS.get(name, "#c7c7cc")
        legend.append(
            f'<circle cx="{lx+5}" cy="{ly-4}" r="5" fill="{color}"/>'
            f'<text x="{lx+18}" y="{ly}" font-size="12.5" fill="{INK}">{esc(name)}</text>'
            f'<text x="{lx+206}" y="{ly}" text-anchor="end" font-size="12.5" fill="{LIGHT}" font-feature-settings="\'tnum\'">{pct}%</text>')

    legend_rows = max(1, -(-len(d["langs"]) // 2)) if d["langs"] else 1
    div2_y = 282 + legend_rows * 26 + 8

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <style>{FONTS}</style>
    <clipPath id="av"><circle cx="58" cy="58" r="30"/></clipPath>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="2" stdDeviation="8" flood-color="#000" flood-opacity="0.05"/>
    </filter>
  </defs>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="#ffffff" stroke="{BORDER}" filter="url(#shadow)"/>
  <image x="28" y="28" width="60" height="60" clip-path="url(#av)" href="data:image/png;base64,{d['avatar']}"/>
  <text x="104" y="54" font-size="20" font-weight="600" fill="{INK}">xiaomu</text>
  <text x="104" y="76" font-size="12.5" fill="{GRAY}">Code · Build · Ship · Tools for busy people</text>
  <line x1="28" y1="110" x2="{W-28}" y2="110" stroke="{BORDER}"/>
{tiles_svg}
  <line x1="28" y1="208" x2="{W-28}" y2="208" stroke="{BORDER}"/>
  <text x="28" y="232" font-size="12" font-weight="600" fill="{INK}">Languages</text>
  {''.join(bar)}
  {''.join(legend)}
  <line x1="28" y1="{div2_y}" x2="{W-28}" y2="{div2_y}" stroke="{BORDER}"/>
  <text x="28" y="{div2_y+26}" font-size="11.5" fill="{GRAY}">Joined GitHub {esc(d['joined'])}</text>
  <text x="{W-28}" y="{div2_y+26}" text-anchor="end" font-size="11.5" fill="{GRAY}">{d['active']} active days · recent 90d</text>
</svg>"""


def build_header():
    W, H = 880, 170
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <style>{FONTS}</style>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOT}"/>
    </linearGradient>
    <radialGradient id="blob" cx="0.5" cy="0.4" r="0.6">
      <stop offset="0" stop-color="#dcdce2" stop-opacity="0.9"/><stop offset="1" stop-color="#dcdce2" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <ellipse cx="440" cy="60" rx="380" ry="120" fill="url(#blob)"/>
  <circle cx="440" cy="118" r="3.5" fill="{BLUE}"/>
  <text x="440" y="76" text-anchor="middle" font-size="46" font-weight="600" fill="{INK}" letter-spacing="0.5">xiaomu</text>
  <text x="459" y="124" text-anchor="middle" font-size="14.5" fill="{GRAY}">Code · Build · Ship</text>
</svg>"""


def build_footer():
    W, H = 880, 64
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="fg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{BG_BOT}"/><stop offset="1" stop-color="{BG_TOP}"/>
    </linearGradient>
  </defs>
  <path d="M0,{H-14} C220,{H+10} 660,{H-34} {W},{H-10} L{W},{H} L0,{H} Z" fill="url(#fg)"/>
</svg>"""


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print("fetching github data ...")
    data = fetch_data()
    print("loading fonts ...")
    FONTS = load_fonts()
    print("stats:", data["commits"], "commits,", data["stars"], "stars,",
          data["followers"], "followers,", data["repos"], "repos, langs:", data["langs"])
    for name, svg in [("header.svg", build_header()), ("card.svg", build_card(data)), ("footer.svg", build_footer())]:
        path = os.path.join(OUT_DIR, name)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", path, os.path.getsize(path), "bytes")
