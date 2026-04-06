"""
blog_writer.py — Reads next keyword from config/keywords.txt,
calls Gemini, saves complete blog HTML to blog/ folder.
"""

import json, os, re, requests, sys
from datetime import datetime
from deploy import deploy_file

KEYWORDS_FILE   = "config/keywords.txt"
WRITTEN_FILE    = "config/written_posts.json"
GEMINI_API_KEY  = os.environ["GEMINI_API_KEY"]
GEMINI_API_KEY_2 = os.environ.get("GEMINI_API_KEY_2", "")
GEMINI_URL      = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def call_gemini(prompt, retries=3):
    import time
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192}
    }
    keys = [k for k in [GEMINI_API_KEY, GEMINI_API_KEY_2] if k]
    for key_idx, key in enumerate(keys):
        print(f"  🔑 Trying API key {key_idx + 1}/{len(keys)}...")
        for attempt in range(retries):
            r = requests.post(
                GEMINI_URL, json=payload,
                headers={"Content-Type": "application/json"},
                params={"key": key},
                timeout=90
            )
            if r.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f"  ⏳ Rate limited. Waiting {wait}s before retry {attempt+1}/{retries}...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        print(f"  ⚠️ Key {key_idx + 1} exhausted. Trying next key...")
    print("  ⚠️ All API keys exhausted. Skipping blog post today.")
    return None

def keyword_to_slug(kw):
    slug = re.sub(r'[^a-z0-9\s]', '', kw.lower())
    return re.sub(r'\s+', '-', slug.strip())[:80]

def get_next_keyword():
    if not os.path.exists(KEYWORDS_FILE):
        return None
    written = set()
    if os.path.exists(WRITTEN_FILE):
        written = {p["keyword"] for p in json.load(open(WRITTEN_FILE))}
    with open(KEYWORDS_FILE) as f:
        for line in f:
            kw = line.strip()
            if kw and not kw.startswith("#") and kw not in written:
                return kw
    return None

