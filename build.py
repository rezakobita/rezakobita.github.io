#!/usr/bin/env python3
"""
রেজার কবিতা — site builder.

Reads every poem in poems/ (one .txt file per poem) and writes the finished
website into _site/. GitHub runs this automatically on every push, so you
normally never need to run it yourself.

Run locally:   python3 build.py
Preview build: python3 build.py --preview   (links point at index.html files)
"""
import html, json, os, re, shutil, sys, unicodedata
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "_site")
PREVIEW = "--preview" in sys.argv

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
EN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
MONTHS = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই",
          "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
YES = {"yes", "y", "true", "হ্যাঁ", "হ্যা", "1"}

def bn(n):
    return str(n).translate(BN_DIGITS)

def esc(s):
    return html.escape(s or "", quote=True)

# ---------------------------------------------------------------- reading
def read_doc(path):
    """Split a file into (front-matter dict, body text)."""
    with open(path, encoding="utf-8-sig") as f:
        text = unicodedata.normalize("NFC", f.read().replace("\r\n", "\n"))
    meta, body = {}, text
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                for l in lines[1:i]:
                    if ":" in l:
                        k, v = l.split(":", 1)
                        meta[k.strip().lower()] = v.strip()
                body = "\n".join(lines[i + 1:])
                break
    return meta, body

