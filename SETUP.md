# PayMatrixCalc Autopilot Engine — Setup Guide

## What This Does
Runs 100% automatically, 100% free. Every day at 5:30 AM IST:
- Publishes 1 new SEO blog post
- Discovers emerging calculator demand from Google/Reddit/News
- Builds full calculator pages for high-demand trends (score ≥ 7)
- Injects FAQ schema into calculator pages
- Rebuilds sitemap
- Pings IndexNow + Google Indexing API

Every Sunday:
- Generates 5 Reddit + 3 Quora answer drafts → you post in 15 min
- Rewrites weak title/meta tags automatically

**Your time after setup: 15 min/week (Sunday posting only)**

---

## STEP 1 — Create GitHub Repo (10 min)

1. Go to https://github.com → Sign up / Log in
2. Click **New Repository**
3. Name: `paymatrixcalc-site`
4. Set to **Public** (required for free unlimited Actions minutes)
5. Click **Create repository**
6. Upload ALL files from your site zip into this repo:
   - Click "uploading an existing file"
   - Drag the entire contents (not the zip, the extracted files)
   - Include the `blog/` folder, `scripts/` folder, `.github/` folder, `config/` folder
   - Commit message: "Initial deploy v16 + autopilot engine"

---

## STEP 2 — Connect Netlify to GitHub (5 min)

1. Go to https://app.netlify.com
2. **Team overview** → Add new site → **Import from Git**
3. Choose **GitHub** → Select `paymatrixcalc-site` repo
4. Build settings:
   - Build command: *(leave blank)*
   - Publish directory: `/` (root)
5. Click **Deploy site**
6. In Site settings → Domain management → Add your custom domain `paymatrixcalc.com`
7. **From now on: every git push = auto deploy. Stop using drag-and-drop.**

---

## STEP 3 — Get Gemini API Key (3 min)

1. Go to https://aistudio.google.com
2. Click **Get API key** → **Create API key**
3. Copy the key (starts with `AIza...`)
4. Keep it safe — you'll add it to GitHub Secrets next

---

## STEP 4 — Add GitHub Secrets (5 min)

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets one by one:

| Secret Name | Value | Where to get it |
|---|---|---|
| `GEMINI_API_KEY` | Your Gemini API key | Step 3 above |
| `INDEXNOW_KEY` | Any random 32-char hex string | Generate at https://indexnow.org/generateKey |
| `GOOGLE_SA_JSON` | Service account JSON (optional but recommended) | Step 5 below |

---

## STEP 5 — Google Indexing API (15 min, optional but powerful)

This lets the automation ping Google directly when new pages are published.

1. Go to https://console.cloud.google.com
2. **Create new project** → Name: `paymatrixcalc-seo`
3. **Enable APIs**: search "Indexing API" → Enable
4. **IAM & Admin → Service Accounts → Create Service Account**
   - Name: `paymatrix-indexer`
   - Role: Owner (or Indexing API User)
5. Click the service account → **Keys → Add Key → JSON** → Download
6. Open the downloaded JSON file → **copy all contents**
7. Paste as the value of `GOOGLE_SA_JSON` secret in GitHub
8. In Google Search Console:
   - Settings → Users and permissions → Add user
   - Email = the service account email (from JSON file, `client_email` field)
   - Permission = **Owner**

---

## STEP 6 — IndexNow Verification File (2 min)

1. Generate a key at https://indexnow.org/generateKey (or use any 32-char string)
2. Create a file named `[your-key].txt` in your repo root
3. File contents = just the key, nothing else
4. Commit and push — Netlify deploys it
5. Add the same key as `INDEXNOW_KEY` GitHub Secret

---

## STEP 7 — Test the Engine (2 min)

1. In your GitHub repo → **Actions** tab
2. Click **Daily SEO Autopilot** workflow
3. Click **Run workflow** → **Run workflow** (green button)
4. Watch it run — should take 2-3 minutes
5. Check your repo — new files should appear in `blog/` and `config/`
6. Netlify should auto-deploy within 30 seconds of the commit

