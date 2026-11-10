"""
app/routes/sponsor.py
------------------------
Scholarships that a sponsor (a local business, club, family, school group)
posts on ScholarMatch. Students apply inside the app; the sponsor reads
applications through a private review link; ScholarMatch never handles the
money -- the sponsor pays winners directly.

  POST  /api/sponsor/scholarships                        -> post one (waits for approval)
  GET   /api/sponsor/review/<token>                      -> the sponsor's private review page
  PATCH /api/sponsor/review/<token>/applications/<id>    -> mark winner / not selected

Approval (header X-Admin-Key must equal the ADMIN_KEY setting):
  GET    /api/admin/pending                              -> listings waiting for approval
  POST   /api/admin/scholarships/<id>/approve            -> publish it
  DELETE /api/admin/scholarships/<id>                    -> reject (delete) it
"""

import hmac
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models import Application, Scholarship
from app.models.application import APPLICATION_STATUSES
from app.services.hosted import hash_token, new_review_token, validate_listing

sponsor_bp = Blueprint("sponsor", __name__, url_prefix="/api")

MAX_PENDING_PER_EMAIL = 3
MAX_PENDING_TOTAL = 50


def _listing(s: Scholarship) -> dict:
    return {
        **s.to_dict(),
        "approved": bool(s.is_active and s.status == "active"),
        "sponsor_name": s.sponsor_name,
    }


@sponsor_bp.post("/sponsor/scholarships")
def post_scholarship():
    data = request.get_json(silent=True) or {}
    fields, errors = validate_listing(data)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    pending = Scholarship.query.filter_by(hosted=True, status="needs_review")
    if pending.count() >= MAX_PENDING_TOTAL or pending.filter_by(sponsor_email=fields["sponsor_email"]).count() >= MAX_PENDING_PER_EMAIL:
        return jsonify({"error": "Too many scholarships are waiting for review. Please try again later."}), 429

    token = new_review_token()
    token_hash = hash_token(token)
    has_essay = bool(fields["essay_prompt"])
    s = Scholarship(
        title=fields["title"],
        organization=fields["organization"],
        description=fields["description"],
        essay_prompt=fields["essay_prompt"],
        essay_required=has_essay,
        award_amount=fields["award_amount"],
        num_awards=fields["num_awards"],
        deadline=fields["deadline"],
        grade_levels=fields["grade_levels"],
        states=fields["states"],
        min_gpa=fields["min_gpa"],
        demographics=[],
        majors=[],
        interests=[],
        award_frequency="one_time",
        estimated_hours_to_apply=2.0 if has_essay else 0.5,
        # Posted here, seen only by ScholarMatch users: a small pool.
        estimated_applicant_pool=50,
        hosted=True,
        sponsor_name=fields["sponsor_name"],
        sponsor_email=fields["sponsor_email"],
        review_token_hash=token_hash,
        source_name="sponsor",
        external_id=f"sponsor-{token_hash[:16]}",
        source_url=None,
        is_active=False,
        status="needs_review",
    )
    db.session.add(s)
    db.session.commit()
    # The raw token is shown once and never stored; only its hash is.
    return jsonify({"id": s.id, "review_token": token}), 201


def _by_token(token):
    s = Scholarship.query.filter_by(hosted=True, review_token_hash=hash_token(token)).first()
    if s is None:
        return None, (jsonify({"error": "This review link isn't valid"}), 404)
    return s, None


@sponsor_bp.get("/sponsor/review/<token>")
def review(token):
    s, err = _by_token(token)
    if err:
        return err
    apps = Application.query.filter_by(scholarship_id=s.id).order_by(Application.created_at).all()
    return jsonify({"scholarship": _listing(s), "applications": [a.to_dict() for a in apps]})


@sponsor_bp.patch("/sponsor/review/<token>/applications/<int:application_id>")
def decide(token, application_id):
    s, err = _by_token(token)
    if err:
        return err
    application = Application.query.filter_by(id=application_id, scholarship_id=s.id).first_or_404()
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in APPLICATION_STATUSES:
        return jsonify({"error": f"status must be one of {list(APPLICATION_STATUSES)}"}), 400
    application.status = status
    db.session.commit()
    return jsonify(application.to_dict())


# --- Approval ---------------------------------------------------------------------

def _admin_ok():
    key = current_app.config.get("ADMIN_KEY")
    given = request.headers.get("X-Admin-Key", "")
    return bool(key) and hmac.compare_digest(key, given)


@sponsor_bp.get("/admin/pending")
def pending():
    if not _admin_ok():
        return jsonify({"error": "not allowed"}), 403
    rows = Scholarship.query.filter_by(hosted=True).order_by(Scholarship.created_at.desc()).limit(100).all()
    return jsonify({"results": [{**_listing(s), "sponsor_email": s.sponsor_email} for s in rows]})


@sponsor_bp.post("/admin/scholarships/<int:scholarship_id>/approve")
def approve(scholarship_id):
    if not _admin_ok():
        return jsonify({"error": "not allowed"}), 403
    s = Scholarship.query.filter_by(id=scholarship_id, hosted=True).first_or_404()
    s.is_active = True
    s.status = "active"
    s.last_verified_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_listing(s))


@sponsor_bp.delete("/admin/scholarships/<int:scholarship_id>")
def reject(scholarship_id):
    if not _admin_ok():
        return jsonify({"error": "not allowed"}), 403
    s = Scholarship.query.filter_by(id=scholarship_id, hosted=True).first_or_404()
    db.session.delete(s)
    db.session.commit()
    return "", 204
