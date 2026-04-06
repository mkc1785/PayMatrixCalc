"""
blog_writer.py — Reads next keyword from config/keywords.txt,
calls Gemini 2.0 Flash, saves complete blog HTML to blog/ folder.
Matches exact blog post template of paymatrixcalc.com.
"""

import json, os, re, requests, sys
from datetime import datetime
from deploy import deploy_file

KEYWORDS_FILE  = "config/keywords.txt"
WRITTEN_FILE   = "config/written_posts.json"
GEMINI_API_KEY  = os.environ["GEMINI_API_KEY"]
GEMINI_API_KEY_2 = os.environ.get("GEMINI_API_KEY_2", "")
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

BLOG_SYSTEM = """You are an expert Indian government salary and finance writer with 16 years of experience as a Central Government PSU employee. Write authoritative, accurate, helpful content.
Output ONLY complete HTML. No markdown. No code fences. No explanation.
Tone: Professional but plain English. Like a knowledgeable colleague explaining to a colleague.
Facts: All DA rates, HRA slabs, NPS rules must be accurate as of 2026 (DA=60% Jan 2026, etc.)
"""

NAV_BLOG = """<nav>
<div class="nav-inner">
  <a href="/" class="logo">
    <div class="logo-dot">Rs</div>
    <div class="logo-text">PayMatrixCalc<span>India's Govt Pay Calculator</span></div>
  </a>
  <div class="nav-links">
    <a href="/">7th CPC</a><a href="/da-calculator">DA Calc</a>
    <a href="/hra-calculator">HRA</a><a href="/tax-calculator">Income Tax</a>
    <a href="/nps-calculator">NPS</a><a href="/gratuity-calculator">Gratuity</a>
    <a href="/pay-matrix">Pay Matrix</a><a href="/blog/" class="active">Blog</a>
  </div>
  <button class="hamburger" onclick="toggleMenu()" aria-label="Menu">&#9776;</button>
</div>
<div class="mobile-menu" id="mobileMenu">
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
</nav>"""

FOOTER_BLOG = """<footer>
<div class="footer-inner">
  <div class="footer-grid">
    <div class="footer-brand">
      <a href="/" style="display:inline-flex;align-items:center;gap:10px;text-decoration:none;margin-bottom:10px">
        <div style="width:36px;height:36px;background:var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;color:var(--navy);font-weight:bold;font-family:serif">Rs</div>
        <div style="font-family:Georgia,serif;font-size:16px;font-weight:bold;color:white;line-height:1.2">PayMatrixCalc<span style="display:block;font-size:.7em;color:var(--gold);font-weight:normal">India's #1 Govt Pay Calculator</span></div>
      </a>
      <p>Free salary calculators for Central Government and PSU employees. Updated after every Cabinet revision.</p>
    </div>
    <div class="footer-col">
      <h4>Calculators</h4>
      <a href="/">7th CPC Salary</a><a href="/pay-matrix">Pay Matrix Table</a>
      <a href="/8th-cpc-calculator">8th CPC Projected</a><a href="/da-calculator">DA &amp; Arrears</a>
      <a href="/hra-calculator">HRA</a><a href="/tax-calculator">Income Tax</a>
      <a href="/nps-calculator">NPS Pension</a><a href="/gratuity-calculator">Gratuity</a>
      <a href="/leave-encashment-calculator">Leave Encashment</a>
      <a href="/gpf-calculator">GPF Interest</a><a href="/macp-calculator">MACP Calculator</a>
    </div>
    <div class="footer-col">
      <h4>Resources</h4>
      <a href="/blog/">Blog</a><a href="/about">About</a><a href="/contact">Contact</a>
      <a href="/privacy">Privacy Policy</a><a href="/disclaimer">Disclaimer</a><a href="/terms">Terms of Use</a>
    </div>
  </div>
  <div class="footer-bottom">
    <p>&#169; 2026 PayMatrixCalc &middot; All rights reserved</p>
    <p>Educational purposes only. Not financial or legal advice. Verify with your DDO/PAO.</p>
  </div>
</div>
</footer>"""

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
        print(f"  ⚠️ Key {key_idx + 1} exhausted after {retries} retries. Trying next key...")
    print("  ⚠️ All API keys exhausted. Skipping blog post today.")
    return None

