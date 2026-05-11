# Weekly Deep Dive

An automated weekly newsletter that picks a notable open-source project and produces a structured technical report at three difficulty levels (beginner, intermediate, advanced).

A Claude agent researches each project — cloning repos, reading source code, searching the web — then writes a report that gets saved to Firestore, emailed to subscribers, and published to a static site.

## Architecture

- **`functions/generate_report`** — Cloud Function (Pub/Sub triggered) that selects a project using Claude Haiku, runs a Claude Agent SDK research agent, saves the report to Firestore, and emails subscribers via Resend
- **`functions/api`** — Cloud Function (HTTP) providing subscribe/unsubscribe and report listing endpoints
- **`frontend/`** — Static site hosted on GitHub Pages
- **Cloud Scheduler** — Triggers report generation weekly (default: Mondays 7am PT)

## Setup

### Prerequisites

- Google Cloud project with these APIs enabled: Cloud Functions, Pub/Sub, Cloud Scheduler, Firestore, Secret Manager, Cloud Build, Cloud Run, Eventarc
- [Resend](https://resend.com) account with a verified sender domain
- Anthropic API key

### Secrets

Create a secret called `environment-variables` in GCP Secret Manager with:

```
ANTHROPIC_API_KEY=<your-key>
RESEND_API_KEY=<your-key>
UNSUBSCRIBE_SECRET=<random-hex>
FROM_EMAIL=<your-verified-sender@yourdomain.com>
```

Grant the default compute service account the `Secret Manager Secret Accessor` role on this secret.

### Deploy

```bash
# Set your GCP project
gcloud config set project <your-project-id>

# Deploy backend + scheduler
bash deploy.sh

# Frontend is deployed automatically via GitHub Pages on push to main
```

### Manual trigger

```bash
gcloud pubsub topics publish deep-dive-trigger --message='{}'
```

## Roadmap

- [ ] **Podcast generation** — Use TTS to convert reports into audio episodes and publish to podcast directories (Apple Podcasts, Spotify, etc.)

## Configuration

Environment variables in `deploy.sh`:

| Variable | Default | Description |
|---|---|---|
| `GCP_PROJECT` | `dev-deep-dive` | GCP project ID |
| `GCP_REGION` | `us-central1` | Deployment region |
| `SITE_URL` | `https://acham1.github.io/dev-deep-dive` | Public site URL |
| `SCHEDULE` | `0 7 * * MON` | Cron schedule |
| `TIMEZONE` | `America/Los_Angeles` | Scheduler timezone |
