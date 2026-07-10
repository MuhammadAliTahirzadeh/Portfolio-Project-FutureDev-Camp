import hmac
import os
import re
import smtplib
from email.message import EmailMessage
from functools import wraps
from pathlib import Path

from flask import Flask, abort, jsonify, make_response, render_template, request

from portfolio_db import (
    create_message,
    create_project,
    delete_message,
    delete_project,
    get_messages,
    get_project,
    get_projects,
    init_db,
    seed_projects,
    update_message,
    update_project,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
init_db()
seed_projects()


def load_env_file() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file()


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MAX_NAME_LENGTH = 120
MAX_EMAIL_LENGTH = 254
MAX_MESSAGE_LENGTH = 5000
MAX_TITLE_LENGTH = 200
MAX_SUMMARY_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 10000
ALLOWED_MESSAGE_STATUSES = {"new", "read", "updated", "archived"}


def admin_auth_error():
    """Return an error response if the request lacks a valid admin token.

    The token must be supplied via the ``X-Admin-Token`` header or an
    ``Authorization: Bearer <token>`` header and is compared in constant time.
    Returns ``None`` when the request is authorized.
    """
    expected = os.getenv("ADMIN_TOKEN")
    if not expected:
        return jsonify(
            {
                "success": False,
                "message": "Admin API is not configured. Set the ADMIN_TOKEN environment variable.",
            }
        ), 503

    provided = request.headers.get("X-Admin-Token", "")
    if not provided:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            provided = auth_header[len("Bearer "):].strip()

    if not provided or not hmac.compare_digest(provided, expected):
        return jsonify({"success": False, "message": "Unauthorized."}), 401

    return None


def validate_project_fields(title, summary, description):
    """Return an error response for invalid project input, else ``None``."""
    if not all([title, summary, description]):
        return jsonify({"success": False, "message": "All project fields are required."}), 400
    if (
        len(title) > MAX_TITLE_LENGTH
        or len(summary) > MAX_SUMMARY_LENGTH
        or len(description) > MAX_DESCRIPTION_LENGTH
    ):
        return jsonify({"success": False, "message": "One or more fields are too long."}), 400
    return None


def require_admin(view):
    """Decorator enforcing admin authentication on a view."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        error = admin_auth_error()
        if error is not None:
            return error
        return view(*args, **kwargs)

    return wrapper


def get_mail_config():
    return {
        "server": os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        "port": int(os.getenv("MAIL_PORT", "587")),
        "username": os.getenv("MAIL_USERNAME"),
        "password": os.getenv("MAIL_PASSWORD"),
        "recipient": os.getenv("MAIL_RECIPIENT", "muhammadali.tahirzadeh@gmail.com"),
        "use_tls": os.getenv("MAIL_USE_TLS", "true").lower() in {"1", "true", "yes", "on"},
    }


def send_contact_email(name: str, sender_email: str, message_text: str) -> None:
    mail_config = get_mail_config()

    if not mail_config["username"] or not mail_config["password"]:
        raise RuntimeError(
            "Email credentials are not configured. Set MAIL_USERNAME and MAIL_PASSWORD environment variables."
        )

    message = EmailMessage()
    message["Subject"] = f"Portfolio contact from {name}"
    message["From"] = mail_config["username"]
    message["To"] = mail_config["recipient"]
    message.set_content(
        f"Name: {name}\nEmail: {sender_email}\n\nMessage:\n{message_text}"
    )

    with smtplib.SMTP(mail_config["server"], mail_config["port"]) as server:
        if mail_config["use_tls"]:
            server.starttls()
        server.login(mail_config["username"], mail_config["password"])
        server.send_message(message)


@app.route("/")
def home():
    view_mode = request.args.get("view", "default")
    projects = get_projects()
    return render_template(
        "index.html",
        page_title="Muhammad Ali Tahirzadeh | Portfolio",
        page_description="A modern personal portfolio powered by Flask and Jinja2.",
        view_mode=view_mode,
        projects=projects,
    )


@app.route("/project/<int:project_id>")
def project_detail(project_id: int):
    project = get_project(project_id)
    if not project:
        abort(404)

    return render_template(
        "project_detail.html",
        page_title=f"{project['title']} | Portfolio",
        page_description=project["summary"],
        project=project,
        source="portfolio",
    )


@app.route("/health")
def health():
    if request.method == "GET":
        return make_response({"status": "ok", "message": "Flask server is running"}, 200)
    return make_response({"status": "error"}, 405)


@app.route("/api/messages", methods=["GET", "POST"])
def messages_api():
    if request.method == "GET":
        error = admin_auth_error()
        if error is not None:
            return error
        return jsonify(get_messages())

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message_text = (data.get("message") or "").strip()

    if not all([name, email, message_text]):
        return jsonify({"success": False, "message": "Please fill all fields."}), 400

    if not EMAIL_PATTERN.match(email):
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400

    if (
        len(name) > MAX_NAME_LENGTH
        or len(email) > MAX_EMAIL_LENGTH
        or len(message_text) > MAX_MESSAGE_LENGTH
    ):
        return jsonify({"success": False, "message": "One or more fields are too long."}), 400

    message_id = create_message(name, email, message_text)

    try:
        send_contact_email(name, email, message_text)
    except Exception as exc:
        return jsonify(
            {
                "success": False,
                "message": (
                    "Message was saved, but email delivery failed. "
                    "Check your Gmail app password and MAIL_USERNAME/MAIL_PASSWORD settings."
                ),
                "error": str(exc),
            }
        ), 500

    return jsonify({"success": True, "message": "Message saved and sent.", "id": message_id})


@app.route("/api/messages/<int:message_id>", methods=["PUT", "DELETE"])
@require_admin
def message_detail_api(message_id: int):
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        text = (data.get("message") or "").strip()
        status = (data.get("status") or "new").strip()
        if not text:
            return jsonify({"success": False, "message": "Message text is required."}), 400
        if len(text) > MAX_MESSAGE_LENGTH:
            return jsonify({"success": False, "message": "Message text is too long."}), 400
        if status not in ALLOWED_MESSAGE_STATUSES:
            return jsonify({"success": False, "message": "Invalid status."}), 400
        update_message(message_id, text, status)
        return jsonify({"success": True, "message": "Message updated."})

    delete_message(message_id)
    return jsonify({"success": True, "message": "Message deleted."})


@app.route("/api/projects", methods=["GET", "POST"])
def projects_api():
    if request.method == "GET":
        return jsonify(get_projects())

    error = admin_auth_error()
    if error is not None:
        return error

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    summary = (data.get("summary") or "").strip()
    description = (data.get("description") or "").strip()

    validation_error = validate_project_fields(title, summary, description)
    if validation_error is not None:
        return validation_error

    project_id = create_project(title, summary, description)
    return jsonify({"success": True, "message": "Project added.", "id": project_id})


@app.route("/api/projects/<int:project_id>", methods=["PUT", "DELETE"])
@require_admin
def project_detail_api(project_id: int):
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        summary = (data.get("summary") or "").strip()
        description = (data.get("description") or "").strip()
        validation_error = validate_project_fields(title, summary, description)
        if validation_error is not None:
            return validation_error
        update_project(project_id, title, summary, description)
        return jsonify({"success": True, "message": "Project updated."})

    delete_project(project_id)
    return jsonify({"success": True, "message": "Project deleted."})


if __name__ == "__main__":
    debug_enabled = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes", "on"}
    app.run(
        debug=debug_enabled,
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
    )

