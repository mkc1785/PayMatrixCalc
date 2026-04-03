"""
sitemap_and_index.py — Regenerates sitemap.xml from all HTML files,
then pings new URLs via IndexNow (Bing/Yandex) and Google Indexing API.
Reads new URLs from config/new_pages.txt.
"""

import os, json, requests
from datetime import datetime, date
from glob import glob
from deploy import deploy_file

SITE_URL       = "https://paymatrixcalc.com"
INDEXNOW_KEY   = os.environ.get("INDEXNOW_KEY","")
NEW_PAGES_FILE = "config/new_pages.txt"

# Priority map
PRIORITIES = {
    "/":                          ("1.0","daily"),
    "/8th-cpc-calculator":        ("1.0","weekly"),
    "/pay-matrix":                ("0.9","monthly"),
    "/da-calculator":             ("0.9","weekly"),
    "/hra-calculator":            ("0.9","monthly"),
    "/tax-calculator":            ("0.9","monthly"),
    "/nps-calculator":            ("0.8","monthly"),
    "/gratuity-calculator":       ("0.8","monthly"),
    "/leave-encashment-calculator":("0.8","monthly"),
    "/gpf-calculator":            ("0.8","monthly"),
    "/macp-calculator":           ("0.8","monthly"),
    "/blog/":                     ("0.9","weekly"),
}

def discover_urls():
    urls = []
    # Root HTML files
    for f in glob("*.html"):
        slug = "/" + f.replace(".html","")
        if slug == "/index": slug = "/"
        urls.append(slug)
    # Blog posts
    for f in glob("blog/*.html"):
        if "index" in f:
            urls.append("/blog/")
        else:
            urls.append("/" + f)
    # Remove duplicates, sort
    return sorted(set(urls))

def build_sitemap(urls):
    today = date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        prio, freq = PRIORITIES.get(u, ("0.7","monthly"))
        lines.append(f'  <url><loc>{SITE_URL}{u}</loc>'
                     f'<lastmod>{today}</lastmod>'
                     f'<changefreq>{freq}</changefreq>'
                     f'<priority>{prio}</priority></url>')
    lines.append('</urlset>')
    content = "\n".join(lines)
    with open("sitemap.xml","w") as f:
        f.write(content)
    print(f"✅ sitemap.xml updated with {len(urls)} URLs")
    return content

def ping_indexnow(new_urls):
    if not INDEXNOW_KEY or not new_urls:
        return
    payload = {
        "host": "paymatrixcalc.com",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": [f"{SITE_URL}{u}" if u.startswith("/") else u for u in new_urls]
    }
    try:
        r = requests.post("https://api.indexnow.org/indexnow", json=payload, timeout=10)
        print(f"✅ IndexNow ping: {r.status_code} for {len(new_urls)} URLs")
    except Exception as e:
        print(f"⚠️ IndexNow failed: {e}")

def ping_google_indexing(new_urls):
    """
    Google Indexing API via service account.
    Reads GOOGLE_SA_JSON env var (the full JSON key as string).
    """
    sa_json = os.environ.get("GOOGLE_SA_JSON","")
    if not sa_json or not new_urls:
        print("⚠️ No Google SA JSON — skipping Google Indexing API")
        return
    try:
        import google.oauth2.service_account as sa
        import google.auth.transport.requests as ga_req
        creds_info = json.loads(sa_json)
        creds = sa.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/indexing"]
        )
        creds.refresh(ga_req.Request())
        token = creds.token
        headers = {"Authorization": f"Bearer {token}", "Content-Type":"application/json"}
        for url in new_urls[:200]:  # API limit 200/day
            full_url = f"{SITE_URL}{url}" if url.startswith("/") else url
            payload = {"url": full_url, "type": "URL_UPDATED"}
            r = requests.post(
                "https://indexing.googleapis.com/v3/urlNotifications:publish",
                json=payload, headers=headers, timeout=10
            )
            print(f"  Google index: {r.status_code} {full_url}")
    except Exception as e:
        print(f"⚠️ Google Indexing API error: {e}")

def get_new_pages():
    if not os.path.exists(NEW_PAGES_FILE):
        return []
    with open(NEW_PAGES_FILE) as f:
        urls = [l.strip() for l in f if l.strip()]
    # Clear the file after reading
    open(NEW_PAGES_FILE,"w").close()
    return urls

def main():
    urls = discover_urls()
    build_sitemap(urls)
    deploy_file("sitemap.xml", "")
    new_pages = get_new_pages()
    if new_pages:
        print(f"📡 Pinging {len(new_pages)} new URLs...")
        ping_indexnow(new_pages)
        ping_google_indexing(new_pages)
    else:
        print("No new pages to ping today.")

if __name__ == "__main__":
    main()
