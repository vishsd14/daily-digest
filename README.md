# Daily SEO / Digital Marketing Digest

Automated daily digest: RSS + Reddit + HN + targeted web search → Claude curates,
scores, and summarizes → renders as a styled page on GitHub Pages → Telegram push
with the top 3 headlines each morning.

Runs entirely on GitHub Actions. No server, no laptop dependency.

## Setup

### 1. Push this repo to GitHub

```bash
cd daily-digest
git init
git add .
git commit -m "init: daily digest pipeline"
gh repo create daily-digest --public --source=. --push
# or manually: create repo on github.com, then git remote add origin ... && git push
```

Public repo — this is industry news content, no client data, safe to run in the open
(unlike query-fanout-auditor). Also makes the Pages URL work without a paid plan.

### 2. Create a Telegram bot (5 min)

1. Open Telegram, message **@BotFather**
2. Send `/newbot`, follow the prompts, name it whatever
3. BotFather gives you a token like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` — this is `TELEGRAM_BOT_TOKEN`
4. Message your new bot anything (so it can find your chat)
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
6. Find `"chat":{"id": 123456789, ...}` in the response — this number is `TELEGRAM_CHAT_ID`

### 3. Add repo secrets

Repo → Settings → Secrets and variables → Actions:

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | your existing Anthropic key |
| `TELEGRAM_BOT_TOKEN` | from step 2 |
| `TELEGRAM_CHAT_ID` | from step 2 |

Repo → Settings → Secrets and variables → Actions → **Variables** tab:

| Name | Value |
|---|---|
| `DIGEST_URL` | `https://<your-github-username>.github.io/daily-digest/` |

### 4. Enable GitHub Pages

Repo → Settings → Pages → Build and deployment → Source: **GitHub Actions**
(not "Deploy from a branch" — the workflow handles deployment directly)

### 5. Test it

Repo → Actions → "Daily SEO Digest" → Run workflow (manual trigger via
`workflow_dispatch`). Check:
- Actions log for errors (dead feeds log as warnings, not failures — normal)
- Telegram for the push
- The Pages URL for the rendered page

### 6. Confirm the cron time

Workflow fires `30 6 * * *` UTC = 12:00 PM IST. Adjust the cron line in
`.github/workflows/daily-digest.yml` if you want it waiting for you at, say,
8 AM IST instead (`30 2 * * *`).

## Architecture notes

- **Fabrication-risk guardrail**: the Claude prompt in `digest.py` explicitly
  forbids inventing statistics, dates, or claims not present in the source
  snippet — same discipline as the `--outline-depth` fabrication issue in
  query-fanout-auditor. Worth spot-checking the first week of output against
  source articles before trusting it unattended.
- **Standalone, no shared code** with gsc-anomaly-detector or query-fanout-auditor —
  consistent with the project's independent-repo pattern. If you want it to react
  to fanout-auditor or anomaly-detector findings later, that's a conditional text
  recommendation, not a code dependency — same pattern as the existing pipeline.
- **AI Search / GEO category has no RSS backbone** — it leans on `web_search`
  via the Claude API, which costs more per run than parsing a feed. If this
  category turns out low-signal in practice, worth cutting to save API spend.
- **`digest.json` gets committed** each run as an audit trail (same principle as
  keeping GSC pulls verifiable) — you can diff any day against the source pool.

## Known gaps (v0.1 — flagging, not fixing yet)

- No dedupe across days — if a story is still trending on day 2, it can resurface.
  Worth adding a "seen URLs" cache if it gets noisy.
- Reddit's public JSON endpoint is unauthenticated and can rate-limit or get
  blocked by Reddit without warning — no fallback if it goes down mid-run.
- No LinkedIn source — that's where a chunk of practitioner SEO discourse
  actually happens, but there's no clean free API/RSS path in. Flagging as an
  open gap, not silently skipping it.
