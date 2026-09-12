# -*- coding: utf-8 -*-
"""Two-column profile card. Square corners, hairline rules, tight rhythm.

Outputs gen/profile-{light,dark}.svg
Latin text uses embedded Inter; Chinese falls back to the viewer's platform font.
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

W, H = 900, 328
PAD = 32
LX, LW = PAD, 268            # left column: 32 .. 300
DIV = 340                    # vertical hairline
RX = 372
RW = W - RX - PAD            # 496

INK_L, INK_D = "#1d1d1f", "#f5f5f7"
GRAY_L, GRAY_D = "#6e6e73", "#98989d"
FAINT_L, FAINT_D = "#86868b", "#a1a1a6"
HAIR_L, HAIR_D = "#e3e3e6", "#3a3a3c"
BLUE_L, BLUE_D = "#0071e3", "#2997ff"

# Inter covers latin; Chinese falls back to the platform UI font of the viewer.
FAM = ("Inter, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', "
       "'Noto Sans SC', sans-serif")

LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "C#": "#4c8f5d",
    "C": "#8f8f8f", "C++": "#f34b7d", "Python": "#3572A5", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051", "Go": "#00ADD8", "Rust": "#dea584",
    "Java": "#b07219", "PowerShell": "#012456", "Dockerfile": "#384d54",
}

FONT_URLS = {
    400: "https://cdn.jsdelivr.net/npm/@fontsource/inter@5.1.0/files/inter-latin-400-normal.woff2",
    600: "https://cdn.jsdelivr.net/npm/@fontsource/inter@5.1.0/files/inter-latin-600-normal.woff2",
}

REPO_DESCS = {
    "stealth-pdf-viewer": "隐蔽的 VS Code PDF 阅读批注工具。",
    "MqttVision-Server": "C# 编写的实时 MQTT 视觉服务。",
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

    langs = {}
    for r in repos:
        if r["language"]:
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
    langs = [(n, round(c / total * 100)) for n, c in top]

    featured = sorted([r for r in repos if not r["fork"]],
                      key=lambda r: (-r["stargazers_count"], r["pushed_at"]))[:2]
    featured = [{
        "name": r["name"],
        "lang": r["language"] or "",
        "desc": REPO_DESCS.get(r["name"], ""),
        "stars": r["stargazers_count"],
    } for r in featured]

    dt = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    joined = f"{dt.year} 年 {dt.month} 月"
    return dict(commits=commits, stars=sum(r["stargazers_count"] for r in repos),
                followers=user["followers"], repos=user["public_repos"],
                langs=langs, featured=featured, joined=joined)


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


def build(d, theme):
    light = theme == "light"
    ink = INK_L if light else INK_D
    gray = GRAY_L if light else GRAY_D
    faint = FAINT_L if light else FAINT_D
    hair = HAIR_L if light else HAIR_D
    blue = BLUE_L if light else BLUE_D

    L = []
    a = L.append

    # ---- left column: identity
    a(f'  <text x="{LX}" y="64" font-family="{FAM}" font-size="34" font-weight="600" '
      f'letter-spacing="-0.9" fill="{ink}">xiaomu.</text>')
    a(f'  <text x="{LX}" y="90" font-family="{FAM}" font-size="13.5" fill="{gray}">写代码，也写工具。</text>')

    a(f'  <line x1="{LX}" y1="114" x2="{LX+LW}" y2="114" stroke="{hair}"/>')

    rows = [("加入", d["joined"]),
            ("公开仓库", d["repos"]),
            ("关注者", d["followers"]),
            ("提交次数", f'{d["commits"]:,}')]
    y = 140
    for label, value in rows:
        a(f'  <text x="{LX}" y="{y}" font-family="{FAM}" font-size="11.5" letter-spacing="0.5" '
          f'fill="{faint}">{esc(label)}</text>')
        a(f'  <text x="{LX+LW}" y="{y}" text-anchor="end" font-family="{FAM}" font-size="12.5" '
          f'font-weight="600" font-feature-settings="\'tnum\'" fill="{ink}">{esc(value)}</text>')
        y += 26

    a(f'  <text x="{LX}" y="{y+18}" font-family="{FAM}" font-size="12" fill="{blue}">'
      f'github.com/{USER}</text>')

    # divider
    a(f'  <line x1="{DIV}" y1="40" x2="{DIV}" y2="{H-40}" stroke="{hair}"/>')

    # ---- right column: selected work
    a(f'  <text x="{RX}" y="50" font-family="{FAM}" font-size="11.5" font-weight="600" '
      f'letter-spacing="0.8" fill="{faint}">作品</text>')

    y = 84
    for r in d["featured"]:
        dot = LANG_COLORS.get(r["lang"], "#aeaeb2")
        meta = r["lang"] + (f'   {r["stars"]}★' if r["stars"] else "")
        a(f'  <text x="{RX}" y="{y}" font-family="{FAM}" font-size="15" font-weight="600" '
          f'letter-spacing="-0.2" fill="{ink}">{esc(r["name"])}</text>')
        a(f'  <text x="{RX+RW}" y="{y}" text-anchor="end" font-family="{FAM}" font-size="12" '
          f'fill="{gray}">{esc(meta)}</text>')
        if r["desc"]:
            a(f'  <circle cx="{RX+3.5}" cy="{y+22.5}" r="3.5" fill="{dot}"/>')
            a(f'  <text x="{RX+14}" y="{y+26}" font-family="{FAM}" font-size="12.5" '
              f'fill="{gray}">{esc(r["desc"])}</text>')
        y += 48

    # ---- right column: activity
    y += 6
    a(f'  <line x1="{RX}" y1="{y}" x2="{RX+RW}" y2="{y}" stroke="{hair}"/>')

    y += 26
    a(f'  <text x="{RX}" y="{y}" font-family="{FAM}" font-size="11.5" font-weight="600" '
      f'letter-spacing="0.8" fill="{faint}">活跃度</text>')
    y += 24
    segs = f'{d["commits"]:,} 次提交   ·   {d["stars"]} 星标   ·   {d["repos"]} 个仓库'
    a(f'  <text x="{RX}" y="{y}" font-family="{FAM}" font-size="13" fill="{ink}">{esc(segs)}</text>')

    # ---- right column: languages
    y += 30
    a(f'  <text x="{RX}" y="{y}" font-family="{FAM}" font-size="11.5" font-weight="600" '
      f'letter-spacing="0.8" fill="{faint}">语言</text>')
    bar_y = y + 14
    langs = d["langs"] or [("None", 100)]
    offset = 0.0
    for i, (name, pct) in enumerate(langs):
        seg_w = max(RW * pct / 100 - (2 if i < len(langs) - 1 else 0), 4)
        a(f'  <rect x="{RX+offset:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="8" '
          f'fill="{LANG_COLORS.get(name, "#aeaeb2")}"/>')
        offset += RW * pct / 100
        if offset >= RW:
            break
    legend = "    ".join(f"{n} {p}%" for n, p in langs)
    a(f'  <text x="{RX}" y="{bar_y+30}" font-family="{FAM}" font-size="12" fill="{faint}">'
      f'{esc(legend)}</text>')

    body = "\n".join(L)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs><style>{FONTS}
.g{{animation:fade .6s cubic-bezier(.25,.1,.25,1) both}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
  </style></defs>
  <g class="g">
{body}
  </g>
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
    outs = {"profile-light.svg": build(data, "light"),
            "profile-dark.svg": build(data, "dark")}
    for name, svg in outs.items():
        path = os.path.join(OUT_DIR, name)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", path, os.path.getsize(path), "bytes")
