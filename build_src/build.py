#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Static-site generator for Hoàng-Ân's Poetry Collection.
Reads build_src/poems.json + translations (pilot module + optional swarm json)
and emits a custom site into ./site/.
"""
import json, html, shutil, math, re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "build_src"
OUT = ROOT / "site"
import sys; sys.path.insert(0, str(SRC))
from translations import TRANSLATIONS

POET = "Hoàng-Ân"
YEARS_NOTE = "2005 – 2014"

# ---------- de-duplication (catch-all for residual 2-4x repeats) ----------
def collapse_repeats(text, title=""):
    """Collapse a body that is the same poem repeated 2-4x, even when the copies
    are separated by a title or blank lines (uneven line counts). Uses sequence
    period detection with guards so a real refrain (e.g. 'À ơi') is never eaten:
    the repeating unit must be >=4 lines and span ~the whole body (2-4 copies)."""
    lines = [l.rstrip() for l in (text or "").split("\n")]
    ne = [(i, re.sub(r"\s+", " ", l.strip())) for i, l in enumerate(lines) if l.strip()]
    norms = [n for _, n in ne]
    m = len(norms)
    for p in range(4, m // 2 + 1):                     # unit >= 4 non-empty lines
        if all(norms[i] == norms[i + p] for i in range(m - p)):
            k = round(m / p)
            if 2 <= k <= 4 and abs(m - k * p) <= 2:    # whole body is k near-equal copies
                lines = lines[: ne[p - 1][0] + 1]      # keep the first copy
                break
    body = "\n".join(lines)
    # strip a trailing separator (blank lines or a line repeating the title)
    tk = _barekey(title)
    ls = body.split("\n")
    while ls and (not ls[-1].strip() or (tk and _barekey(ls[-1]) == tk)):
        ls.pop()
    return "\n".join(ls).strip()

def _barekey(s):
    s = "".join(c for c in __import__("unicodedata").normalize("NFD", s or "")
                if not __import__("unicodedata").combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.translate(str.maketrans("đĐ", "dD")).lower())

def strip_lead_title(body, title):
    """Drop a leading line that merely repeats the title (diacritic-insensitive)."""
    tk = _barekey(title)
    ls = body.split("\n")
    while ls and (not ls[0].strip() or (tk and _barekey(ls[0]) == tk)):
        ls.pop(0)
    return "\n".join(ls).strip()

# ---------- load ----------
poems = json.loads((SRC / "poems.json").read_text(encoding="utf-8"))
poems = [p for p in poems if len((p["body"] or "").strip()) > 4]  # drop empties
for p in poems:
    p["body"] = collapse_repeats(p["body"], p["title"])

# merge translations: pilot (hand) + swarm + codex (machine, cross-checked)
trans = {k: dict(v, _src="hand") for k, v in TRANSLATIONS.items()}

def _ingest(records, src):
    for r in records:
        slug = r.get("slug")
        body = (r.get("en_body") or "").strip()
        if not slug or len(body) < 20 or slug in trans:
            continue
        body = collapse_repeats(body, r.get("en_title", ""))
        body = strip_lead_title(body, r.get("en_title", ""))
        trans[slug] = {"en_title": r.get("en_title", ""), "en_body": body,
                       "note": r.get("note", ""), "_src": src, "fidelity": r.get("fidelity")}

swarm_path = SRC / "translations_swarm.json"
if swarm_path.exists():
    _ingest(json.loads(swarm_path.read_text(encoding="utf-8")), "swarm")
codex_dir = SRC / "codex_out"
if codex_dir.exists():
    recs = []
    for f in sorted(codex_dir.glob("*.json")):
        if f.name.startswith("_"):
            continue
        try:
            recs.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    _ingest(recs, "codex")

def dkey(p):
    try:
        d = datetime.strptime(p.get("date", ""), "%d/%m/%Y")
        return (p["year"], d.strftime("%Y%m%d"), p["slug"])
    except Exception:
        return (p["year"], "00000000", p["slug"])

poems.sort(key=dkey)
order = [p["slug"] for p in poems]
byslug = {p["slug"]: p for p in poems}

def _bare(s):
    return re.sub(r"[^a-z0-9]+", "", re.sub(r"[̀-ͯ]", "",
                  (s or "").translate(str.maketrans("đĐ", "dD")).lower()))

def first_line(body, title=""):
    tb = _bare(title)
    for ln in body.splitlines():
        s = ln.strip()
        if not s:
            continue
        letters = sum(c.isalpha() for c in s)
        if letters < 3:                  # skip dash/punctuation-only artifact lines
            continue
        if tb and _bare(s) == tb:        # skip a line that just repeats the title
            continue
        return s
    return ""

E = lambda s: html.escape(s or "", quote=True)

# ---------- shared SVG ----------
def willow(cls):
    """Procedurally drawn drooping willow branch."""
    strands = []
    for i in range(11):
        x = 60 + i * 46
        sway = 18 + (i % 3) * 10
        length = 230 + (i % 4) * 60
        cx = x + (sway if i % 2 else -sway)
        path = f"M{x} 40 Q{cx} {40+length*0.5} {x-sway*0.4} {40+length}"
        strands.append(f'<path d="{path}" fill="none" stroke="currentColor" stroke-width="2" opacity="0.8"/>')
        # leaves along the strand
        for t in (0.30, 0.48, 0.64, 0.78, 0.9):
            ly = 40 + length * t
            lx = x + (cx - x) * (t * 1.2) * 0.5 + (8 if i % 2 else -8) * t
            rot = -35 if i % 2 else 35
            strands.append(
                f'<ellipse cx="{lx:.0f}" cy="{ly:.0f}" rx="4" ry="13" fill="currentColor" '
                f'opacity="0.85" transform="rotate({rot} {lx:.0f} {ly:.0f})"/>')
    return (f'<svg class="{cls}" viewBox="0 0 600 560" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            f'<path d="M-10 44 Q300 8 610 44" fill="none" stroke="currentColor" stroke-width="3"/>'
            + "".join(strands) + "</svg>")

ORNAMENT = ('<svg viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            '<path d="M2 12h40" stroke="currentColor" stroke-width="1.2"/>'
            '<path d="M118 12H78" stroke="currentColor" stroke-width="1.2"/>'
            '<path d="M60 4C53 9 53 15 60 20 67 15 67 9 60 4Z" fill="currentColor"/>'
            '<circle cx="46" cy="12" r="1.6" fill="currentColor"/>'
            '<circle cx="74" cy="12" r="1.6" fill="currentColor"/></svg>')

IC_MOON = '<svg class="theme-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z"/></svg>'
IC_SUN = '<svg class="theme-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19"/></svg>'
IC_SEARCH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>'
IC_LEAF = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M12 2C6 7 4 13 12 22 20 13 18 7 12 2Z" opacity=".9"/><path d="M12 4v16" stroke="var(--paper)" stroke-width="1" opacity=".5"/></svg>'

def head(title, desc, css_rel, depth):
    pre = "../" * depth
    return f"""<!doctype html>