def parse_date(s):
    """'১৪/০৫/২০২৪' or '14/05/2024' or '2024-05-14' -> (sort_key, display)."""
    if not s:
        return None, ""
    t = s.translate(EN_DIGITS)
    m = re.match(r"^\s*(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{2,4})\s*$", t)
    m2 = re.match(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*$", t)
    try:
        if m2:
            y, mo, d = map(int, m2.groups())
        elif m:
            d, mo, y = map(int, m.groups())
            if y < 100: y += 2000
        else:
            return None, s
        dt = date(y, mo, d)
        return dt.isoformat(), f"{bn(dt.day)} {MONTHS[dt.month-1]} {bn(dt.year)}"
    except ValueError:
        return None, s

def stanzas(body):
    blocks, cur = [], []
    for raw in body.split("\n"):
        line = raw.strip()
        if line:
            cur.append(line)
        elif cur:
            blocks.append(cur); cur = []
    if cur:
        blocks.append(cur)
    return blocks

def load_poems(sections):
    poems, skipped = [], []
    pdir = os.path.join(ROOT, "poems")
    for dirpath, _, files in os.walk(pdir):
        for fn in sorted(files):
            if not fn.endswith(".txt") or fn.startswith("_"):
                continue
            path = os.path.join(dirpath, fn)
            meta, body = read_doc(path)
            slug = re.sub(r"[^a-z0-9\-]+", "-", fn[:-4].lower()).strip("-")
            if meta.get("hidden", "").lower() in YES:
                skipped.append(slug); continue
            st = stanzas(body)
            if not meta.get("title") or not st:
                print(f"  ! skipped {fn}: missing title or poem text"); continue
            sec = meta.get("section", "").strip()
            if sec not in sections:
                print(f"  ! {fn}: unknown section '{sec}', using 'jibon'")
                sec = "jibon"
            sort_key, date_disp = parse_date(meta.get("date", ""))
            poems.append({
                "slug": slug, "title": meta["title"], "section": sec,
                "date_key": sort_key, "date": date_disp,
                "place": meta.get("place", ""), "dedication": meta.get("dedication", ""),
                "signoff": meta.get("signoff", ""), "stanzas": st,
                "lines": sum(len(s) for s in st),
            })
    poems.sort(key=lambda p: p["title"])
    return poems, skipped

# ---------------------------------------------------------------- links
def link(depth, path=""):
    """Relative link from a page `depth` folders deep to a site path."""
    prefix = "../" * depth
    if path == "" or path.endswith("/"):
        target = prefix + path
        if PREVIEW:
            target += "index.html"
        return target or "./"
    return prefix + path

# ---------------------------------------------------------------- shared html
ICONS = {
    "dice": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="4"/><circle cx="8.5" cy="8.5" r="1.3"/><circle cx="15.5" cy="15.5" r="1.3"/><circle cx="15.5" cy="8.5" r="1.3"/><circle cx="8.5" cy="15.5" r="1.3"/><circle cx="12" cy="12" r="1.3"/></svg>',
    "moon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z"/></svg>',
    "share": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5.5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="18.5" r="2.5"/><path d="m8.2 10.8 7.6-4.1M8.2 13.2l7.6 4.1"/></svg>',
    "search": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/></svg>',
    "left": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.5 5.5 8 12l6.5 6.5"/></svg>',
    "right": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9.5 5.5 16 12l-6.5 6.5"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h10"/></svg>',
}

FLOWER = '''<svg class="shiuli" viewBox="0 0 40 40" aria-hidden="true"><g transform="translate(20 20)">
<path class="pt" d="M0-3C-3-9-2-16 0-18 2-16 3-9 0-3Z"/><path class="pt" transform="rotate(72)" d="M0-3C-3-9-2-16 0-18 2-16 3-9 0-3Z"/>
<path class="pt" transform="rotate(144)" d="M0-3C-3-9-2-16 0-18 2-16 3-9 0-3Z"/><path class="pt" transform="rotate(216)" d="M0-3C-3-9-2-16 0-18 2-16 3-9 0-3Z"/>
<path class="pt" transform="rotate(288)" d="M0-3C-3-9-2-16 0-18 2-16 3-9 0-3Z"/><circle class="ct" r="3.2"/></g></svg>'''

ORNAMENT = '''<svg class="ornament" viewBox="0 0 120 24" aria-hidden="true"><path d="M2 12h40M78 12h40"/>
<path d="M60 3c4 4 4 14 0 18-4-4-4-14 0-18Z"/><path d="M60 12c6-6 13-6 16 0-3 6-10 6-16 0Z"/><path d="M60 12c-6-6-13-6-16 0 3 6 10 6 16 0Z"/>
<circle cx="60" cy="12" r="1.6"/></svg>'''

def page(cfg, *, depth, title, body, desc="", cls="", canonical="", data_json=""):
    full_title = f"{title} · {cfg['site_title']}" if title != cfg["site_title"] else title
    desc = desc or cfg["tagline"]
    canon = cfg["base_url"].rstrip("/") + "/" + canonical
    nav = [("", "প্রথম পাতা", "home"), ("kobita/", "সব কবিতা", "all"), ("kobi/", "কবি পরিচিতি", "about")]
    nav_html = "".join(
        f'<a href="{link(depth, p)}" data-nav="{k}">{esc(n)}</a>' for p, n, k in nav)
    return f'''<!DOCTYPE html>
<html lang="bn" class="no-js" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{esc(cfg['site_title'])}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canon)}">
<link rel="canonical" href="{esc(canon)}">
<meta name="theme-color" content="#f5eee1">
<link rel="icon" href="{link(depth, 'assets/favicon.svg')}" type="image/svg+xml">
<link rel="preload" href="{link(depth, 'assets/fonts/tiro-bangla-bengali-400-normal.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{link(depth, 'assets/fonts/galada-bengali-400-normal.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{link(depth, 'assets/style.css')}">
<script>try{{var t=localStorage.getItem("rk-theme");if(t){{document.documentElement.dataset.theme=t;if(t=="dark")document.querySelector('meta[name=theme-color]').content="#121620"}}var s=localStorage.getItem("rk-scale");if(s)document.documentElement.style.setProperty("--scale",s)}}catch(e){{}}</script>
</head>
<body class="{cls}">
<div class="progress" aria-hidden="true"></div>
<header class="site-header">
  <a class="brand" href="{link(depth, '')}">{esc(cfg['site_title'])}</a>
  <nav class="nav" id="nav">{nav_html}</nav>
  <div class="tools">
    <button class="icon-btn" data-random title="এলোমেলো একটি কবিতা" aria-label="এলোমেলো একটি কবিতা">{ICONS['dice']}</button>
    <button class="icon-btn" data-theme-toggle title="আলো / আঁধার" aria-label="আলো অথবা আঁধার রং">{ICONS['moon']}</button>
    <button class="icon-btn menu-btn" data-menu aria-label="মেনু" aria-controls="nav">{ICONS['menu']}</button>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  {ORNAMENT}
  <p class="foot-name">{esc(cfg['poet'])}</p>
  <p class="foot-small">সকল কবিতার স্বত্ব কবির · <a href="{link(depth, 'kobita/')}">সব কবিতা</a> · <a href="{link(depth, 'kobi/')}">কবি পরিচিতি</a></p>
</footer>
<div class="toast" role="status" aria-live="polite"></div>
<script id="site-data" type="application/json">{data_json}</script>
<script src="{link(depth, 'assets/app.js')}" defer></script>
</body>
</html>
'''

def excerpt(p, n=4):
    return p["stanzas"][0][:n]

def card(p, depth, secmap, i=0, show_excerpt=2):
    lines = "".join(f"<span>{esc(l)}</span>" for l in excerpt(p, show_excerpt))
    meta = esc(secmap[p["section"]]["name"])
    if p["date"]:
        meta += f' · {esc(p["date"])}'
    return f'''<a class="card reveal" style="--i:{i}" href="{link(depth, 'kobita/' + p['slug'] + '/')}" data-slug="{p['slug']}" data-section="{p['section']}">
  <span class="card-sec sec-{p['section']}">{meta}</span>
  <span class="card-title" data-vt="{p['slug']}">{esc(p['title'])}</span>
  <span class="card-ex">{lines}</span>
</a>'''

# ---------------------------------------------------------------- pages
def build_home(cfg, poems, secs, secmap, data):
    depth = 0
    dated = sorted([p for p in poems if p["date_key"]], key=lambda p: p["date_key"], reverse=True)
    latest = dated[0] if dated else poems[0]
    feat_lines = "".join(f"<span>{esc(l)}</span>" for l in latest["stanzas"][0])
    recent = "".join(card(p, depth, secmap, i) for i, p in enumerate(dated[1:4]))
    sec_cards = []
    for i, s in enumerate(secs):
        sample = [p["title"] for p in poems if p["section"] == s["slug"]][:3]
        sec_cards.append(f'''<a class="sec-card reveal sec-{s['slug']}" style="--i:{i}" href="{link(depth, 'kobita/')}{'' if not PREVIEW else ''}#{s['slug']}">
  <span class="sec-count">{bn(s['count'])}টি কবিতা</span>
  <span class="sec-name">{esc(s['name'])}</span>
  <span class="sec-blurb">{esc(s['blurb'])}</span>
  <span class="sec-sample">{esc(' · '.join(sample))}</span>
</a>''')
    flowers = "".join(f'<span class="fall" style="--x:{x}%;--d:{d}s;--t:{t}s;--s:{sc}">{FLOWER}</span>'
                      for x, d, t, sc in [(4,-3,13,1.1),(13,-9,16,.8),(24,-1,14,1.3),(36,-12,17,.9),(47,-6,15,1.2),
                                          (58,-14,18,.85),(69,-4,14,1.25),(80,-10,16,1),(90,-7,13,1.15),(97,-2,17,.8)])
    body = f'''
<section class="hero">
  <div class="petals" aria-hidden="true">{flowers}</div>
  <p class="eyebrow reveal" style="--i:0">কবিতার খাতা</p>
  <h1 class="hero-name reveal" style="--i:1">{esc(cfg['poet'].split('(')[0].strip())}</h1>
  <svg class="scribble" viewBox="0 0 400 24" preserveAspectRatio="none" aria-hidden="true"><path d="M4 16C70 6 130 20 200 12S330 4 396 14"/></svg>
  <p class="hero-tag reveal" style="--i:2">{esc(cfg['tagline'])}</p>
  <p class="hero-stats reveal" style="--i:3"><b>{bn(len(poems))}</b>টি কবিতা · <b>{bn(len(secs))}</b>টি বিষয়</p>
  <div class="hero-cta reveal" style="--i:4">
    <a class="btn primary" href="{link(depth, 'kobita/')}">কবিতা পড়ুন</a>
    <button class="btn ghost" data-random>{ICONS['dice']} এলোমেলো একটি</button>
  </div>
</section>

<section class="block">
  <div class="block-head reveal"><h2>নতুন কবিতা</h2><span class="rule"></span></div>
  <a class="featured reveal" href="{link(depth, 'kobita/' + latest['slug'] + '/')}" data-slug="{latest['slug']}">
    <span class="card-sec sec-{latest['section']}">{esc(secmap[latest['section']]['name'])}{' · ' + esc(latest['date']) if latest['date'] else ''}</span>
    <span class="featured-title card-title" data-vt="{latest['slug']}">{esc(latest['title'])}</span>
    <span class="featured-lines">{feat_lines}</span>
    <span class="more">পুরো কবিতা পড়ুন →</span>
  </a>
  <div class="grid three">{recent}</div>
</section>

<section class="block daily-wrap" hidden>
  <div class="block-head reveal"><h2>আজকের কবিতা</h2><span class="rule"></span></div>
  <a class="daily reveal" href="#"></a>
</section>

<section class="block">
  <div class="block-head reveal"><h2>বিষয় অনুযায়ী</h2><span class="rule"></span></div>
  <div class="grid sections">{''.join(sec_cards)}</div>
</section>
'''
    return page(cfg, depth=depth, title=cfg["site_title"], body=body, cls="home", data_json=data)

def build_index(cfg, poems, secs, secmap, data):
    depth = 1
    chips = ['<button class="chip active" data-filter="all">সব <small>' + bn(len(poems)) + '</small></button>']
    chips += [f'<button class="chip sec-{s["slug"]}" data-filter="{s["slug"]}">{esc(s["name"])} <small>{bn(s["count"])}</small></button>' for s in secs]
    cards = "".join(card(p, depth, secmap, i % 9) for i, p in enumerate(poems))
    body = f'''
<section class="page-head">
  <p class="eyebrow reveal" style="--i:0">সূচিপত্র</p>
  <h1 class="page-title reveal" style="--i:1">সব কবিতা</h1>
  <label class="search reveal" style="--i:2">{ICONS['search']}
    <input type="search" id="q" placeholder="কবিতার নাম বা কোনো পঙ্‌ক্তি লিখে খুঁজুন…" autocomplete="off">
  </label>
  <div class="chips reveal" style="--i:3" role="toolbar" aria-label="বিষয়">{''.join(chips)}</div>
  <p class="result-count" aria-live="polite"></p>
</section>
<section class="block tight">
  <div class="grid cards" id="cards">{cards}</div>
  <p class="empty" hidden>কিছু পাওয়া যায়নি। অন্য কোনো শব্দ লিখে দেখুন।</p>
</section>
'''
    return page(cfg, depth=depth, title="সব কবিতা", body=body, cls="index", canonical="kobita/", data_json=data)

def build_poem(cfg, p, poems, secmap, data):
    depth = 2
    same = [q for q in poems if q["section"] == p["section"]]
    i = same.index(p)
    prev_p, next_p = same[i - 1], same[(i + 1) % len(same)]
    li = 0
    st_html = []
    for s in p["stanzas"]:
        ls = []
        for j, l in enumerate(s):
            ls.append(f'<span class="line" style="--j:{j}">{esc(l)}</span>')
            li += 1
        st_html.append(f'<p class="stanza">{"".join(ls)}</p>')
    more = [q for q in same if q is not p][:6]
    more_html = "".join(f'<a href="{link(depth, "kobita/" + q["slug"] + "/")}">{esc(q["title"])}</a>' for q in more)
    foot = []
    if p["place"]: foot.append(esc(p["place"]))
    if p["date"]: foot.append(esc(p["date"]))
    ded = f'<p class="dedication">{esc(p["dedication"])}</p>' if p["dedication"] else ""
    sign = f'<p class="signoff">{esc(p["signoff"])}</p>' if p["signoff"] else ""
    sec = secmap[p["section"]]
    body = f'''
<article class="poem" data-slug="{p['slug']}">
  <a class="crumb sec-{p['section']}" href="{link(depth, 'kobita/')}#{p['section']}">{esc(sec['name'])}</a>
  <h1 class="poem-title">{esc(p['title'])}</h1>
  <p class="byline">{esc(cfg['poet'])}</p>
  {ded}
  <div class="poem-body">
    {''.join(st_html)}
  </div>
  {sign}
  {ORNAMENT}
  {'<p class="written">' + ' · '.join(foot) + '</p>' if foot else ''}

  <div class="poem-tools">
    <div class="sizer" role="group" aria-label="লেখার আকার">
      <button data-size="-1" aria-label="ছোট লেখা">অ−</button>
      <button data-size="1" aria-label="বড় লেখা">অ+</button>
    </div>
    <button class="btn ghost small" data-share>{ICONS['share']} শেয়ার করুন</button>
  </div>
  <div class="share-panel" hidden>
    <a data-wa target="_blank" rel="noopener">হোয়াটসঅ্যাপ</a>
    <a data-fb target="_blank" rel="noopener">ফেসবুক</a>
    <button data-copy>লিংক কপি</button>
  </div>
</article>

<nav class="pager" aria-label="আরও কবিতা">
  <a class="pg prev" href="{link(depth, 'kobita/' + prev_p['slug'] + '/')}" data-key="ArrowLeft">{ICONS['left']}<span><small>আগের</small>{esc(prev_p['title'])}</span></a>
  <a class="pg next" href="{link(depth, 'kobita/' + next_p['slug'] + '/')}" data-key="ArrowRight"><span><small>পরের</small>{esc(next_p['title'])}</span>{ICONS['right']}</a>
</nav>
{'<section class="more-from"><h2>' + esc(sec['name']) + ' — আরও পড়ুন</h2><div class="more-list">' + more_html + '</div></section>' if more_html else ''}
'''
    desc = " / ".join(p["stanzas"][0][:2])
    return page(cfg, depth=depth, title=p["title"], body=body, desc=desc, cls="poem-page",
                canonical=f"kobita/{p['slug']}/", data_json=data)

def build_about(cfg, poems, secs, data):
    depth = 1
    meta, body_txt = read_doc(os.path.join(ROOT, "about.txt"))
    paras = "".join(f'<p class="reveal" style="--i:{i+2}">{esc(" ".join(s))}</p>'
                    for i, s in enumerate(stanzas(body_txt)))
    photo_src = None
    for ext in ("jpg", "jpeg", "png", "webp"):
        if os.path.exists(os.path.join(ROOT, f"kobi.{ext}")):
            photo_src = f"kobi.{ext}"
    photo = (f'<img class="portrait" src="{link(depth, "assets/" + photo_src)}" alt="{esc(cfg["poet"])}">'
             if photo_src else f'<div class="portrait mono" aria-hidden="true">{esc(cfg["poet_short"][:2])}</div>')
    dated = sorted(p["date_key"] for p in poems if p["date_key"])
    stats = [f"<b>{bn(len(poems))}</b><span>কবিতা</span>", f"<b>{bn(len(secs))}</b><span>বিষয়</span>"]
    if dated:
        stats.append(f"<b>{bn(dated[0][:4])}–{bn(dated[-1][:4])}</b><span>তারিখযুক্ত লেখা</span>")
    body = f'''
<section class="about">
  <div class="reveal" style="--i:0">{photo}</div>
  <h1 class="page-title reveal" style="--i:1">{esc(meta.get('title', 'কবি পরিচিতি'))}</h1>
  <p class="byline">{esc(cfg['poet'])}</p>
  <div class="about-text">{paras}</div>
  <div class="stats reveal">{''.join(f'<div>{s}</div>' for s in stats)}</div>
  <a class="btn primary" href="{link(depth, 'kobita/')}">কবিতাগুলো পড়ুন</a>
</section>
'''
    return page(cfg, depth=depth, title="কবি পরিচিতি", body=body, cls="about-page", canonical="kobi/", data_json=data)

def build_404(cfg, data):
    body = f'''<section class="page-head center"><p class="eyebrow">৪০৪</p>
<h1 class="page-title">পাতাটি খুঁজে পাওয়া গেল না</h1>
<p class="hero-tag">হয়তো ঠিকানাটা বদলে গেছে। চাইলে একটি কবিতা পড়ে আসুন।</p>
<div class="hero-cta"><a class="btn primary" href="/">প্রথম পাতা</a><button class="btn ghost" data-random>{ICONS['dice']} এলোমেলো একটি</button></div></section>'''
    # 404 is served from any depth, so it uses root-absolute links
    return page(cfg, depth=0, title="পাওয়া যায়নি", body=body, cls="notfound", data_json=data).replace('href="assets/', 'href="/assets/').replace('"assets/fonts', '"/assets/fonts').replace('src="assets/', 'src="/assets/').replace('href="kobita/', 'href="/kobita/').replace('href="kobi/', 'href="/kobi/').replace('href="./"', 'href="/"')

# ---------------------------------------------------------------- main
def write(rel, content):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    with open(os.path.join(ROOT, "site.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    secmap = {s["slug"]: s for s in cfg["sections"]}
    poems, hidden = load_poems(secmap)
    if not poems:
        sys.exit("No poems found in poems/")
    secs = []
    for s in cfg["sections"]:
        c = sum(1 for p in poems if p["section"] == s["slug"])
        if c:
            secs.append(dict(s, count=c))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # small index used by search, random-poem and poem-of-the-day
    def data_for(depth):
        return json.dumps({
            "root": link(depth, ""),
            "preview": PREVIEW,
            "sections": {s["slug"]: s["name"] for s in secs},
            "poems": [{"s": p["slug"], "t": p["title"], "c": p["section"],
                       "u": link(depth, "kobita/" + p["slug"] + "/"),
                       "x": p["stanzas"][0][:4]} for p in poems],
        }, ensure_ascii=False).replace("</", "<\\/")

    write("index.html", build_home(cfg, poems, secs, secmap, data_for(0)))
    write("kobita/index.html", build_index(cfg, poems, secs, secmap, data_for(1)))
    for p in poems:
        write(f"kobita/{p['slug']}/index.html", build_poem(cfg, p, poems, secmap, data_for(2)))
    write("kobi/index.html", build_about(cfg, poems, secs, data_for(1)))
    write("404.html", build_404(cfg, data_for(0)))

    # full text for search (loaded only when someone searches)
    write("assets/search.json", json.dumps(
        {p["slug"]: "\n".join("\n".join(s) for s in p["stanzas"]) for p in poems}, ensure_ascii=False))

    theme = os.path.join(ROOT, "theme")
    shutil.copytree(theme, os.path.join(OUT, "assets"), dirs_exist_ok=True)
    for ext in ("jpg", "jpeg", "png", "webp"):
        src = os.path.join(ROOT, f"kobi.{ext}")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(OUT, "assets", f"kobi.{ext}"))
    write(".nojekyll", "")

    print(f"Built {len(poems)} poems in {len(secs)} sections"
          + (f" ({len(hidden)} hidden: {', '.join(hidden)})" if hidden else ""))

if __name__ == "__main__":
    main()