---

## STEP 8 — Deploy BSNL VRS Calculator NOW

This is already built in the `bsnl-vrs-2026-calculator.html` file.
After GitHub is set up, it will be live at:
`https://paymatrixcalc.com/bsnl-vrs-2026-calculator`

**Immediately after deploy:**
1. Submit in Google Search Console: URL Inspection → Request Indexing
2. Share in BSNL/telecom WhatsApp groups
3. Post on r/bsnl and r/india

---

## WHAT GETS BUILT AUTOMATICALLY

### Daily (5:30 AM IST)
- `blog/[new-post-slug].html` — 1 new 1,200-word SEO blog post
- `blog/index.html` — updated blog listing page
- `sitemap.xml` — regenerated with all pages
- Schema injection on any calculator pages missing FAQ schema
- If a trending calculator is detected (score ≥ 7): full calculator HTML built

### Weekly (Sunday 7 AM IST)
- `drafts/week-XX-reddit-*.txt` — 5 Reddit answer drafts
- `drafts/week-XX-quora-*.txt` — 3 Quora answer drafts
- Meta tags rewritten on low-CTR pages (impressions > 10, CTR < 2%)

---

## YOUR WEEKLY ROUTINE (15 min every Sunday)

1. Open GitHub repo → `drafts/` folder
2. Open each `.txt` file — it shows you exactly where to post and the ready-to-copy answer
3. Go to Reddit/Quora → paste the answer → submit
4. Done

---

## ADDING MORE KEYWORDS

Open `config/keywords.txt` in GitHub → Edit → Add new keyword at the bottom → Commit.
The blog writer picks the next unwritten keyword every morning.

---

## MONITORING

- **Traffic**: https://analytics.google.com (GA4 already on all pages)
- **Rankings**: https://search.google.com/search-console
- **Automation logs**: GitHub → Actions → click any workflow run → see logs
- **New calculators built**: `config/built_calculators.json`
- **Posts written**: `config/written_posts.json`
- **Opportunities queue**: `config/opportunities.json`

---

## COST

| Item | Cost |
|---|---|
| GitHub (public repo + Actions) | ₹0 |
| Netlify (free tier) | ₹0 |
| Gemini 2.5 Flash-Lite API | ₹0 (1,000 req/day free) |
| Google Indexing API | ₹0 (200 URLs/day) |
| IndexNow | ₹0 |
| **Total** | **₹0/month** |

---

## FOLDER STRUCTURE IN REPO

```
paymatrixcalc-site/
├── .github/workflows/
│   ├── daily_seo.yml          ← runs 5:30 AM IST daily
│   └── weekly_tasks.yml       ← runs Sunday 7 AM IST
├── scripts/
│   ├── trend_hunter.py
│   ├── calc_builder.py
│   ├── blog_writer.py
│   ├── blog_index_updater.py
│   ├── schema_injector.py
│   ├── sitemap_and_index.py
│   ├── meta_optimizer.py
│   └── backlink_drafter.py
├── config/
│   ├── keywords.txt           ← add new blog topics here
│   ├── seeds.txt              ← trend hunting seed terms
│   ├── opportunities.json     ← auto-generated
│   ├── written_posts.json     ← auto-generated
│   └── built_calculators.json ← auto-generated
├── blog/                      ← auto-generated posts land here
├── drafts/                    ← Sunday posting drafts
├── [all your existing HTML files]
├── bsnl-vrs-2026-calculator.html  ← NEW — deploy immediately
└── sitemap.xml                ← auto-regenerated daily
```

---

## QUESTIONS? ISSUES?

Check GitHub Actions logs first — every script prints clear status messages.
Common issues:
- `GEMINI_API_KEY not found` → Check Secrets spelling exactly
- Netlify not deploying → Check repo is connected in Netlify settings
- Schema not injecting → Page already has FAQPage schema (skip is correct)
