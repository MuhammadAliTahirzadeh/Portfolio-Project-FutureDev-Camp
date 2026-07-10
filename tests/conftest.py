import tempfile
from pathlib import Path

import pytest

# ``app`` runs ``init_db()``/``seed_projects()`` at import time. Redirect the
# database at collection time (before ``app`` is first imported) so those
# side effects never touch the real repository directory.
import portfolio_db

portfolio_db.DB_PATH = Path(tempfile.gettempdir()) / "portfolio_test_import.db"


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Point the database module at an isolated, freshly initialised SQLite file."""
    import portfolio_db

    db_path = tmp_path / "test_portfolio.db"
    monkeypatch.setattr(portfolio_db, "DB_PATH", db_path)
    portfolio_db.init_db()
    return portfolio_db


@pytest.fixture
def client(db, monkeypatch):
    """Flask test client backed by the isolated database.

    ``app`` imports the CRUD helpers by name, so the module-level references are
    repointed at the isolated-database implementations for the duration of a test.
    """
    import app as app_module

    for name in (
        "init_db",
        "seed_projects",
        "get_projects",
        "get_project",
        "create_project",
        "update_project",
        "delete_project",
        "get_messages",
        "create_message",
        "update_message",
        "delete_message",
    ):
        monkeypatch.setattr(app_module, name, getattr(db, name))

    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client
