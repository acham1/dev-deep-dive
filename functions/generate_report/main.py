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
from feed_generator import regenerate_rss_feed
from firestore_client import (
    get_subscribers,
    mark_email_sent,
    mark_project_covered,
    save_report,
)
from project_selector import select_project

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@functions_framework.cloud_event
def generate_report(cloud_event: CloudEvent) -> None:
    logger.info("Starting report generation")

    project = select_project()
    logger.info("Selected project: %s (%s)", project["name"], project["repo_url"])

    report = run_agent(project)
    logger.info("Agent completed report: %s", report.get("title", "untitled"))

    report_id = save_report(project, report)
    mark_project_covered(project)
    logger.info("Saved report %s", report_id)

    subscribers = get_subscribers()
    if subscribers:
        send_report_email(subscribers, project, report, report_id)
        mark_email_sent(report_id)
        logger.info("Sent email to %d subscribers", len(subscribers))
    else:
        logger.info("No subscribers, skipping email")

    regenerate_rss_feed()
    logger.info("RSS feed regenerated")