<html lang="vi" data-theme="day">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500;1,600&family=Be+Vietnam+Pro:wght@300;400;500&display=swap&subset=vietnamese,latin,latin-ext" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%232F6E4C' d='M12 2C6 7 4 13 12 22 20 13 18 7 12 2Z'/%3E%3C/svg%3E">
<link rel="stylesheet" href="{pre}assets/style.css">
</head>
<body>"""

def topbar(depth, active=""):
    pre = "../" * depth
    def nl(href, label, key):
        cl = "navlink" + (" active" if key == active else "")
        return f'<a class="{cl}" href="{pre}{href}">{label}</a>'
    return f"""<header class="topbar">
  <div class="brand"><a href="{pre}index.html"><span class="leaf">{IC_LEAF}</span>{POET}</a></div>
  <div class="spacer"></div>
  {nl('archive.html','Tuyển tập','archive')}
  <a class="navlink" href="#about">Về tác giả</a>
  <label class="search"><span>{IC_SEARCH}</span><input data-search type="search" placeholder="Tìm bài thơ…  /" aria-label="Search poems"></label>
  <button class="iconbtn" data-theme-toggle aria-label="Toggle day / night">{IC_MOON}{IC_SUN}</button>
</header>"""

def footer(depth):
    pre = "../" * depth
    return f"""<footer class="foot" id="about">
  <span class="leaf">{IC_LEAF}</span>
  <p>Tuyển tập thơ <strong>{POET}</strong> · {YEARS_NOTE}<br>
  Một collection of {len(poems)} poems, lovingly preserved and translated.</p>
  <p><a href="{pre}archive.html">Toàn bộ tuyển tập →</a></p>
