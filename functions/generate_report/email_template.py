import markdown as md


def render_email(report: dict, report_id: str, unsub_token: str, site_url: str) -> str:
    why_html = md.markdown(report.get("why_it_matters", ""))
    beginner_html = md.markdown(report.get("beginner", ""))
    intermediate_html = md.markdown(report.get("intermediate", ""))
    advanced_html = md.markdown(report.get("advanced", ""))
    takeaways_html = md.markdown(report.get("key_takeaways", ""))

    report_url = f"{site_url}/report.html?id={report_id}"
    unsub_url = f"{site_url}/unsubscribe.html?token={unsub_token}"
    archive_url = f"{site_url}/archive.html"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;">
<tr><td align="center" style="padding:20px 10px;">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">

<!-- Header -->
<tr><td style="background:#1a1a2e;padding:24px 32px;">
<h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:normal;">Weekly Deep Dive</h1>
</td></tr>

<!-- Title + Tagline -->
<tr><td style="padding:32px 32px 16px;">
<h2 style="margin:0 0 8px;color:#1a1a2e;font-size:24px;">{report.get("title", "")}</h2>
<p style="margin:0;color:#666;font-size:16px;font-style:italic;">{report.get("tagline", "")}</p>
</td></tr>

<!-- Why It Matters -->
<tr><td style="padding:0 32px 24px;">
<h3 style="margin:0 0 12px;color:#1a1a2e;font-size:18px;">Why It Matters</h3>
<div style="color:#333;font-size:15px;line-height:1.6;">{why_html}</div>
</td></tr>

<!-- Beginner -->
<tr><td style="padding:0 32px 24px;">
<div style="border-left:4px solid #4CAF50;background:#f1f8e9;padding:16px 20px;border-radius:0 4px 4px 0;">
<h3 style="margin:0 0 12px;color:#2E7D32;font-size:16px;">Beginner Level</h3>
<div style="color:#333;font-size:15px;line-height:1.6;">{beginner_html}</div>
</div>
</td></tr>

<!-- Intermediate -->
<tr><td style="padding:0 32px 24px;">
<div style="border-left:4px solid #FF9800;background:#FFF3E0;padding:16px 20px;border-radius:0 4px 4px 0;">
<h3 style="margin:0 0 12px;color:#E65100;font-size:16px;">Intermediate Level</h3>
<div style="color:#333;font-size:15px;line-height:1.6;">{intermediate_html}</div>
</div>
</td></tr>

<!-- Advanced -->
<tr><td style="padding:0 32px 24px;">
<div style="border-left:4px solid #F44336;background:#FFEBEE;padding:16px 20px;border-radius:0 4px 4px 0;">
<h3 style="margin:0 0 12px;color:#C62828;font-size:16px;">Advanced Level</h3>
<div style="color:#333;font-size:15px;line-height:1.6;">{advanced_html}</div>
</div>
</td></tr>

<!-- Key Takeaways -->
<tr><td style="padding:0 32px 24px;">
<h3 style="margin:0 0 12px;color:#1a1a2e;font-size:18px;">Key Takeaways</h3>
<div style="color:#333;font-size:15px;line-height:1.6;">{takeaways_html}</div>
</td></tr>

<!-- CTA Button -->
<tr><td align="center" style="padding:0 32px 32px;">
<a href="{report_url}" style="display:inline-block;background:#1a1a2e;color:#ffffff;padding:12px 28px;text-decoration:none;border-radius:4px;font-size:15px;">Read on the web</a>
</td></tr>

<!-- Footer -->
<tr><td style="background:#f9f9f9;padding:20px 32px;border-top:1px solid #eee;">
<p style="margin:0;color:#999;font-size:13px;text-align:center;">
<a href="{archive_url}" style="color:#666;">Browse past deep dives</a>
&nbsp;&middot;&nbsp;
<a href="{unsub_url}" style="color:#666;">Unsubscribe</a>
</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
