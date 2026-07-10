import sqlite3


def test_init_db_creates_tables(db):
    with db.get_connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert {"messages", "projects"}.issubset(tables)


def test_init_db_is_idempotent(db):
    db.init_db()
    db.init_db()
    with db.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()["c"]
    assert count == 0


def test_get_connection_uses_row_factory(db):
    with db.get_connection() as conn:
        assert conn.row_factory is sqlite3.Row


def test_seed_projects_inserts_defaults(db):
    db.seed_projects()
    projects = db.get_projects()
    assert len(projects) == 2
    titles = {p["title"] for p in projects}
    assert titles == {"Portfolio Website", "Basic Backend App"}


def test_seed_projects_does_not_duplicate(db):
    db.seed_projects()
    db.seed_projects()
    assert len(db.get_projects()) == 2


def test_seed_projects_skips_when_data_present(db):
    db.create_project("Existing", "summary", "description")
    db.seed_projects()
    projects = db.get_projects()
    assert len(projects) == 1
    assert projects[0]["title"] == "Existing"


def test_create_and_get_project(db):
    project_id = db.create_project("Title", "Summary", "Description")
    assert isinstance(project_id, int)

    project = db.get_project(project_id)
    assert project["id"] == project_id
    assert project["title"] == "Title"
    assert project["summary"] == "Summary"
    assert project["description"] == "Description"
    assert "created_at" in project


def test_get_project_returns_none_when_missing(db):
    assert db.get_project(999) is None


def test_get_projects_ordered_by_id_desc(db):
    first = db.create_project("First", "s1", "d1")
    second = db.create_project("Second", "s2", "d2")
    projects = db.get_projects()
    assert [p["id"] for p in projects] == [second, first]


def test_update_project(db):
    project_id = db.create_project("Old", "old summary", "old description")
    db.update_project(project_id, "New", "new summary", "new description")

    project = db.get_project(project_id)
    assert project["title"] == "New"
    assert project["summary"] == "new summary"
    assert project["description"] == "new description"


def test_delete_project(db):
    project_id = db.create_project("Doomed", "s", "d")
    db.delete_project(project_id)
    assert db.get_project(project_id) is None
    assert db.get_projects() == []


def test_create_and_get_messages(db):
    message_id = db.create_message("Alice", "alice@example.com", "Hello there")
    assert isinstance(message_id, int)

    messages = db.get_messages()
    assert len(messages) == 1
    message = messages[0]
    assert message["id"] == message_id
    assert message["name"] == "Alice"
    assert message["email"] == "alice@example.com"
    assert message["message"] == "Hello there"
    assert message["status"] == "new"
    assert "created_at" in message


def test_get_messages_ordered_by_id_desc(db):
    first = db.create_message("A", "a@example.com", "first")
    second = db.create_message("B", "b@example.com", "second")
    messages = db.get_messages()
    assert [m["id"] for m in messages] == [second, first]


def test_get_messages_empty(db):
    assert db.get_messages() == []


def test_update_message(db):
    message_id = db.create_message("Bob", "bob@example.com", "original")
    db.update_message(message_id, "edited text", "read")

    message = db.get_messages()[0]
    assert message["message"] == "edited text"
    assert message["status"] == "read"


def test_delete_message(db):
    message_id = db.create_message("Carol", "carol@example.com", "bye")
    db.delete_message(message_id)
    assert db.get_messages() == []
