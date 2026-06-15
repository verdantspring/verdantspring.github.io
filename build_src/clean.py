#!/usr/bin/env python3
"""
Clean the Hoàng-Ân poetry corpus.

Fixes three classes of mechanical corruption (never rewords):
  1. 3x body duplication (the whole poem repeated 2-3 times)
  2. stray artifacts: ¬ (U+00AC), soft hyphen (U+00AD), nbsp
  3. spurious space after an ACCENTED vowel / combining tone mark that
     splits a single Vietnamese syllable ("Hoà ng" -> "Hoàng", "bà i" -> "bài")

Emits cleaned markdown back into docs/ AND a structured manifest build_src/poems.json
"""
import json, re, unicodedata, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# --- accented vowel set: precomposed Vietnamese vowels carrying a tone mark
#     or a special base (â ă ê ô ơ ư), both cases ---
TONE = {0x300, 0x301, 0x303, 0x309, 0x323}  # grave acute tilde hook dot
SPECIAL_BASE = set("âăêôơưÂĂÊÔƠƯ")

def is_accented_vowel(ch):
    d = unicodedata.normalize("NFD", ch)
    if any(ord(c) in TONE for c in d):
        return True
    return ch in SPECIAL_BASE

ACCENTED = "".join(sorted({chr(c) for c in range(0x20, 0x2000)
                           if unicodedata.category(chr(c)).startswith("L")
                           and is_accented_vowel(chr(c))}))

# space-join: accented vowel + spaces + (syllable coda) -> joined.
# Coda = ng|nh|ch|gh or a single completing letter, bounded by a word edge.
JOIN = re.compile(
    rf"([{re.escape(ACCENTED)}])[ \t]+(?=(?:ng|nh|ch|gh|kh|[iyuoaăâeêơưmnctp])\b)"
)

AUTHOR_CANON = "Hoàng-Ân"
AUTHOR_RX = re.compile(r"^\s*Hoà?\s?ng-Ân\s*$")

def strip_artifacts(t):
    t = t.replace("¬", "").replace("­", "").replace("​", "")
    t = t.replace("\xa0", " ")
    return t

def fix_spacing(t):
    t = unicodedata.normalize("NFC", t)
    prev = None
    while prev != t:                       # iterate: "Hoà ng" needs one pass, chains need more
        prev = t
        t = JOIN.sub(r"\1", t)
    # collapse runs of spaces (not newlines) that the joins may leave
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t

def parse(path):
    raw = strip_artifacts(path.read_text(encoding="utf-8", errors="replace"))
    fm = {}
    body = raw
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2)
    # drop a leading "# H1" (we regenerate titles from frontmatter)
    body = re.sub(r"^\s*#\s+.*\n", "", body, count=1)
    return fm, body

def _trim(p):
    p = [l.rstrip() for l in p]
    while p and not p[0].strip(): p.pop(0)
    while p and not p[-1].strip(): p.pop()
    return p

def _norm(p):
    return [re.sub(r"\s+", " ", l).strip() for l in p if l.strip()]

def collapse_dupes(body, title=""):
    """The corpus duplicates each poem 2-4x, separated by 'Hoàng-Ân' lines.
    Split on those author lines, drop identical blocks, keep order."""
    parts, cur = [], []
    for ln in body.splitlines():
        if AUTHOR_RX.match(ln):
            parts.append(cur); cur = []
        else:
            cur.append(ln)
    parts.append(cur)
    parts = [p for p in (_trim(x) for x in parts) if p]

    if len(parts) <= 1:
        # no author separators: fall back to exact period detection
        lines = _trim(body.splitlines()); n = len(lines)
        for k in (4, 3, 2):
            if n >= 4 and n % k == 0:
                u = n // k
                ch = [_norm(lines[i*u:(i+1)*u]) for i in range(k)]
                if all(c == ch[0] for c in ch[1:]) and ch[0]:
                    lines = lines[:u]; break
        parts = [_trim(lines)] if lines else []
    else:
        seen, uniq = [], []
        for p in parts:
            n = _norm(p)
            if n not in seen:
                seen.append(n); uniq.append(p)
        parts = uniq

    block = "\n\n".join("\n".join(p) for p in parts).strip()
    # strip a leading line that just repeats the title (diacritic-insensitive)
    def bare(s):
        s = unicodedata.normalize("NFD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9]+", "", s.lower())
    tnorm = bare(strip_artifacts(title))
    lines = block.splitlines()
    while lines and (not lines[0].strip() or (tnorm and bare(lines[0]) == tnorm)):
        lines.pop(0)
    return "\n".join(lines).strip()

def slugify(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-{2,}", "-", s) or "untitled"

def clean_title(fm, path):
    t = fm.get("title") or path.stem.replace("-", " ")
    t = fix_spacing(strip_artifacts(t)).strip()
    # title-case-ish: leave Vietnamese as-is, just tidy
    return t

records = []
for path in sorted(DOCS.glob("20*/*.md")):
    year = path.parent.name
    fm, body = parse(path)
    body = fix_spacing(body)
    title = clean_title(fm, path)
    body = collapse_dupes(body, title)
    date = fm.get("date", "")
    slug = slugify(title)
    records.append({
        "year": year, "date": date, "title": title,
        "slug": slug, "body": body, "src": str(path.relative_to(ROOT)),
        "lines": body.count("\n") + 1, "chars": len(body),
    })

# de-dup slugs
seen = {}
for r in records:
    s = r["slug"]
    if s in seen:
        seen[s] += 1
        r["slug"] = f"{s}-{seen[s]}"
    else:
        seen[s] = 1

out = ROOT / "build_src" / "poems.json"
out.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"cleaned {len(records)} poems -> {out}")
print(f"years: {sorted({r['year'] for r in records})}")
print(f"avg lines: {sum(r['lines'] for r in records)/len(records):.1f}")
# sanity: any remaining triplicated author lines?
bad = sum(1 for r in records if r["body"].count(AUTHOR_CANON) >= 2)
print(f"bodies still with >=2 author lines: {bad}")
