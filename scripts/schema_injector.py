"""
schema_injector.py — Injects/updates FAQPage + HowTo JSON-LD into all
calculator HTML pages that don't have it yet.
Calls Gemini to generate page-specific FAQ content.
Runs on every deploy to catch new pages.
"""

import json, os, re, requests
from glob import glob
from deploy import deploy_file

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
INJECTED_LOG   = "config/schema_injected.json"

# Calculator pages to process (not blog posts - they get schema from blog_writer)
CALC_PAGES = [
    "index.html",
    "da-calculator.html",
    "hra-calculator.html",
    "tax-calculator.html",
    "nps-calculator.html",
    "gratuity-calculator.html",
    "leave-encashment-calculator.html",
    "gpf-calculator.html",
    "macp-calculator.html",
    "pay-matrix.html",
    "8th-cpc-calculator.html",
]

def call_gemini(prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}
    }
    r = requests.post(
        GEMINI_URL, json=payload,
        headers={"Content-Type":"application/json"},
        params={"key": GEMINI_API_KEY},
        timeout=60
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def generate_faq_schema(page_file, title_tag):
    prompt = f"""Generate a FAQPage JSON-LD schema for this Indian government salary calculator page:
Page: {page_file}
Title: {title_tag}

Output ONLY the JSON-LD script tag. No explanation. No markdown.
Include 4 highly specific, useful FAQ items that a Central Govt employee would actually ask.
Use real values: DA=60% (Jan 2026), 7th CPC levels 1-18, etc.
Format:
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[...]}}
</script>"""
    result = call_gemini(prompt)
    # Ensure clean output
    result = result.strip()
    if not result.startswith('<script'):
        # Find script tag if buried
        match = re.search(r'<script type="application/ld\+json">.*?</script>', result, re.DOTALL)
        if match:
            return match.group(0)
    return result

def get_title(html):
    m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    return m.group(1) if m else "Calculator"

def already_has_faq_schema(html):
    return '"FAQPage"' in html

def inject_schema(html, schema_tag):
    # Inject just before </head>
    return html.replace('</head>', f'{schema_tag}\n</head>', 1)

def main():
    injected_log = json.load(open(INJECTED_LOG)) if os.path.exists(INJECTED_LOG) else {}

    for page in CALC_PAGES:
        if not os.path.exists(page):
            continue

        with open(page) as f:
            html = f.read()

        if already_has_faq_schema(html):
            continue  # Already has schema

        title = get_title(html)
        print(f"💉 Injecting schema: {page}")

        try:
            schema_tag = generate_faq_schema(page, title)
            html = inject_schema(html, schema_tag)
            with open(page,"w") as f:
                f.write(html)
            injected_log[page] = True
            print(f"  ✅ Done: {page}")
            remote_path = "blog/" if page.startswith("blog/") else ""
            deploy_file(page, remote_path)
        except Exception as e:
            print(f"  ⚠️ Failed {page}: {e}")

    json.dump(injected_log, open(INJECTED_LOG,"w"), indent=2)

if __name__ == "__main__":
    main()
