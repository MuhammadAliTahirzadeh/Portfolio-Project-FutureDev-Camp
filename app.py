import os
from pathlib import Path

import httpx
from flask import Flask, abort, jsonify, make_response, render_template, request
from supabase import create_client, Client

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


def get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase credentials are not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
    return create_client(supabase_url, supabase_key)


def send_contact_email(name: str, sender_email: str, message_text: str) -> None:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    recipient = os.getenv("MAIL_RECIPIENT", "muhammadali.tahirzadeh.uni@gmail.com")
    
    # Use direct HTTP call to Supabase Edge Function
    function_url = f"{supabase_url}/functions/v1/send-email"
    headers = {
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": name,
        "sender_email": sender_email,
        "message_text": message_text,
        "recipient": recipient
    }
    
    response = httpx.post(function_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        error_data = response.json() if response.content else {}
        raise RuntimeError(f"Edge Function failed: {error_data.get('error', 'Unknown error')}")
        
    return response.json()


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

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        data = {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message_text = (data.get("message") or "").strip()

    if not all([name, email, message_text]):
        return jsonify({"success": False, "message": "Please fill all fields."}), 400

    message_id = create_message(name, email, message_text)

    try:
        send_contact_email(name, email, message_text)
    except Exception as exc:
        return jsonify(
            {
                "success": False,
                "message": (
                    "Message was saved, but email delivery failed. "
                    "Check your Supabase Edge Function and RESEND_API_KEY settings."
                ),
                "error": str(exc),
            }
        ), 500

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

