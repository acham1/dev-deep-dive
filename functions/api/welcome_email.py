import logging
import os

import resend

from firestore_client import get_latest_report

logger = logging.getLogger(__name__)


def send_welcome_email(email: str):
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY not set, skipping welcome email")
        return

    resend.api_key = api_key
    from_email = os.environ.get("FROM_EMAIL", "deepdive@mail.dev-deep-dive.alanch.am")
    site_url = os.environ.get("SITE_URL", "https://acham1.github.io/dev-deep-dive")

    report = get_latest_report()

    body = f"""<h2>Welcome to Weekly Deep Dive!</h2>
<p>You'll receive a deep dive into a notable open-source project every week,
explained at three levels of difficulty.</p>"""

    if report:
        report_url = f"{site_url}/report.html?id={report['id']}"
        body += f"""<hr>
<p>Here's the most recent deep dive to get you started:</p>
<h3>{report.get('title', report.get('project_name', 'Untitled'))}</h3>
<p><em>{report.get('tagline', '')}</em></p>
<p>{report.get('why_it_matters', '')[:500]}...</p>
<p><a href="{report_url}">Read the full report</a></p>"""

    try:
        resend.Emails.send(
            {
                "from": from_email,
                "to": email,
                "subject": "Welcome to Weekly Deep Dive!",
                "html": body,
            }
        )
    except Exception:
        logger.exception("Failed to send welcome email to %s", email)
