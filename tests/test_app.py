import smtplib

import pytest


@pytest.fixture
def app_module():
    import app as app_module

    return app_module


# --------------------------------------------------------------------------- #
# load_env_file
# --------------------------------------------------------------------------- #
def test_load_env_file_no_file(tmp_path, monkeypatch, app_module):
    monkeypatch.setattr(app_module, "__file__", str(tmp_path / "app.py"))
    # Should silently return without raising when no .env exists.
    app_module.load_env_file()


def test_load_env_file_parses_values(tmp_path, monkeypatch, app_module):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# a comment",
                "",
                'MAIL_USERNAME="quoted@example.com"',
                "MAIL_PORT=2525",
                "INVALID_LINE_WITHOUT_EQUALS",
                "MAIL_PASSWORD='secret'",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "__file__", str(tmp_path / "app.py"))
    for key in ("MAIL_USERNAME", "MAIL_PORT", "MAIL_PASSWORD"):
        monkeypatch.delenv(key, raising=False)

    app_module.load_env_file()

    import os

    assert os.environ["MAIL_USERNAME"] == "quoted@example.com"
    assert os.environ["MAIL_PORT"] == "2525"
    assert os.environ["MAIL_PASSWORD"] == "secret"


def test_load_env_file_does_not_override_existing(tmp_path, monkeypatch, app_module):
    env_file = tmp_path / ".env"
    env_file.write_text("MAIL_RECIPIENT=fromfile@example.com", encoding="utf-8")
    monkeypatch.setattr(app_module, "__file__", str(tmp_path / "app.py"))
    monkeypatch.setenv("MAIL_RECIPIENT", "preset@example.com")

    app_module.load_env_file()

    import os

    assert os.environ["MAIL_RECIPIENT"] == "preset@example.com"


# --------------------------------------------------------------------------- #
# get_mail_config
# --------------------------------------------------------------------------- #
def test_get_mail_config_defaults(monkeypatch, app_module):
    for key in (
        "MAIL_SERVER",
        "MAIL_PORT",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "MAIL_RECIPIENT",
        "MAIL_USE_TLS",
    ):
        monkeypatch.delenv(key, raising=False)

    config = app_module.get_mail_config()
    assert config["server"] == "smtp.gmail.com"
    assert config["port"] == 587
    assert config["username"] is None
    assert config["password"] is None
    assert config["use_tls"] is True


def test_get_mail_config_reads_env(monkeypatch, app_module):
    monkeypatch.setenv("MAIL_SERVER", "smtp.example.com")
    monkeypatch.setenv("MAIL_PORT", "465")
    monkeypatch.setenv("MAIL_USERNAME", "user@example.com")
    monkeypatch.setenv("MAIL_PASSWORD", "pw")
    monkeypatch.setenv("MAIL_USE_TLS", "false")

    config = app_module.get_mail_config()
    assert config["server"] == "smtp.example.com"
    assert config["port"] == 465
    assert config["username"] == "user@example.com"
    assert config["use_tls"] is False


# --------------------------------------------------------------------------- #
# send_contact_email
# --------------------------------------------------------------------------- #
def test_send_contact_email_requires_credentials(monkeypatch, app_module):
    monkeypatch.delenv("MAIL_USERNAME", raising=False)
    monkeypatch.delenv("MAIL_PASSWORD", raising=False)

    with pytest.raises(RuntimeError):
        app_module.send_contact_email("Name", "a@example.com", "hi")


def test_send_contact_email_sends_via_smtp(monkeypatch, app_module):
    monkeypatch.setenv("MAIL_USERNAME", "user@example.com")
    monkeypatch.setenv("MAIL_PASSWORD", "pw")
    monkeypatch.setenv("MAIL_USE_TLS", "true")

    sent = {}

    class FakeSMTP:
        def __init__(self, server, port):
            sent["server"] = server
            sent["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            sent["starttls"] = True

        def login(self, username, password):
            sent["login"] = (username, password)

        def send_message(self, message):
            sent["message"] = message

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    app_module.send_contact_email("Alice", "alice@example.com", "Hello")

    assert sent["starttls"] is True
    assert sent["login"] == ("user@example.com", "pw")
    assert sent["message"]["To"]  # recipient set
    assert "Alice" in sent["message"].get_content()


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "message": "Flask server is running"}


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_project_detail_found(client, db):
    project_id = db.create_project("Detail", "a summary", "a description")
    response = client.get(f"/project/{project_id}")
    assert response.status_code == 200


def test_project_detail_not_found(client):
    response = client.get("/project/999")
    assert response.status_code == 404


def test_messages_api_get_empty(client):
    response = client.get("/api/messages")
    assert response.status_code == 200
    assert response.get_json() == []


def test_messages_api_post_missing_fields(client):
    response = client.post("/api/messages", json={"name": "Only name"})
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_messages_api_post_success(client, app_module, monkeypatch):
    monkeypatch.setattr(app_module, "send_contact_email", lambda *a, **k: None)
    response = client.post(
        "/api/messages",
        json={"name": "Bob", "email": "bob@example.com", "message": "Hi"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert "id" in body

    listed = client.get("/api/messages").get_json()
    assert len(listed) == 1


def test_messages_api_post_email_failure_still_saves(client, app_module, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(app_module, "send_contact_email", boom)
    response = client.post(
        "/api/messages",
        json={"name": "Bob", "email": "bob@example.com", "message": "Hi"},
    )
    assert response.status_code == 500
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "smtp down"
    # The message is persisted even though delivery failed.
    assert len(client.get("/api/messages").get_json()) == 1


def test_message_detail_put_updates(client, db):
    message_id = db.create_message("Bob", "bob@example.com", "original")
    response = client.put(
        f"/api/messages/{message_id}",
        json={"message": "updated", "status": "read"},
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert db.get_messages()[0]["message"] == "updated"


def test_message_detail_put_requires_text(client, db):
    message_id = db.create_message("Bob", "bob@example.com", "original")
    response = client.put(f"/api/messages/{message_id}", json={"message": "   "})
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_message_detail_delete(client, db):
    message_id = db.create_message("Bob", "bob@example.com", "bye")
    response = client.delete(f"/api/messages/{message_id}")
    assert response.status_code == 200
    assert db.get_messages() == []


def test_projects_api_get(client, db):
    db.create_project("P1", "s1", "d1")
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_projects_api_post_missing_fields(client):
    response = client.post("/api/projects", json={"title": "only title"})
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_projects_api_post_success(client):
    response = client.post(
        "/api/projects",
        json={"title": "New", "summary": "sum", "description": "desc"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert "id" in body


def test_project_detail_api_put_updates(client, db):
    project_id = db.create_project("Old", "old", "old")
    response = client.put(
        f"/api/projects/{project_id}",
        json={"title": "New", "summary": "new", "description": "new"},
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert db.get_project(project_id)["title"] == "New"


def test_project_detail_api_put_requires_fields(client, db):
    project_id = db.create_project("Old", "old", "old")
    response = client.put(f"/api/projects/{project_id}", json={"title": "New"})
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_project_detail_api_delete(client, db):
    project_id = db.create_project("Doomed", "s", "d")
    response = client.delete(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert db.get_project(project_id) is None
