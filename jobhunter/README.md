# JobHunter

Automated pipeline that scrapes multiple job boards (remote-friendly, freelance,
OSS, ATS), scores opportunities for fit, optionally reranks via LLM, and pushes
high-value leads to your phone via ntfy.sh (with optional WhatsApp fallback).

## How it runs

GitHub Actions runs `python main.py` every 5 hours (see `.github/workflows/jobhunter.yml`).
After each run the workflow commits `jobs.db` (URL dedup memory) and `reports/`
(human-readable digests) back to the repo. You can also trigger a run manually
from the **Actions** tab → **JobHunter** → **Run workflow**.

## Repo secrets

Configure these in **Settings → Secrets and variables → Actions**:

| Secret | Required? | What it does |
|---|---|---|
| `NTFY_TOPIC` | yes | Your ntfy.sh push topic. The pipeline POSTs to `https://ntfy.sh/<topic>` |
| `ANTHROPIC_API_KEY` | optional | Enables LLM rerank + cover-letter drafts |
| `NTFY_SERVER` | optional | Override default `https://ntfy.sh` (self-hosted ntfy) |
| `CALLMEBOT_PHONE` | optional | WhatsApp fallback delivery |
| `CALLMEBOT_APIKEY` | optional | WhatsApp fallback delivery |

## Receiving notifications

1. Install the **ntfy** app (Play Store / App Store).
2. Tap `+`, enter the same topic name you set as `NTFY_TOPIC`.
3. High-value leads (score ≥ 65, channel B/C, posted within the last 3 days)
   arrive as push notifications. Tapping a notification opens the job URL.

## Running locally

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
NTFY_TOPIC=your-topic venv/bin/python main.py --no-llm
```

Reports land in `reports/YYYY-MM-DD-HHMM.md`.
