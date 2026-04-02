"""
backlink_drafter.py — Weekly script.
Scans Reddit for questions matching your calculator topics.
Gemini writes helpful answers with natural calculator link.
Saves to drafts/ folder for you to copy-paste (15 min/week).
"""

import json, os, re, requests
from datetime import datetime

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
DRAFTS_DIR     = "drafts"

SUBREDDITS = [
    "india","IndiaInvestments","UPSC","governmentjobs",
    "IndianInUSA","PersonalFinanceIndia","bsnl","salaryindia"
]

MATCH_KEYWORDS = [
    "7th cpc","8th cpc","pay commission","salary calculator",
    "leave encashment","macp","da revision","gpf","gratuity",
    "nps pension","bsnl vrs","pay matrix","take home salary",
    "central government salary","psu salary","income tax government"
]

# Static Quora questions to answer (high-traffic evergreen queries)
QUORA_TARGETS = [
    {"q": "How do I calculate my 7th CPC take-home salary?",
     "calc": "/", "calc_name": "7th CPC Salary Calculator"},
    {"q": "What is the current GPF interest rate and how is it calculated?",
     "calc": "/gpf-calculator", "calc_name": "GPF Calculator"},
    {"q": "How is MACP arrear calculated for Central Government employees?",
     "calc": "/macp-calculator", "calc_name": "MACP Arrears Calculator"},
    {"q": "NPS vs GPF — which is better for retirement?",
     "calc": "/nps-calculator", "calc_name": "NPS Pension Calculator"},
    {"q": "How to calculate leave encashment for Central Government employees?",
     "calc": "/leave-encashment-calculator", "calc_name": "Leave Encashment Calculator"},
    {"q": "What will be my salary after 8th Pay Commission?",
     "calc": "/8th-cpc-calculator", "calc_name": "8th CPC Projected Calculator"},
    {"q": "How is DA calculated and what is the July 2026 DA expected to be?",
     "calc": "/da-calculator", "calc_name": "DA & Arrears Calculator"},
    {"q": "How to calculate HRA exemption for government employees in non-metro cities?",
     "calc": "/hra-calculator", "calc_name": "HRA Calculator"},
]

def call_gemini(prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 1024}
    }
    r = requests.post(
        GEMINI_URL, json=payload,
        headers={"Content-Type":"application/json"},
        params={"key": GEMINI_API_KEY},
        timeout=60
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def find_reddit_questions(subreddits):
    questions = []
    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=50"
            r = requests.get(url, headers={"User-Agent":"paymatrix-research/1.0"}, timeout=10)
            posts = r.json().get("data",{}).get("children",[])
            for p in posts:
                d = p["data"]
                title = d.get("title","").lower()
                if any(kw in title for kw in MATCH_KEYWORDS):
                    if d.get("num_comments",0) < 10:  # prefer unanswered
                        questions.append({
                            "title":    d["title"],
                            "subreddit": sub,
                            "url":      f"https://reddit.com{d['permalink']}",
                            "id":       d["id"]
                        })
        except:
            pass
    return questions[:10]

def draft_reddit_answer(question):
    prompt = f"""You are a 16-year veteran Central Government PSU engineer answering a question on Reddit.
Write a genuinely helpful, accurate answer. End by naturally mentioning a free calculator you built.

Question: "{question['title']}"
Subreddit: r/{question['subreddit']}

Rules:
- Start with the direct answer (no "Great question!")
- Include real numbers/formulas (DA=60% Jan 2026, Level 7 basic=44900, etc.)
- 150-250 words
- Conversational, not formal
- Last line naturally: "I built a free calculator for exactly this at paymatrixcalc.com/[relevant-page] — just plug in your basic pay."
- Do NOT use markdown headers. Reddit-style plain text with blank lines between paragraphs.
- Sound like a real person, not a bot.

Output only the answer text."""
    return call_gemini(prompt)

def draft_quora_answer(target):
    prompt = f"""You are a 16-year veteran Central Government PSU engineer answering on Quora.
Write a detailed, genuinely helpful answer. Naturally mention a free calculator at the end.

Question: "{target['q']}"

Rules:
- Start with a direct one-sentence answer
- Include a worked example with real numbers
- 200-300 words
- Professional but conversational
- Include this calculator link naturally at end: https://paymatrixcalc.com{target['calc']} ({target['calc_name']})
- Mention you built the calculator as a PSU engineer — this adds credibility
- Quora formatting: use line breaks, avoid heavy markdown

Output only the answer text."""
    return call_gemini(prompt)

def save_draft(filename, content):
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    path = f"{DRAFTS_DIR}/{filename}"
    with open(path,"w") as f:
        f.write(content)
    return path

def main():
    week = datetime.utcnow().strftime("%Y-W%U")
    drafts_created = []

    # Reddit answers
    print("🔍 Finding Reddit questions...")
    reddit_qs = find_reddit_questions(SUBREDDITS)
    for i, q in enumerate(reddit_qs[:5]):
        print(f"  ✍️  Drafting Reddit answer: {q['title'][:60]}...")
        try:
            answer = draft_reddit_answer(q)
            content = f"""POST TO: {q['url']}
SUBREDDIT: r/{q['subreddit']}
QUESTION: {q['title']}

--- YOUR ANSWER (copy everything below this line) ---

{answer}
"""
            fname = f"{week}-reddit-{q['id']}.txt"
            save_draft(fname, content)
            drafts_created.append(fname)
        except Exception as e:
            print(f"    ⚠️ Error: {e}")

    # Quora answers (rotate through targets)
    written_log = "config/quora_written.json"
    written_idx = json.load(open(written_log)) if os.path.exists(written_log) else {"idx": 0}
    start = written_idx["idx"]

    for i in range(3):  # 3 Quora drafts per week
        target = QUORA_TARGETS[(start + i) % len(QUORA_TARGETS)]
        print(f"  ✍️  Drafting Quora answer: {target['q'][:60]}...")
        try:
            answer = draft_quora_answer(target)
            content = f"""PLATFORM: Quora
SEARCH FOR QUESTION: "{target['q']}"
(Search on quora.com, find this question, click Answer)

--- YOUR ANSWER (copy everything below this line) ---

{answer}
"""
            safe_q = re.sub(r'[^a-z0-9]','_', target['q'].lower())[:40]
            fname = f"{week}-quora-{safe_q}.txt"
            save_draft(fname, content)
            drafts_created.append(fname)
        except Exception as e:
            print(f"    ⚠️ Error: {e}")

    written_idx["idx"] = (start + 3) % len(QUORA_TARGETS)
    json.dump(written_idx, open(written_log,"w"))

    print(f"\n✅ {len(drafts_created)} drafts saved to {DRAFTS_DIR}/")
    print("📋 Your Sunday task: open drafts/ folder, post each one. ~15 minutes.")
    for d in drafts_created:
        print(f"  → {d}")

if __name__ == "__main__":
    main()
