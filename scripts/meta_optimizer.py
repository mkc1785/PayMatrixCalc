"""
meta_optimizer.py — Weekly script.
Reads GSC performance data via API, finds pages with impressions>10 but CTR<2%,
rewrites title + meta description using Gemini.
"""

import json, os, re, requests
from glob import glob
from deploy import deploy_file

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
GSC_SA_JSON    = os.environ.get("GOOGLE_SA_JSON","")
SITE_URL       = "https://paymatrixcalc.com"

def get_gsc_data():
    """Pull page performance from GSC API."""
    if not GSC_SA_JSON:
        print("⚠️ No GSC service account — using hardcoded low-CTR pages")
        # Fallback: known low-CTR pages from SC data
        return [
            {"page": "/leave-encashment-calculator", "impressions": 27, "ctr": 0.0, "position": 43.8},
            {"page": "/8th-cpc-calculator",          "impressions": 11, "ctr": 0.0, "position": 48.4},
            {"page": "/gpf-calculator",              "impressions": 34, "ctr": 0.0, "position": 16.1},
            {"page": "/macp-calculator",             "impressions": 18, "ctr": 0.0, "position": 9.6},
            {"page": "/da-calculator",               "impressions": 7,  "ctr": 0.0, "position": 17.4},
        ]

    try:
        import google.oauth2.service_account as sa
        import google.auth.transport.requests as ga_req
        creds = sa.Credentials.from_service_account_info(
            json.loads(GSC_SA_JSON),
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )
        creds.refresh(ga_req.Request())
        headers = {"Authorization": f"Bearer {creds.token}"}
        payload = {
            "startDate": "2026-02-25",
            "endDate":   "2026-03-25",
            "dimensions": ["page"],
            "rowLimit": 50
        }
        r = requests.post(
            f"https://searchconsole.googleapis.com/v1/sites/{SITE_URL}/searchAnalytics/query",
            json=payload, headers=headers, timeout=20
        )
        rows = r.json().get("rows",[])
        return [
            {"page": row["keys"][0].replace(SITE_URL,""),
             "impressions": row.get("impressions",0),
             "ctr": row.get("ctr",0),
             "position": row.get("position",99)}
            for row in rows
            if row.get("impressions",0) >= 10 and row.get("ctr",1) < 0.02
        ]
    except Exception as e:
        print(f"⚠️ GSC API error: {e}")
        return []

def get_page_file(page_path):
    """Map URL path to local HTML file."""
    p = page_path.rstrip("/")
    if p == "" or p == "/":
        return "index.html"
    candidates = [
        f"{p.lstrip('/')}.html",
        f"{p.lstrip('/')}/index.html",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def rewrite_meta(page_file, current_title, current_desc, position, impressions):
    prompt = f"""You are an SEO expert. Rewrite the title tag and meta description for this Indian government calculator page to improve click-through rate.

Current title: {current_title}
Current description: {current_desc}
Average search position: {position:.1f}
Monthly impressions: {impressions}

Rules:
- Title: 55-60 characters, include year (2026), include primary keyword, show unique value
- Description: 140-155 characters, start with action verb, include specific benefit, include "free"
- Make it compelling for a Central Govt/PSU employee searching at work
- Mention specific numbers where possible (e.g., "DA 60%", "Level 1-18")

Output ONLY a JSON object like:
{{"title": "...", "description": "..."}}
No explanation. No markdown."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 256}
    }
    r = requests.post(
        GEMINI_URL, json=payload,
        headers={"Content-Type":"application/json"},
        params={"key": GEMINI_API_KEY},
        timeout=30
    )
    r.raise_for_status()
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    raw = re.sub(r'^```json?\n?','',raw)
    raw = re.sub(r'\n?```$','',raw)
    return json.loads(raw)

def apply_meta(html, new_title, new_desc):
    html = re.sub(r'<title>.*?</title>', f'<title>{new_title}</title>', html, flags=re.DOTALL)
    html = re.sub(r'<meta name="description" content=".*?"',
                  f'<meta name="description" content="{new_desc}"', html)
    # Also update OG tags
    html = re.sub(r'<meta property="og:title" content=".*?"',
                  f'<meta property="og:title" content="{new_title}"', html)
    html = re.sub(r'<meta property="og:description" content=".*?"',
                  f'<meta property="og:description" content="{new_desc}"', html)
    return html

def get_current_meta(html):
    title_m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    desc_m  = re.search(r'<meta name="description" content="(.*?)"', html)
    return (title_m.group(1).strip() if title_m else "",
            desc_m.group(1).strip()  if desc_m  else "")

def main():
    low_ctr_pages = get_gsc_data()
    if not low_ctr_pages:
        print("No low-CTR pages to optimize this week.")
        return

    print(f"🎯 Optimizing {len(low_ctr_pages)} low-CTR pages...")
    for page_data in low_ctr_pages:
        page_file = get_page_file(page_data["page"])
        if not page_file:
            print(f"  ⚠️ File not found for: {page_data['page']}")
            continue

        with open(page_file) as f:
            html = f.read()

        current_title, current_desc = get_current_meta(html)
        if not current_title:
            continue

        print(f"  📝 Rewriting: {page_file} (pos={page_data['position']:.1f}, CTR={page_data['ctr']*100:.1f}%)")
        try:
            new_meta = rewrite_meta(page_file, current_title, current_desc,
                                    page_data["position"], page_data["impressions"])
            html = apply_meta(html, new_meta["title"], new_meta["description"])
            with open(page_file,"w") as f:
                f.write(html)
            print(f"    ✅ New title: {new_meta['title']}")
            print(f"    ✅ New desc:  {new_meta['description']}")
            remote_path = "blog/" if page_file.startswith("blog/") else ""
            deploy_file(page_file, remote_path)
            # Queue for re-indexing
            with open("config/new_pages.txt","a") as f:
                f.write(f"https://paymatrixcalc.com{page_data['page']}\n")
        except Exception as e:
            print(f"    ⚠️ Error: {e}")

if __name__ == "__main__":
    main()
