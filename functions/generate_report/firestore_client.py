import os
from datetime import datetime, timezone

from google.cloud import firestore


def _db():
    return firestore.Client(project=os.environ.get("GCP_PROJECT"))


def get_covered_projects() -> list[dict]:
    docs = _db().collection("covered_projects").order_by("covered_at").stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        results.append(
            {
                "name": d.get("name", ""),
                "repo_url": d.get("repo_url", ""),
                "category": d.get("category", ""),
            }
        )
    return results


def mark_project_covered(project: dict):
    _db().collection("covered_projects").add(
        {
            "name": project["name"],
            "repo_url": project["repo_url"],
            "category": project.get("category", ""),
            "covered_at": datetime.now(timezone.utc),
        }
    )


def save_report(project: dict, report: dict) -> str:
    _, doc_ref = (
        _db()
        .collection("reports")
        .add(
            {
                "project_name": project["name"],
                "repo_url": project["repo_url"],
                "category": project.get("category", ""),
                **report,
                "created_at": datetime.now(timezone.utc),
                "email_sent": False,
                "email_sent_at": None,
            }
        )
    )
    return doc_ref.id


def get_subscribers() -> list[dict]:
    docs = _db().collection("subscribers").where("active", "==", True).stream()
    return [doc.to_dict() for doc in docs]


def get_all_reports_for_feed() -> list[dict]:
    docs = (
        _db()
        .collection("reports")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    results = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        results.append(d)
    return results


def update_report_audio(report_id: str, audio_data: dict):
    _db().collection("reports").document(report_id).update(audio_data)


def mark_email_sent(report_id: str):
    _db().collection("reports").document(report_id).update(
        {
            "email_sent": True,
            "email_sent_at": datetime.now(timezone.utc),
        }
    )