</footer>
<script src="{pre}assets/app.js"></script>
</body></html>"""

# ---------- cover ----------
def build_cover():
    n_tr = len(trans)
    epi = trans.get("bai-ca-duong-lieu", {}).get("en_body", "")
    html_ = head(f"{POET} — Poetry Collection",
                 "A curated, bilingual collection of Hoàng-Ân's poetry, 2005–2014.", "", 0)
    html_ += f"""
<div class="cover" data-petals>
  {willow('willow')}{willow('willow-2')}
  <div class="cover-top">
    <span class="cover-mark">Tuyển Tập Thơ · Poetry</span>
    <button class="iconbtn" data-theme-toggle aria-label="Toggle day / night">{IC_MOON}{IC_SUN}</button>
  </div>
  <div class="cover-main">
    <div class="kicker reveal d1">Thơ · Poetry · {YEARS_NOTE}</div>
    <h1 class="reveal d2">Hoàng<span class="amp">·</span>Ân</h1>
    <p class="sub reveal d3">những bài thơ của một đời — <span style="font-style:normal">a life in verse</span></p>
    <blockquote class="epigraph reveal d4">
      <span class="q">“By the waters of Babylon,<br>I sit, and I sing…<br>my harp hangs upon the boughs of that willow tree.”</span>
      <cite>— Song of the Willow, 2005</cite>
    </blockquote>
    <div class="cover-cta reveal d5">
      <a class="btn btn-primary" href="archive.html">Vào tuyển tập&nbsp;&nbsp;→</a>
      <a class="btn btn-ghost" href="#about">Về tác giả</a>
    </div>
    <div class="cover-meta reveal d6">{len(poems)} bài thơ · {n_tr} translated · Vietnamese &amp; English</div>
  </div>