def build_blog_post(keyword):
    slug = keyword_to_slug(keyword)
    date_str = datetime.utcnow().strftime("%B %Y")

    prompt = f"""You are an expert Indian government salary writer with 16 years experience as a Central Govt PSU employee.

Write a complete blog post HTML file for paymatrixcalc.com.

Target keyword: "{keyword}"
Slug: {slug}
Date: {date_str}
Site: paymatrixcalc.com

RULES:
- Output ONLY raw HTML. No markdown, no code fences, no explanation.
- Facts accurate as of 2026: DA=60% Jan 2026, HRA X=27% Y=18% Z=9%
- 1200-1500 words
- Include one data table with real numbers
- Include one worked example (Level 7 employee)
- Two internal links to calculators on paymatrixcalc.com
- Short sentences. Direct answers. No "In this article..."

HTML STRUCTURE:
<!DOCTYPE html>
<html lang="en">
<head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-Q8D66EKSSK"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-Q8D66EKSSK');</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>[55-60 char SEO title] | PayMatrixCalc</title>
<meta name="description" content="[150 char description with keyword]">
<link rel="canonical" href="https://paymatrixcalc.com/blog/{slug}.html">
<meta property="og:title" content="[title]">
<meta property="og:description" content="[description]">
<meta property="og:url" content="https://paymatrixcalc.com/blog/{slug}.html">
<meta property="og:type" content="article">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0f2744">
<script type="application/ld+json">[FAQPage schema with 4 questions]</script>
<script type="application/ld+json">[Article schema]</script>
<style>
:root{{--navy:#0f2744;--navy2:#1a3a5c;--gold:#d4a017;--gold3:#f5c842;--cream:#faf7f0;--cream2:#f0ebe0;--text:#1a1a2e;--text2:#3d3d5c;--text3:#6b6b8a;--green:#16a34a;--border:#d0c9b8}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Georgia,serif;background:var(--cream);color:var(--text);line-height:1.6}}
a{{color:var(--navy2);text-decoration:none}}a:hover{{color:var(--gold)}}
nav{{position:sticky;top:0;z-index:100;background:var(--navy);border-bottom:3px solid var(--gold)}}
.nav-inner{{max-width:1200px;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between;height:60px}}
.logo{{display:flex;align-items:center;gap:10px;text-decoration:none}}
.logo-dot{{width:32px;height:32px;background:var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;color:var(--navy);font-weight:bold;font-family:sans-serif}}
.logo-text{{font-family:Georgia,serif;font-size:17px;font-weight:bold;color:white;line-height:1.2}}
.logo-text span{{color:var(--gold);display:block;font-size:.7em;font-weight:normal}}
.nav-links{{display:flex;align-items:center;gap:4px}}
.nav-links a{{color:rgba(255,255,255,.85);font-size:13px;padding:6px 11px;border-radius:6px;font-family:sans-serif}}
.nav-links a:hover,.nav-links a.active{{background:rgba(212,160,23,.15);color:var(--gold)}}
.hamburger{{display:none;background:none;border:2px solid rgba(255,255,255,.3);color:white;font-size:20px;width:38px;height:38px;border-radius:6px;cursor:pointer;align-items:center;justify-content:center}}
.mobile-menu{{display:none;position:absolute;top:63px;left:0;right:0;background:var(--navy2);border-bottom:2px solid var(--gold);padding:12px;z-index:99}}
.mobile-menu.open{{display:block}}
.mobile-menu a{{display:block;color:rgba(255,255,255,.9);padding:10px 16px;border-radius:6px;font-family:sans-serif;font-size:14px;margin-bottom:2px}}
.page-hero{{background:linear-gradient(135deg,var(--navy) 0%,var(--navy2) 100%);color:white;padding:48px 20px 36px;text-align:center}}
.page-hero .badge{{display:inline-block;background:rgba(212,160,23,.15);border:1px solid rgba(212,160,23,.4);color:var(--gold3);padding:5px 14px;border-radius:20px;font-size:12px;font-family:sans-serif;margin-bottom:12px}}
.page-hero h1{{font-size:clamp(22px,4vw,34px);font-weight:bold;margin-bottom:10px}}
.page-hero .meta{{font-family:sans-serif;font-size:13px;opacity:.75}}
.breadcrumb{{background:rgba(15,39,68,.05);border-bottom:1px solid var(--border);padding:7px 0;font-family:sans-serif;font-size:12px;color:var(--text3)}}
.breadcrumb-inner{{max-width:820px;margin:0 auto;padding:0 20px}}
.breadcrumb a{{color:var(--navy2)}}
.article-wrap{{max-width:820px;margin:0 auto;padding:32px 20px 48px}}
.article h2{{font-size:22px;color:var(--navy);margin:28px 0 12px}}
.article h3{{font-size:18px;color:var(--navy2);margin:20px 0 8px}}
.article p{{font-family:sans-serif;font-size:15px;color:var(--text2);line-height:1.8;margin-bottom:14px}}
.article ul,.article ol{{margin:10px 0 14px 20px;font-family:sans-serif;font-size:15px;color:var(--text2);line-height:1.8}}
.article strong{{color:var(--navy)}}
.calc-cta{{background:linear-gradient(135deg,var(--navy),var(--navy2));border-radius:12px;padding:20px 24px;margin:24px 0;display:flex;align-items:center;justify-content:space-between;gap:16px;border:1px solid rgba(212,160,23,.3)}}
.calc-cta p{{color:rgba(255,255,255,.85);font-family:sans-serif;font-size:14px;margin:0}}
.calc-cta a{{background:var(--gold);color:var(--navy);padding:10px 20px;border-radius:8px;font-family:sans-serif;font-weight:bold;font-size:14px;white-space:nowrap;flex-shrink:0}}
table{{width:100%;border-collapse:collapse;font-family:sans-serif;font-size:14px;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 10px rgba(15,39,68,.08);margin:20px 0}}
th{{background:var(--navy);color:white;padding:11px 14px;text-align:left;font-size:12px;letter-spacing:.5px;text-transform:uppercase}}
td{{padding:10px 14px;border-bottom:1px solid var(--cream2)}}
tr:last-child td{{border-bottom:none}}
tr:nth-child(even) td{{background:#fafaf8}}
.faq-item{{border-bottom:1px solid var(--cream2);padding:16px 0}}
.faq-item:last-child{{border-bottom:none}}
.faq-item h3{{font-size:16px;font-family:sans-serif;font-weight:600;color:var(--navy);margin-bottom:8px}}
footer{{background:var(--navy);color:white;padding:40px 20px 20px}}
.footer-inner{{max-width:1200px;margin:0 auto}}
.footer-grid{{display:grid;grid-template-columns:2fr 1fr 1fr;gap:32px;margin-bottom:28px}}
.footer-brand p{{font-family:sans-serif;font-size:13px;opacity:.7;margin-top:8px;line-height:1.7}}
.footer-col h4{{font-family:sans-serif;font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--gold);margin-bottom:12px}}
.footer-col a{{display:block;font-family:sans-serif;font-size:13px;opacity:.75;padding:3px 0;color:rgba(255,255,255,.85)}}
.footer-bottom{{border-top:1px solid rgba(255,255,255,.1);padding-top:16px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px}}
.footer-bottom p{{font-family:sans-serif;font-size:12px;opacity:.6;color:white}}
@media(max-width:768px){{.nav-links{{display:none}}.hamburger{{display:flex}}.footer-grid{{grid-template-columns:1fr}}.calc-cta{{flex-direction:column}}}}
</style>
</head>
<body>
<nav>
<div class="nav-inner">
  <a href="/" class="logo"><div class="logo-dot">Rs</div><div class="logo-text">PayMatrixCalc<span>India's Govt Pay Calculator</span></div></a>
  <div class="nav-links">
    <a href="/">7th CPC</a><a href="/da-calculator">DA Calc</a><a href="/hra-calculator">HRA</a>
    <a href="/tax-calculator">Income Tax</a><a href="/nps-calculator">NPS</a>
    <a href="/pay-matrix">Pay Matrix</a><a href="/blog/" class="active">Blog</a>
  </div>
  <button class="hamburger" onclick="this.closest('nav').querySelector('.mobile-menu').classList.toggle('open')" aria-label="Menu">&#9776;</button>
</div>
<div class="mobile-menu">
  <a href="/">&#127968; 7th CPC Salary Calculator</a>
  <a href="/da-calculator">&#128200; DA &amp; Arrears Calculator</a>
  <a href="/hra-calculator">&#127968; HRA Calculator</a>
  <a href="/tax-calculator">&#128188; Income Tax Calculator</a>
  <a href="/nps-calculator">&#127970; NPS Pension Calculator</a>
  <a href="/gratuity-calculator">&#127873; Gratuity Calculator</a>
  <a href="/pay-matrix">&#128202; Pay Matrix Table</a>
  <a href="/8th-cpc-calculator" style="color:var(--gold3)">&#127381; 8th CPC Calculator</a>
  <a href="/blog/" style="color:var(--gold3)">&#128196; Blog</a>
  <a href="/about">About</a><a href="/contact">Contact</a>
</div>
</nav>
<div class="page-hero">
  <div style="max-width:820px;margin:0 auto">
    <div class="badge">[CATEGORY]</div>
    <h1>[H1 TITLE]</h1>
    <div class="meta">&#128197; {date_str} &middot; [X] min read &middot; Written by a Central Govt PSU employee</div>
  </div>
</div>
<div class="breadcrumb"><div class="breadcrumb-inner"><a href="/">Home</a> &rsaquo; <a href="/blog/">Blog</a> &rsaquo; [SHORT TITLE]</div></div>
<div class="article-wrap">
  <article class="article">
    [FULL ARTICLE CONTENT — opening para, h2 sections, table, worked example, 2 calc-cta blocks, FAQ section]
  </article>
</div>
<footer>
<div class="footer-inner">
  <div class="footer-grid">
    <div class="footer-brand">
      <a href="/" style="display:inline-flex;align-items:center;gap:10px;text-decoration:none;margin-bottom:10px">
        <div style="width:36px;height:36px;background:var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;color:var(--navy);font-weight:bold;font-family:serif">Rs</div>
        <div style="font-family:Georgia,serif;font-size:16px;font-weight:bold;color:white;line-height:1.2">PayMatrixCalc<span style="display:block;font-size:.7em;color:var(--gold);font-weight:normal">India's #1 Govt Pay Calculator</span></div>
      </a>
      <p>Free salary calculators for Central Government and PSU employees.</p>
    </div>
    <div class="footer-col"><h4>Calculators</h4>
      <a href="/">7th CPC Salary</a><a href="/pay-matrix">Pay Matrix Table</a>
      <a href="/8th-cpc-calculator">8th CPC Projected</a><a href="/da-calculator">DA &amp; Arrears</a>
      <a href="/hra-calculator">HRA</a><a href="/tax-calculator">Income Tax</a>
      <a href="/nps-calculator">NPS Pension</a><a href="/gratuity-calculator">Gratuity</a>
      <a href="/leave-encashment-calculator">Leave Encashment</a>
      <a href="/gpf-calculator">GPF Interest</a><a href="/macp-calculator">MACP Calculator</a>
    </div>
    <div class="footer-col"><h4>Resources</h4>
      <a href="/blog/">Blog</a><a href="/about">About</a><a href="/contact">Contact</a>
      <a href="/privacy">Privacy Policy</a><a href="/disclaimer">Disclaimer</a><a href="/terms">Terms of Use</a>
    </div>
  </div>
  <div class="footer-bottom">
    <p>&#169; 2026 PayMatrixCalc &middot; All rights reserved</p>
    <p>Educational purposes only. Not financial or legal advice.</p>
  </div>
</div>
</footer>
</body>
</html>

Fill in all [PLACEHOLDERS] with real content for the keyword "{keyword}". Output complete HTML only."""

    html = call_gemini(prompt)
    if html is None:
        return None, None
    html = re.sub(r'^```html?\n?', '', html.strip())
    html = re.sub(r'\n?```$', '', html)
    return html, slug

def main():
    keyword = get_next_keyword()
    if not keyword:
        print("No more keywords in queue. Add more to config/keywords.txt")
        return

    print(f"✍️  Writing post: {keyword}")
    html, slug = build_blog_post(keyword)

    if html is None:
        print("  ⏭️ Skipping today — all keys exhausted. Will retry tomorrow.")
        sys.exit(0)

    os.makedirs("blog", exist_ok=True)
    out_path = f"blog/{slug}.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"✅ Saved: {out_path}")
    deploy_file(out_path, "blog/")

    written = json.load(open(WRITTEN_FILE)) if os.path.exists(WRITTEN_FILE) else []
    written.append({"keyword": keyword, "slug": slug, "date": datetime.utcnow().strftime("%Y-%m-%d")})
    json.dump(written, open(WRITTEN_FILE, "w"), indent=2)

    with open("config/new_pages.txt", "a") as f:
        f.write(f"https://paymatrixcalc.com/blog/{slug}.html\n")

if __name__ == "__main__":
    main()
