import hashlib
import hmac
import os
from datetime import datetime, timezone

from google.cloud import firestore


def _db():
    return firestore.Client(project=os.environ.get("GCP_PROJECT"))


def add_subscriber(email: str) -> str:
    db = _db()
    existing = list(
        db.collection("subscribers").where("email", "==", email).limit(1).stream()
    )
    if existing:
        doc = existing[0]
        if not doc.to_dict().get("active", True):
            doc.reference.update({"active": True})
            return "resubscribed"
        return "already_subscribed"

    secret = os.environ["UNSUBSCRIBE_SECRET"]
    token = hmac.new(secret.encode(), email.encode(), hashlib.sha256).hexdigest()
    db.collection("subscribers").add(
        {
            "email": email,
            "subscribed_at": datetime.now(timezone.utc),
            "unsubscribe_token": token,
            "active": True,
        }
    )
    return "subscribed"


def remove_subscriber(token: str) -> bool:
    db = _db()
    docs = list(
        db.collection("subscribers")
        .where("unsubscribe_token", "==", token)
        .limit(1)
        .stream()
    )
    if not docs:
        return False
    docs[0].reference.update({"active": False})
    return True


def list_reports(limit: int = 20, start_after: str | None = None) -> list[dict]:
    db = _db()
    q = (
        db.collection("reports")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    if start_after:
        doc = db.collection("reports").document(start_after).get()
        if doc.exists:
            q = q.start_after(doc)

    results = []
    for doc in q.stream():
        d = doc.to_dict()
        d["id"] = doc.id
        for key in ("raw_markdown", "beginner", "intermediate", "advanced"):
            d.pop(key, None)
        if "created_at" in d and hasattr(d["created_at"], "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        results.append(d)
    return results


def get_report(report_id: str) -> dict | None:
    doc = _db().collection("reports").document(report_id).get()
    if not doc.exists:
        return None
    d = doc.to_dict()
    d["id"] = doc.id
    d.pop("raw_markdown", None)
    if "created_at" in d and hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d