def keyword_to_slug(kw):
    slug = re.sub(r'[^a-z0-9\s]','', kw.lower())
    return re.sub(r'\s+','-', slug.strip())[:80]

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

    prompt = f"""{BLOG_SYSTEM}

NAV TO USE EXACTLY:
{NAV_BLOG}

FOOTER TO USE EXACTLY:
{FOOTER_BLOG}

WRITE A BLOG POST FOR:
Target keyword: "{keyword}"
URL: https://paymatrixcalc.com/blog/{slug}.html
Date: {date_str}

Structure (match exactly to existing paymatrixcalc.com blog posts):

<!DOCTYPE html>
<html lang="en">
<head>
  [GA4 tag G-Q8D66EKSSK]
  [meta charset, viewport]
  <title>[SEO title 55-60 chars] | PayMatrixCalc</title>
  <meta name="description" content="[150 chars max, include keyword]">
  <link rel="canonical" href="https://paymatrixcalc.com/blog/{slug}.html">
  [OG tags: title, description, url, type=article]
  [google-site-verification: s-bnDE3I-Z-8WI7tdNin-OYBULSlzSpNYAEugUXKejI]
  [favicon inline SVG matching site]
  [manifest, theme-color]
  [FAQPage JSON-LD schema with 4-5 questions]
  [Article JSON-LD schema]
  <style>
    [Full CSS matching paymatrixcalc.com blog style - :root vars, nav, footer, article, calc-cta, data-table, page-hero, breadcrumb, mobile styles]
  </style>
</head>
<body>
[NAV - exact copy above]
<div class="page-hero">
  <div style="max-width:820px;margin:0 auto">
    <div class="badge">[Category e.g. "7th Pay Commission"]</div>
    <h1>[H1 matching keyword intent, 50-65 chars]</h1>
    <div class="meta">📅 {date_str} · [X] min read · Written by a Central Govt PSU employee</div>
  </div>
</div>
<div class="breadcrumb"><a href="/">Home</a> › <a href="/blog/">Blog</a> › [Article Title]</div>
<div class="article-wrap">
  <article class="article">
    [Opening paragraph: direct answer to search query in first 100 words]
    [H2 section 1]
    [content with real numbers, formulas, examples]
    [calc-cta box linking to most relevant calculator on paymatrixcalc.com]
    [H2 section 2]
    [data-table where relevant]
    [H2 section 3]
    [worked example with specific numbers - Level 7 employee typical]
    [calc-cta box - second one]
    [H2 "Frequently Asked Questions"]
    [4-5 FAQ items matching FAQPage schema above]
  </article>
</div>
[FOOTER - exact copy above]
[JS: toggleMenu function]
</body>
</html>

Content requirements:
- 1,200-1,500 words total
- All facts accurate as of March 2026
- At least one data table with real numbers
- At least one worked example (Level 6 or Level 7 employee)
- 2 calc-cta blocks linking to calculators on paymatrixcalc.com
- Answer starts directly (no "In this article we will...")
- Short sentences. No jargon without explanation.

Output the complete HTML file only. Start with <!DOCTYPE html>."""

    html = call_gemini(prompt)
    if html is None:
        return None, None
    html = re.sub(r'^```html?\n?','', html.strip())
    html = re.sub(r'\n?```$','', html)
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

    # Log
    written = json.load(open(WRITTEN_FILE)) if os.path.exists(WRITTEN_FILE) else []
    written.append({"keyword": keyword, "slug": slug, "date": datetime.utcnow().strftime("%Y-%m-%d")})
    json.dump(written, open(WRITTEN_FILE,"w"), indent=2)

    # Trigger sitemap/indexing
    with open("config/new_pages.txt","a") as f:
        f.write(f"https://paymatrixcalc.com/blog/{slug}.html\n")

if __name__ == "__main__":
    main()
