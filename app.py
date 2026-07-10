import os
import smtplib
from email.message import EmailMessage

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

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message_text = (data.get("message") or "").strip()

    if not all([name, email, message_text]):
        return jsonify({"success": False, "message": "Please fill all fields."}), 400

    message_id = create_message(name, email, message_text)

    try:
        send_contact_email(name, email, message_text)
    except Exception as exc:
        return jsonify({"success": False, "message": f"Message saved but email delivery failed: {exc}"}), 500

    return jsonify({"success": True, "message": "Message saved and sent.", "id": message_id})


@app.route("/api/messages/<int:message_id>", methods=["PUT", "DELETE"])
def message_detail_api(message_id: int):
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        text = (data.get("message") or "").strip()
        status = (data.get("status") or "new").strip()
        if not text:
            return jsonify({"success": False, "message": "Message text is required."}), 400
        update_message(message_id, text, status)
        return jsonify({"success": True, "message": "Message updated."})

    delete_message(message_id)
    return jsonify({"success": True, "message": "Message deleted."})


@app.route("/api/projects", methods=["GET", "POST"])
def projects_api():
    if request.method == "GET":
        return jsonify(get_projects())

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    summary = (data.get("summary") or "").strip()
    description = (data.get("description") or "").strip()

    if not all([title, summary, description]):
        return jsonify({"success": False, "message": "All project fields are required."}), 400

    project_id = create_project(title, summary, description)
    return jsonify({"success": True, "message": "Project added.", "id": project_id})


@app.route("/api/projects/<int:project_id>", methods=["PUT", "DELETE"])
def project_detail_api(project_id: int):
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        summary = (data.get("summary") or "").strip()
        description = (data.get("description") or "").strip()
        if not all([title, summary, description]):
            return jsonify({"success": False, "message": "All project fields are required."}), 400
        update_project(project_id, title, summary, description)
        return jsonify({"success": True, "message": "Project updated."})

    delete_project(project_id)
    return jsonify({"success": True, "message": "Project deleted."})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

