# -*- coding: utf-8 -*-
"""Apple-style profile cards. Minimal, typographic, theme-aware.

Outputs to dist/: hero / repos / specs, each in -light and -dark variants.
Text: latin only (Inter embedded). Chinese copy lives in README markdown.
"""
import base64
import io
import json
import os
import urllib.request
from datetime import datetime

USER = "xiaomu1110"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = "gen"

W = 880

INK_L, INK_D = "#1d1d1f", "#f5f5f7"
GRAY_L, GRAY_D = "#6e6e73", "#98989d"
FAINT_L, FAINT_D = "#86868b", "#a1a1a6"
HAIR_L, HAIR_D = "#e5e5ea", "#3a3a3c"
CARD_L, CARD_D = "#fbfbfd", "#1c1c1e"
CARD_EDGE_L, CARD_EDGE_D = "#ececf0", "#2c2c2e"
BLUE = "#0071e3"

LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "C#": "#4c8f5d",
    "C": "#555555", "C++": "#f34b7d", "Python": "#3572A5", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051", "Go": "#00ADD8", "Rust": "#dea584",
    "Java": "#b07219", "PowerShell": "#012456", "Dockerfile": "#384d54",
}

FONT_URLS = {
    400: "https://cdn.jsdelivr.net/npm/@fontsource/inter@5.1.0/files/inter-latin-400-normal.woff2",
    600: "https://cdn.jsdelivr.net/npm/@fontsource/inter@5.1.0/files/inter-latin-600-normal.woff2",
}

REPO_DESCS = {
    "stealth-pdf-viewer": ["A stealthy PDF viewer and annotator for VS Code.",
                           "Built for busy workstations."],
    "MqttVision-Server": ["Realtime MQTT-powered vision server,",
                          "written in C#."],
}


def get(url, raw=False):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "profile-card-gen",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        return data if raw else json.loads(data)


def fetch_data():
    user = get(f"https://api.github.com/users/{USER}")
    repos, page = [], 1
    while True:
        batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    commits = 0
    try:
        commits = get(f"https://api.github.com/search/commits?q=author:{USER}&per_page=1").get("total_count", 0)
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

    langs = {}
    for r in repos:
        if r["language"]:
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    langs = [(n, round(c / total * 100)) for n, c in top]

    featured = sorted(repos, key=lambda r: (-r["stargazers_count"], r["pushed_at"]))[:2]
    featured = [{
        "name": r["name"],
        "lang": r["language"] or "",
        "desc": REPO_DESCS.get(r["name"], ["", ""]),
        "stars": r["stargazers_count"],
    } for r in featured if not r["fork"]][:2]

    joined = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%b %Y")
    return dict(commits=commits, stars=sum(r["stargazers_count"] for r in repos),
                followers=user["followers"], repos=user["public_repos"],
                active=active_days, langs=langs, featured=featured, joined=joined)


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


