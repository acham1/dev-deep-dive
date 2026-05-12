import os
import re
from pathlib import Path

import functions_framework
from flask import jsonify, request

_secrets_path = Path("/etc/secrets/.env")
if _secrets_path.exists():
    for line in _secrets_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from flask import Response

from firestore_client import (
    add_subscriber,
    get_latest_report,
    get_report,
    list_reports,
    remove_subscriber,
)
from welcome_email import send_welcome_email

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def _respond(data, status=200):
    return (jsonify(data), status, _cors_headers())


@functions_framework.http
def api(request):
    if request.method == "OPTIONS":
        return ("", 204, _cors_headers())

    path = request.path.rstrip("/")
    method = request.method

    if path == "/subscribe" and method == "POST":
        return _handle_subscribe(request)
    elif path == "/unsubscribe" and method == "GET":
        return _handle_unsubscribe(request)
    elif path == "/feed.xml" and method == "GET":
        return _handle_feed()
    elif path == "/reports" and method == "GET":
        return _handle_list_reports(request)
    elif path.startswith("/reports/") and method == "GET":
        report_id = path.split("/reports/", 1)[1]
        return _handle_get_report(report_id)
    else:
        return _respond({"error": "not found"}, 404)


def _handle_subscribe(request):
    data = request.get_json(silent=True)
    if not data or "email" not in data:
        return _respond({"error": "email required"}, 400)

    email = data["email"].strip().lower()
    if not EMAIL_RE.match(email):
        return _respond({"error": "invalid email"}, 400)

    status = add_subscriber(email)
    if status == "subscribed":
        send_welcome_email(email)
    return _respond({"status": status})


def _handle_unsubscribe(request):
    token = request.args.get("token", "")
    if not token:
        return _respond({"error": "token required"}, 400)

    if remove_subscriber(token):
        return _respond({"status": "unsubscribed"})
    return _respond({"error": "not found"}, 404)


def _handle_list_reports(request):
    limit = min(int(request.args.get("limit", "20")), 50)
    start_after = request.args.get("start_after")
    reports = list_reports(limit=limit, start_after=start_after)
    return _respond({"reports": reports})


def _handle_feed():
    from feed import build_rss_xml

    reports = list_reports(limit=50)
    xml = build_rss_xml(reports)
    return Response(xml, content_type="application/rss+xml; charset=utf-8", headers=_cors_headers())


def _handle_get_report(report_id):
    report = get_report(report_id)
    if not report:
        return _respond({"error": "not found"}, 404)
    return _respond(report)
