import os
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"


def build_podcast_rss_xml(reports: list[dict]) -> str:
    site_url = os.environ.get("SITE_URL", "https://acham1.github.io/dev-deep-dive")

    rss = Element("rss", version="2.0")
    rss.set("xmlns:itunes", ITUNES_NS)

    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "Weekly Deep Dive"
    SubElement(channel, "link").text = site_url
    SubElement(channel, "language").text = "en-us"
    SubElement(channel, "description").text = (
        "A weekly deep dive into notable open-source projects, "
        "explained at three levels of difficulty by an AI researcher."
    )

    SubElement(channel, f"{{{ITUNES_NS}}}author").text = "Weekly Deep Dive"
    SubElement(channel, f"{{{ITUNES_NS}}}summary").text = (
        "Each week, an AI agent researches a notable open-source project and "
        "produces a structured technical report at beginner, intermediate, and "
        "advanced levels. This podcast is the audio version of that report."
    )
    SubElement(channel, f"{{{ITUNES_NS}}}explicit").text = "no"

    category = SubElement(channel, f"{{{ITUNES_NS}}}category")
    category.set("text", "Technology")

    for report in reports:
        audio_url = report.get("audio_url")
        if not audio_url:
            continue

        item = SubElement(channel, "item")
        title = report.get("title", report.get("project_name", "Untitled"))
        SubElement(item, "title").text = title
        SubElement(item, f"{{{ITUNES_NS}}}author").text = "Weekly Deep Dive"
        SubElement(item, f"{{{ITUNES_NS}}}explicit").text = "no"

        report_id = report.get("id", "")
        link = f"{site_url}/report.html?id={report_id}"
        SubElement(item, "link").text = link
        SubElement(item, "guid").text = audio_url

        tagline = report.get("tagline", "")
        why = report.get("why_it_matters", "")
        SubElement(item, "description").text = (
            f"{tagline}\n\n{why}" if tagline else why
        )

        enclosure = SubElement(item, "enclosure")
        enclosure.set("url", audio_url)
        enclosure.set("type", "audio/mpeg")
        enclosure.set("length", str(report.get("audio_size_bytes", 0)))

        duration_secs = report.get("audio_duration_secs", 0)
        minutes, secs = divmod(duration_secs, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            SubElement(item, f"{{{ITUNES_NS}}}duration").text = (
                f"{hours}:{minutes:02d}:{secs:02d}"
            )
        else:
            SubElement(item, f"{{{ITUNES_NS}}}duration").text = (
                f"{minutes}:{secs:02d}"
            )

        created = report.get("created_at")
        if created:
            if isinstance(created, str):
                dt = datetime.fromisoformat(created)
            else:
                dt = created
            dt = dt.astimezone(timezone.utc)
            SubElement(item, "pubDate").text = dt.strftime(
                "%a, %d %b %Y %H:%M:%S +0000"
            )

    xml_str = tostring(rss, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