# ---------------------------------------------------------------- hero
def build_hero(theme):
    ink = INK_L if theme == "light" else INK_D
    gray = GRAY_L if theme == "light" else GRAY_D
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="250" viewBox="0 0 {W} 250">
  <defs><style>{FONTS}
{{animation:rise .8s cubic-bezier(.25,.1,.25,1) both}}
.t{{animation-delay:.12s}}
@keyframes rise{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
  </style></defs>
  <text class="h" x="440" y="128" text-anchor="middle" font-family="Inter" font-size="68" font-weight="600" letter-spacing="-1.5" fill="{ink}">xiaomu.</text>
  <text class="t" x="440" y="170" text-anchor="middle" font-family="Inter" font-size="16" letter-spacing="0.4" fill="{gray}">Code. Build. Ship.</text>
</svg>"""


# ---------------------------------------------------------------- repos
def repo_card(x, y, w, h, r, theme):
    ink = INK_L if theme == "light" else INK_D
    gray = GRAY_L if theme == "light" else GRAY_D
    faint = FAINT_L if theme == "light" else FAINT_D
    fill = CARD_L if theme == "light" else CARD_D
    edge = CARD_EDGE_L if theme == "light" else CARD_EDGE_D
    dot = LANG_COLORS.get(r["lang"], "#aeaeb2")
    pad = 28
    name_y = y + 62
    d1_y, d2_y = y + 100, y + 122
    foot_y = y + h - 30
    cx = x + pad + 4
    return f"""  <g>
    <rect x="{x+1}" y="{y+1}" width="{w-2}" height="{h-2}" rx="20" fill="{fill}" stroke="{edge}"/>
    <text x="{x+pad}" y="{name_y}" font-family="Inter" font-size="20" font-weight="600" letter-spacing="-0.3" fill="{ink}">{esc(r['name'])}</text>
    <text x="{x+pad}" y="{d1_y}" font-family="Inter" font-size="13.5" fill="{gray}">{esc(r['desc'][0])}</text>
    <text x="{x+pad}" y="{d2_y}" font-family="Inter" font-size="13.5" fill="{gray}">{esc(r['desc'][1])}</text>
    <circle cx="{cx}" cy="{foot_y-4}" r="5" fill="{dot}"/>
    <text x="{cx+14}" y="{foot_y}" font-family="Inter" font-size="12.5" fill="{faint}">{esc(r['lang'])}</text>
    <text x="{x+w-pad}" y="{foot_y}" text-anchor="end" font-family="Inter" font-size="12.5" font-weight="600" fill="{BLUE}">GitHub &#8594;</text>
  </g>"""


def build_repos(d, theme):
    ink = INK_L if theme == "light" else INK_D
    gray = GRAY_L if theme == "light" else GRAY_D
    cards = d["featured"]
    n = max(1, len(cards))
    H = 96 + n * 252 + (n - 1) * 24
    body = []
    for i, r in enumerate(cards):
        body.append(repo_card(30, 96 + i * 276, W - 60, 252, r, theme))
    if not cards:
        body.append("")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs><style>{FONTS}</style></defs>
  <text x="30" y="52" font-family="Inter" font-size="13" font-weight="600" letter-spacing="1.2" fill="{gray}">FEATURED</text>
{chr(10).join(body)}
</svg>"""


# ---------------------------------------------------------------- specs
def build_specs(d, theme):
    ink = INK_L if theme == "light" else INK_D
    gray = GRAY_L if theme == "light" else GRAY_D
    faint = FAINT_L if theme == "light" else FAINT_D
    hair = HAIR_L if theme == "light" else HAIR_D

    rows = [("Commits", d["commits"]), ("Stars", d["stars"]),
            ("Followers", d["followers"]), ("Public repositories", d["repos"]),
            ("Active days · 90d", d["active"]), ("Joined GitHub", d["joined"])]

    y = 96
    body = []
    for label, value in rows:
        body.append(
            f'  <text x="30" y="{y+24}" font-family="Inter" font-size="13" letter-spacing="0.3" fill="{gray}">{esc(label)}</text>\n'
            f'  <text x="{W-30}" y="{y+25}" text-anchor="end" font-family="Inter" font-size="15" font-weight="600" font-feature-settings="\'tnum\'" fill="{ink}">{esc(value)}</text>\n'
            f'  <line x1="30" y1="{y+44}" x2="{W-30}" y2="{y+44}" stroke="{hair}"/>')
        y += 64

    # languages bar
    y += 10
    body.append(f'  <text x="30" y="{y+16}" font-family="Inter" font-size="13" letter-spacing="0.3" fill="{gray}">Languages</text>')
    bar_y = y + 34
    offset = 0.0
    bar_w = W - 60
    langs = d["langs"] or [("None", 100)]
    segs = []
    for i, (name, pct) in enumerate(langs):
        seg_w = max(bar_w * pct / 100 - (2 if i < len(langs) - 1 else 0), 6)
        color = LANG_COLORS.get(name, "#aeaeb2")
        segs.append(f'<rect x="{30+offset:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="10" rx="5" fill="{color}"/>')
        offset += bar_w * pct / 100
        if offset >= bar_w:
            break
    body.append("  " + "".join(segs))
    legend = "   ·   ".join(f"{n} {p}%" for n, p in langs)
    body.append(f'  <text x="30" y="{bar_y+34}" font-family="Inter" font-size="12.5" fill="{faint}">{esc(legend)}</text>')
    H = bar_y + 58
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs><style>{FONTS}</style></defs>
  <text x="30" y="52" font-family="Inter" font-size="13" font-weight="600" letter-spacing="1.2" fill="{gray}">TECH SPECS</text>
{chr(10).join(body)}
</svg>"""


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print("fetching github data ...")
    data = fetch_data()
    print("loading fonts ...")
    FONTS = load_fonts()
    print("stats:", data["commits"], "commits /", data["stars"], "stars /",
          data["followers"], "followers /", data["repos"], "repos /",
          data["langs"], "/ featured:", [r["name"] for r in data["featured"]])
    outs = {
        "hero-light.svg": build_hero("light"), "hero-dark.svg": build_hero("dark"),
        "repos-light.svg": build_repos(data, "light"), "repos-dark.svg": build_repos(data, "dark"),
        "specs-light.svg": build_specs(data, "light"), "specs-dark.svg": build_specs(data, "dark"),
    }
    for name, svg in outs.items():
        path = os.path.join(OUT_DIR, name)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", path, os.path.getsize(path), "bytes")
