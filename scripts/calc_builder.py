"""
calc_builder.py — Takes top opportunity from opportunities.json,
calls Gemini 2.5 Flash-Lite to generate a complete calculator HTML page,
saves it to the site, and marks opportunity as 'built'.
Runs only if score >= 7 (high confidence). Otherwise waits.
"""

import json, os, re, requests
from datetime import datetime

OPPORTUNITIES_FILE = "config/opportunities.json"
BUILT_LOG          = "config/built_calculators.json"
GEMINI_API_KEY     = os.environ["GEMINI_API_KEY"]
GEMINI_URL         = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
CALC_TEMPLATE_FILE = "config/calc_template_snippet.html"
THRESHOLD          = 7  # min score to auto-build

SYSTEM_PROMPT = """You are an expert HTML developer building a free Indian government salary calculator page.
Output ONLY valid, complete HTML. No markdown, no code blocks, no explanation.
The page must match this exact design system:
- CSS variables: --navy:#0f2744; --navy2:#1a3a5c; --gold:#d4a017; --cream:#faf7f0; --text:#1a1a2e
- Font: Georgia serif for body, sans-serif for UI elements
- All calculations in pure JavaScript (no external libraries)
- Mobile-first, responsive
- Include: FAQPage JSON-LD schema, HowTo JSON-LD schema, meta title, meta description
- Include a disclaimer: "Based on publicly available rules. Verify with your HR/DDO/PAO."
- Internal links to related calculators on paymatrixcalc.com
- GA4 tag: G-Q8D66EKSSK
- Nav and footer matching paymatrixcalc.com exactly (see template below)
"""

NAV_HTML = """<nav>
<div class="nav-inner">
  <a href="/" class="logo">
    <div class="logo-dot">Rs</div>
    <div class="logo-text">PayMatrixCalc<span>India's Govt Pay Calculator</span></div>
  </a>
  <div class="nav-links">
    <a href="/">7th CPC</a>
    <a href="/da-calculator">DA Calc</a>
    <a href="/hra-calculator">HRA</a>
    <a href="/tax-calculator">Income Tax</a>
    <a href="/nps-calculator">NPS</a>
    <a href="/gratuity-calculator">Gratuity</a>
    <a href="/pay-matrix">Pay Matrix</a>
    <a href="/blog/">Blog</a>
    <a href="/8th-cpc-calculator" style="color:var(--gold3)">8th CPC&#127381;</a>
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

FOOTER_HTML = """<footer>
<div class="footer-inner">
  <div class="footer-grid">
    <div class="footer-brand">
      <a href="/" style="display:inline-flex;align-items:center;gap:10px;text-decoration:none;margin-bottom:10px">
        <div style="width:36px;height:36px;background:var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;color:var(--navy);font-weight:bold;font-family:serif">Rs</div>
        <div style="font-family:Georgia,serif;font-size:16px;font-weight:bold;color:white;line-height:1.2">PayMatrixCalc<span style="display:block;font-size:.7em;color:var(--gold);font-weight:normal">India's #1 Govt Pay Calculator</span></div>
      </a>
      <p>Free, accurate salary calculators for Central Government, State Government and PSU employees.</p>
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

def call_gemini(prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 8192}
    }
    r = requests.post(
        GEMINI_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        params={"key": GEMINI_API_KEY},
        timeout=90
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def build_calculator(opportunity):
    query = opportunity["text"]
    slug  = opportunity["slug"]

    prompt = f"""{SYSTEM_PROMPT}

NAV HTML TO USE EXACTLY:
{NAV_HTML}

FOOTER HTML TO USE EXACTLY:
{FOOTER_HTML}

BUILD THIS CALCULATOR:
Query/Topic: "{query}"
URL slug: /{slug}
Canonical URL: https://paymatrixcalc.com/{slug}

Requirements:
1. Complete <!DOCTYPE html> page
2. Title tag: "{query.title()} 2026 | Free Calculator | PayMatrixCalc"
3. Meta description: 80-150 chars, include the formula/benefit
4. H1 matching title intent
5. Working calculator with correct Indian govt formula if applicable
6. Inputs with helper tooltips (like existing calculators)
7. Result display with breakdown table
8. "How to use" section (HowTo schema)
9. 4-5 FAQ items (FAQPage schema)  
10. 1 calc-cta block linking to most relevant existing calculator
11. 600+ words of explanatory content
12. GA4 tag G-Q8D66EKSSK in <head>
13. Google site verification: s-bnDE3I-Z-8WI7tdNin-OYBULSlzSpNYAEugUXKejI
14. If formula is uncertain, show best estimate with disclaimer
15. All JS inline, no external dependencies except Chart.js from cdnjs if needed

Output the complete HTML file only. Start with <!DOCTYPE html>."""

    html = call_gemini(prompt)
    # Strip any accidental markdown fences
    html = re.sub(r'^```html?\n?','', html.strip())
    html = re.sub(r'\n?```$','', html)
    return html

def main():
    if not os.path.exists(OPPORTUNITIES_FILE):
        print("No opportunities file. Run trend_hunter.py first.")
        return

    opps = json.load(open(OPPORTUNITIES_FILE))
    built = json.load(open(BUILT_LOG)) if os.path.exists(BUILT_LOG) else []
    built_slugs = {b["slug"] for b in built}

    # Find highest-scored unbuilt opportunity above threshold
    candidate = None
    for opp in opps:
        if opp["slug"] not in built_slugs and opp["score"] >= THRESHOLD:
            candidate = opp
            break

    if not candidate:
        print("No high-confidence opportunity to build today.")
        return

    print(f"🔨 Building: {candidate['text']} (score={candidate['score']})")
    html = build_calculator(candidate)

    # Save to site root
    out_path = f"{candidate['slug']}.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"✅ Saved: {out_path}")

    # Log as built
    built.append({
        "slug": candidate["slug"],
        "text": candidate["text"],
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "file": out_path
    })
    json.dump(built, open(BUILT_LOG,"w"), indent=2)

    # Remove from opportunities
    opps = [o for o in opps if o["slug"] != candidate["slug"]]
    json.dump(opps, open(OPPORTUNITIES_FILE,"w"), indent=2)

    # Write trigger file for sitemap/indexing scripts
    with open("config/new_pages.txt","a") as f:
        f.write(f"https://paymatrixcalc.com/{candidate['slug']}\n")

if __name__ == "__main__":
    main()
