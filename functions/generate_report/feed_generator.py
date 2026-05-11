import logging
import os
from datetime import timezone
from xml.etree.ElementTree import Element, SubElement, tostring

import markdown as md
from google.cloud import storage

from firestore_client import get_all_reports_for_feed

logger = logging.getLogger(__name__)

CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"


def regenerate_rss_feed():
    reports = get_all_reports_for_feed()
    xml = build_rss_xml(reports)
    _upload_to_hosting_bucket(xml)


def build_rss_xml(reports: list[dict]) -> str:
    site_url = os.environ.get("SITE_URL", "https://acham1.github.io/dev-deep-dive")

    rss = Element("rss", version="2.0")
    rss.set("xmlns:content", CONTENT_NS)

    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "Weekly Deep Dive"
    SubElement(channel, "link").text = site_url
    SubElement(channel, "description").text = (
        "A weekly deep dive into notable open-source projects, "
        "explained at three levels of difficulty."
    )
    SubElement(channel, "language").text = "en-us"

    if reports:
        newest = reports[0].get("created_at")
        if newest:
            SubElement(channel, "lastBuildDate").text = _rfc2822(newest)

    for report in reports:
        item = SubElement(channel, "item")
        title = report.get("title", report.get("project_name", "Untitled"))
        SubElement(item, "title").text = title

        report_id = report.get("id", "")
        link = f"{site_url}/report.html?id={report_id}"
        SubElement(item, "link").text = link
        SubElement(item, "guid").text = link

        tagline = report.get("tagline", "")
        why = report.get("why_it_matters", "")
        SubElement(item, "description").text = f"{tagline}\n\n{why}" if tagline else why

        created = report.get("created_at")
        if created:
            SubElement(item, "pubDate").text = _rfc2822(created)

        full_content = _build_full_html(report)
        content_el = SubElement(item, f"{{{CONTENT_NS}}}encoded")
        content_el.text = full_content

    xml_bytes = tostring(rss, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes


def _build_full_html(report: dict) -> str:
    parts = []
    for section in (
        "why_it_matters",
        "beginner",
        "intermediate",
        "advanced",
        "key_takeaways",
    ):
        text = report.get(section, "")
        if text:
            label = section.replace("_", " ").title()
            parts.append(f"<h2>{label}</h2>\n{md.markdown(text)}")
    return "\n".join(parts)


def _rfc2822(dt) -> str:
    if hasattr(dt, "astimezone"):
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def _upload_to_hosting_bucket(xml_content: str):
    bucket_name = os.environ.get("HOSTING_BUCKET")
    if not bucket_name:
        logger.warning("HOSTING_BUCKET not set, skipping feed upload")
        return

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob("feed.xml")
    blob.upload_from_string(
        xml_content,
        content_type="application/rss+xml; charset=utf-8",
    )
    logger.info("Uploaded feed.xml to gs://%s/feed.xml", bucket_name)
