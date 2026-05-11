import logging
import os

import resend

from email_template import render_email

logger = logging.getLogger(__name__)


def send_report_email(
    subscribers: list[dict],
    project: dict,
    report: dict,
    report_id: str,
):
    resend.api_key = os.environ["RESEND_API_KEY"]
    from_email = os.environ.get("FROM_EMAIL", "deepdive@mail.dev-deep-dive.alanch.am")
    site_url = os.environ.get("SITE_URL", "https://acham1.github.io/dev-deep-dive")

    subject = f"Weekly Deep Dive: {report.get('title', project['name'])}"

    for sub in subscribers:
        html = render_email(report, report_id, sub["unsubscribe_token"], site_url)
        try:
            resend.Emails.send(
                {
                    "from": from_email,
                    "to": sub["email"],
                    "subject": subject,
                    "html": html,
                }
            )
        except Exception:
            logger.exception("Failed to send email to %s", sub["email"])
