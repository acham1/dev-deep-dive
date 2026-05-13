import logging
import os
from pathlib import Path

import functions_framework
from cloudevents.http import CloudEvent

_secrets_path = Path("/etc/secrets/.env")
if _secrets_path.exists():
    for line in _secrets_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from agent import run_agent
from email_sender import send_report_email
from firestore_client import (
    get_subscribers,
    mark_email_sent,
    mark_project_covered,
    save_report,
)
from podcast_generator import generate_podcast_audio
from project_selector import select_project

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def _send_error_alert(error: Exception):
    admin_email = os.environ.get("ADMIN_EMAIL")
    resend_key = os.environ.get("RESEND_API_KEY")
    if not admin_email or not resend_key:
        return

    import resend

    resend.api_key = resend_key
    from_email = os.environ.get("FROM_EMAIL", "deepdive@mail.dev-deep-dive.alanch.am")
    try:
        resend.Emails.send(
            {
                "from": from_email,
                "to": admin_email,
                "subject": "Weekly Deep Dive: report generation failed",
                "html": f"<pre>{error.__class__.__name__}: {error}</pre>",
            }
        )
    except Exception:
        logger.exception("Failed to send error alert")


@functions_framework.cloud_event
def generate_report(cloud_event: CloudEvent) -> None:
    try:
        _generate_report()
    except Exception as e:
        logger.exception("Report generation failed")
        _send_error_alert(e)
        raise


def _generate_report():
    logger.info("Starting report generation")

    project = select_project()
    logger.info("Selected project: %s (%s)", project["name"], project["repo_url"])

    report = run_agent(project)
    logger.info("Agent completed report: %s", report.get("title", "untitled"))

    report_id = save_report(project, report)
    mark_project_covered(project)
    logger.info("Saved report %s", report_id)

    try:
        audio = generate_podcast_audio(report, report_id)
        if audio:
            report["audio_url"] = audio["audio_url"]
            logger.info("Generated podcast audio: %s", audio["audio_url"])
    except Exception as e:
        import traceback

        print(f"Podcast audio generation failed (non-fatal): {e}")
        traceback.print_exc()
        logger.exception("Podcast audio generation failed (non-fatal)")

    subscribers = get_subscribers()
    if subscribers:
        send_report_email(subscribers, project, report, report_id)
        mark_email_sent(report_id)
        logger.info("Sent email to %d subscribers", len(subscribers))
    else:
        logger.info("No subscribers, skipping email")
