"""
trend_hunter.py — Discovers emerging calculator demand from 4 free sources.
Saves scored opportunities to config/opportunities.json for calc_builder.py to pick up.
Sources: Google Autocomplete, Reddit RSS, Google News RSS, pytrends.
"""

import json, re, time, os, requests
from datetime import datetime
from xml.etree import ElementTree as ET

OPPORTUNITIES_FILE = "config/opportunities.json"
SEEDS_FILE = "config/seeds.txt"

# ─── 1. GOOGLE AUTOCOMPLETE (free, no key) ───────────────────────────────────
def fetch_autocomplete(seed):
    url = "https://suggestqueries.google.com/complete/search"
    params = {"q": seed, "hl": "en-IN", "gl": "in", "client": "firefox"}
    try:
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        return data[1] if len(data) > 1 else []
    except:
        return []

def scan_autocomplete(seeds):
    signals = []
    for seed in seeds:
        suggestions = fetch_autocomplete(seed)
        for s in suggestions:
            s_lower = s.lower()
            if any(w in s_lower for w in ["calculator","calculate","calculation","formula","how to"]):
                signals.append({"text": s, "source": "autocomplete", "seed": seed})
        time.sleep(0.3)  # be polite
    return signals

# ─── 2. REDDIT RSS (free, no key) ────────────────────────────────────────────
SUBREDDITS = [
    "india","IndiaInvestments","UPSC","governmentjobs",
    "IndianInUSA","PersonalFinanceIndia","bsnl"
]
REDDIT_KEYWORDS = [
    "calculator","calculate","vrs","pay revision","salary",
    "pension","arrears","macp","7th cpc","8th cpc","gpf","gratuity",
    "leave encashment","da revision","bsnl","ongc","bhel","coal india"
]

def scan_reddit(subreddits):
    signals = []
    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
            headers = {"User-Agent": "paymatrixcalc-bot/1.0"}
            r = requests.get(url, headers=headers, timeout=10)
            posts = r.json().get("data", {}).get("children", [])
            for p in posts:
                title = p["data"].get("title","").lower()
                if any(kw in title for kw in REDDIT_KEYWORDS):
                    signals.append({
                        "text": p["data"]["title"],
                        "source": "reddit",
                        "seed": sub,
                        "url": f"https://reddit.com{p['data']['permalink']}"
                    })
        except:
            pass
        time.sleep(0.5)
    return signals

# ─── 3. GOOGLE NEWS RSS (free) ───────────────────────────────────────────────
NEWS_QUERIES = [
    "BSNL VRS 2026","8th pay commission","DA revision July 2026",
    "PSU pay revision 2026","central government salary 2026",
    "ONGC salary revision","Coal India VRS","SAIL pay revision",
    "pension revision 2026","gratuity rules 2026"
]

def scan_news(queries):
    signals = []
    for q in queries:
        try:
            url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=en-IN&gl=IN&ceid=IN:en"
            r = requests.get(url, timeout=10)
            root = ET.fromstring(r.content)
            items = root.findall(".//item")[:5]
            for item in items:
                title = item.findtext("title","")
                signals.append({"text": title, "source": "news", "seed": q})
        except:
            pass
        time.sleep(0.3)
    return signals

# ─── 4. SCORING ENGINE ───────────────────────────────────────────────────────
CALC_KEYWORDS  = ["calculator","calculate","calculation","formula","how to calculate","compute"]
INDIA_KEYWORDS = ["india","indian","central govt","government","7th cpc","8th cpc","bsnl","ongc","psu","da","hra","nps","gpf","macp","vrs","pension"]
HIGH_INTENT    = ["vrs 2026","pay revision","arrears","fitment","bsnl vrs","8th cpc salary","da calculator","macp arrears"]
ALREADY_HAVE   = ["7th cpc salary","da arrears","hra calculator","income tax","nps calculator","gratuity","leave encashment","gpf","macp calculator","pay matrix","8th cpc"]

def score_signal(text):
    t = text.lower()
    if any(h in t for h in ALREADY_HAVE):
        return 0  # skip what we already have
    score = 0
    if any(k in t for k in CALC_KEYWORDS):  score += 3
    if any(k in t for k in INDIA_KEYWORDS): score += 3
    if any(k in t for k in HIGH_INTENT):    score += 2
    # penalise too generic
    if len(t.split()) < 3:                  score -= 2
    return max(0, score)

def deduplicate(signals):
    seen, out = set(), []
    for s in signals:
        key = re.sub(r'\W+','',s["text"].lower())[:40]
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out

def derive_slug(text):
    slug = re.sub(r'[^a-z0-9\s]','', text.lower())
    slug = re.sub(r'\s+','-', slug.strip())
    slug = slug[:60].rstrip('-')
    if not slug.endswith("calculator"):
        slug += "-calculator"
    return slug

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    seeds = open(SEEDS_FILE).read().splitlines() if os.path.exists(SEEDS_FILE) else []

    print("🔍 Scanning autocomplete...")
    signals  = scan_autocomplete(seeds)
    print("🔍 Scanning Reddit...")
    signals += scan_reddit(SUBREDDITS)
    print("🔍 Scanning Google News...")
    signals += scan_news(NEWS_QUERIES)

    signals = deduplicate(signals)

    # Score
    scored = []
    for s in signals:
        sc = score_signal(s["text"])
        if sc >= 5:
            scored.append({
                "text":   s["text"],
                "source": s["source"],
                "score":  sc,
                "slug":   derive_slug(s["text"]),
                "date":   datetime.utcnow().strftime("%Y-%m-%d")
            })

    scored.sort(key=lambda x: x["score"], reverse=True)

    # Load existing, merge, keep top 50
    existing = []
    if os.path.exists(OPPORTUNITIES_FILE):
        existing = json.load(open(OPPORTUNITIES_FILE))
    existing_slugs = {e["slug"] for e in existing}

    new_opps = [s for s in scored if s["slug"] not in existing_slugs]
    merged   = (new_opps + existing)[:50]

    json.dump(merged, open(OPPORTUNITIES_FILE,"w"), indent=2)
    print(f"✅ {len(new_opps)} new opportunities found. Total: {len(merged)}")
    for o in new_opps[:5]:
        print(f"  [{o['score']}] {o['text']} → /{o['slug']}")

if __name__ == "__main__":
    main()
