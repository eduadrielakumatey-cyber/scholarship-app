"""
app/routes/auth.py
--------------------
Signup and login. We use JWT (Flask-JWT-Extended) rather than server-side
sessions because the frontend is a separate React app (possibly on a
different domain/port), and a stateless bearer token is simpler to manage
across that boundary than cookie-based sessions + CORS credentials.

Endpoints:
  POST /api/auth/device  -> one-tap start: account tied to this device, no email/password
  POST /api/auth/signup  -> create account, return token
  POST /api/auth/login   -> verify credentials, return token
  GET  /api/auth/me      -> return the current user's profile (requires token)
  POST /api/auth/link-code        -> one-time code to open this profile on another device
  POST /api/auth/link-code/redeem -> trade that code for a token on the new device
"""

from datetime import datetime, timedelta

from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app.extensions import db
from app.models import DeviceLink, User
from app.services import device_link

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# A device account's token is the only key to it (there's no password to
# log back in with), so it lasts a year instead of the usual week.
DEVICE_TOKEN_LIFETIME = timedelta(days=365)


def _require_consents(data):
    """Both boxes start unchecked in the UI; the server re-checks them so an
    account can't be created without a recorded agreement or by someone
    who said they're under 13 (COPPA)."""
    if data.get("age_confirmed") is not True:
        return jsonify({"error": "you must be at least 13 years old to use ScholarMatch"}), 400
    if data.get("accepted_terms") is not True:
        return jsonify({"error": "you must agree to the Terms of Service and Privacy Policy"}), 400
    return None


@auth_bp.post("/device")
def start_on_device():
    data = request.get_json(silent=True) or {}
    problem = _require_consents(data)
    if problem:
        return problem

    user = User(
        terms_accepted_at=datetime.utcnow(),
        terms_version=current_app.config["TERMS_VERSION"],
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id), expires_delta=DEVICE_TOKEN_LIFETIME)
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400
    problem = _require_consents(data)
    if problem:
        return problem
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "an account with this email already exists"}), 409

    user = User(
        email=email,
        terms_accepted_at=datetime.utcnow(),
        terms_version=current_app.config["TERMS_VERSION"],
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 200


def _token_for(user):
    if user.is_device_account:
        return create_access_token(identity=str(user.id), expires_delta=DEVICE_TOKEN_LIFETIME)
    return create_access_token(identity=str(user.id))


@auth_bp.post("/link-code")
@jwt_required()
def make_link_code():
    """A one-time code that opens this profile on another device."""
    user = User.query.get_or_404(get_jwt_identity())
    now = datetime.utcnow()

    # Only the newest code works: making one cancels any earlier ones, and
    # this is also when old rows get cleaned up.
    DeviceLink.query.filter(
        (DeviceLink.user_id == user.id) | (DeviceLink.expires_at < now)
    ).delete(synchronize_session=False)

    code = device_link.new_code()
    link = DeviceLink(
        user_id=user.id,
        code_hash=device_link.hash_code(code),
        expires_at=now + device_link.CODE_LIFETIME,
    )
    db.session.add(link)
    db.session.commit()
    return jsonify({
        "code": device_link.display(code),
        "expires_in_seconds": int(device_link.CODE_LIFETIME.total_seconds()),
    }), 201


@auth_bp.post("/link-code/redeem")
def redeem_link_code():
    data = request.get_json(silent=True) or {}
    code = device_link.normalize(data.get("code"))
    if len(code) != device_link.CODE_LENGTH:
        return jsonify({"error": "Codes are 8 letters and numbers, like K7QP-4M2X."}), 400

    link = DeviceLink.query.filter_by(code_hash=device_link.hash_code(code)).first()
    if not device_link.is_usable(link):
        return jsonify({
            "error": "That code didn't work. It may have expired or already been used. "
                     "Make a new one on your other device."
        }), 400

    user = db.session.get(User, link.user_id)
    if user is None:
        return jsonify({"error": "That profile no longer exists."}), 400

    # Claim it in one UPDATE so two devices racing with the same code can't
    # both get in.
    claimed = DeviceLink.query.filter_by(id=link.id, used_at=None).update(
        {"used_at": datetime.utcnow()}, synchronize_session=False
    )
    db.session.commit()
    if claimed != 1:
        return jsonify({"error": "That code was just used. Make a new one on your other device."}), 400
    return jsonify({"token": _token_for(user), "user": user.to_dict()}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())