</div>
{footer(0)}"""
    (OUT / "index.html").write_text(html_, encoding="utf-8")

# ---------- archive ----------
def build_archive():
    h = head(f"Tuyển tập — {POET}", "Browse the full collection by year.", "", 0)
    h += topbar(0, "archive")
    h += '<main class="wrap">'
    h += f"""<div class="page-head">
      <h2 class="reveal d1">Tuyển Tập</h2>
      <p class="lead reveal d2">The collected poems, by year</p>
      <p class="count reveal d3">{len(poems)} poems · {YEARS_NOTE}</p>
    </div>"""

    # featured (translated)
    feat = [p for p in poems if p["slug"] in trans]
    # hand-picked pilot first, then others, cap
    feat.sort(key=lambda p: (trans[p["slug"]].get("_src") != "hand", dkey(p)))
    feat = feat[:18]
    if feat:
        cards = []
        for p in feat:
            t = trans[p["slug"]]
            cards.append(f"""<a class="feat-card" href="p/{p['slug']}.html">
              <div class="vt">{E(p['title'])}</div>
              <div class="et">{E(t.get('en_title',''))}</div>
              <div class="fl">{E(first_line(t['en_body'], t.get('en_title','')))}</div>
              <div class="yr">{E(p['date'] or p['year'])} · with translation</div>
            </a>""")
        h += f"""<section class="featured">
          <div class="eyebrow">✦ Featured · songngữ / bilingual</div>
          <div class="feat-grid">{''.join(cards)}</div>
        </section>"""

    # by year
    h += '<section class="years">'
    cur = None
    yposts = {}
    for p in poems:
        yposts.setdefault(p["year"], []).append(p)
    for y in sorted(yposts):
        rows = []
        for p in yposts[y]:
            t = trans.get(p["slug"])
            et = f'<span class="et">— {E(t["en_title"])}</span>' if t else ""
            badge = '<span class="badge">EN</span>' if t else ""
            fl = first_line(p["body"], p["title"])
            search = f"{p['title']} {t['en_title'] if t else ''} {fl}"
            rows.append(f"""<li class="prow" data-search="{E(search)}">
              <span class="date">{E(p['date'])}</span>
              <span class="body"><a href="p/{p['slug']}.html"><span class="t">{E(p['title'])}</span> {et}</a>
                <span class="fl">{E(fl)}</span></span>
              {badge}
              <a class="arrow" href="p/{p['slug']}.html" aria-label="open">→</a>
            </li>""")
        h += f"""<div class="yearblock">
          <div class="yhead"><span class="y">{y}</span><span class="yc">{len(yposts[y])} bài</span><span class="yrule"></span></div>
          <ul class="plist">{''.join(rows)}</ul>
        </div>"""
    h += '<div class="noresult">Không tìm thấy bài thơ nào — no poems match.</div>'
    h += "</section></main>"
    h += footer(0)
    (OUT / "archive.html").write_text(h, encoding="utf-8")

# ---------- poem pages ----------
def build_poem(p):
    slug = p["slug"]
    t = trans.get(slug)
    i = order.index(slug)
    prev = byslug[order[i-1]] if i > 0 else None
    nxt = byslug[order[i+1]] if i < len(order)-1 else None
    title = p["title"]
    h = head(f"{title} — {POET}", first_line(p["body"])[:150], "", 1)
    h += topbar(1)
    h += '<main class="poem-wrap">'

    en_h = f'<div class="en-h reveal d2">{E(t["en_title"])}</div>' if t else ""
    h += f"""<div class="poem-head">
      <div class="yk reveal d1">{E(p['year'])}</div>
      <h1 class="reveal d1">{E(title)}</h1>
      {en_h}
      <div class="date reveal d2">{E(p['date'])} · {E(POET)}</div>
      <div class="ornament reveal d3">{ORNAMENT}</div>"""
    if t:
        h += """<div class="tog-center reveal d3"><div class="viewtoggle" data-viewtoggle>
          <button data-view="both" class="active">Song ngữ</button>
          <button data-view="vn">Tiếng Việt</button>
          <button data-view="en">English</button>
        </div></div>"""
    h += "</div>"

    vn_text = E(p["body"])
    if t:
        en_text = E(t["en_body"])
        h += f"""<div class="poem-body reveal d4">
          <div class="cols" data-poem-stage data-mode="both">
            <div class="col vn"><span class="col-label">Tiếng Việt</span><pre class="poem-text">{vn_text}</pre></div>
            <div class="col en"><span class="col-label">English</span><pre class="poem-text">{en_text}</pre></div>
          </div>"""
        if t.get("note"):
            h += f"""<aside class="tnote"><span class="lbl">Translator's note</span>{E(t['note'])}</aside>"""
        h += "</div>"
    else:
        h += f"""<div class="poem-body reveal d4 poem-single">
          <pre class="poem-text">{vn_text}</pre>
          <p class="no-trans">— bản dịch tiếng Anh đang được thực hiện · translation forthcoming —</p>
        </div>"""

    def pn(poem, cls, lbl):
        if not poem:
            return f'<span class="empty {cls}"></span>'
        return f'<a class="{cls}" href="{poem["slug"]}.html"><div class="lbl">{lbl}</div><div class="t">{E(poem["title"])}</div></a>'
    h += f"""<nav class="pn">
      {pn(prev,'prev','← Bài trước')}
      {pn(nxt,'next','Bài sau →')}
    </nav>"""
    h += "</main>"
    h += footer(1)
    (OUT / "p" / f"{slug}.html").write_text(h, encoding="utf-8")

# ---------- run ----------
def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "p").mkdir(parents=True)
    (OUT / "assets").mkdir()
    shutil.copy(SRC / "assets" / "style.css", OUT / "assets" / "style.css")
    shutil.copy(SRC / "assets" / "app.js", OUT / "assets" / "app.js")
    (OUT / ".nojekyll").write_text("")
    build_cover()
    build_archive()
    for p in poems:
        build_poem(p)
    print(f"built site/ : {len(poems)} poems, {len(trans)} translated, "
          f"cover + archive. Featured first line: {first_line(trans['bai-ca-duong-lieu']['en_body'])[:40]}")

if __name__ == "__main__":
    main()
