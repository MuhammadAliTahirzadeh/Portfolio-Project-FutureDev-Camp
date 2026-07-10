import os
import smtplib
from email.message import EmailMessage
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


def json_fields(*names):
    data = request.get_json(silent=True) or {}
    return {name: (data.get(name) or "").strip() for name in names}


def error_response(message, status=400):
    return jsonify({"success": False, "message": message}), status


def success_response(message, **extra):
    return jsonify({"success": True, "message": message, **extra})


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
        return jsonify(get_messages())

    fields = json_fields("name", "email", "message")
    name, email, message_text = fields["name"], fields["email"], fields["message"]

    if not all([name, email, message_text]):
        return error_response("Please fill all fields.")

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

    return success_response("Message saved and sent.", id=message_id)


@app.route("/api/messages/<int:message_id>", methods=["PUT", "DELETE"])
def message_detail_api(message_id: int):
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        text = (data.get("message") or "").strip()
        status = (data.get("status") or "new").strip()
        if not text:
            return error_response("Message text is required.")
        update_message(message_id, text, status)
        return success_response("Message updated.")

    delete_message(message_id)
    return success_response("Message deleted.")


@app.route("/api/projects", methods=["GET", "POST"])
def projects_api():
    if request.method == "GET":
        return jsonify(get_projects())

    fields = json_fields("title", "summary", "description")
    title, summary, description = fields["title"], fields["summary"], fields["description"]

    if not all([title, summary, description]):
        return error_response("All project fields are required.")

    project_id = create_project(title, summary, description)
    return success_response("Project added.", id=project_id)


@app.route("/api/projects/<int:project_id>", methods=["PUT", "DELETE"])
def project_detail_api(project_id: int):
    if request.method == "PUT":
        fields = json_fields("title", "summary", "description")
        title, summary, description = fields["title"], fields["summary"], fields["description"]
        if not all([title, summary, description]):
            return error_response("All project fields are required.")
        update_project(project_id, title, summary, description)
        return success_response("Project updated.")

    delete_project(project_id)
    return success_response("Project deleted.")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

