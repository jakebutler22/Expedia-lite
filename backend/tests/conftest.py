import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import connect_database, initialize_database
from app.main import create_app


DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "expedia-lite.db"


@pytest.fixture
def connection(database_path: Path) -> Iterator[sqlite3.Connection]:
    initialize_database(database_path, DATA_DIRECTORY)
    database = connect_database(database_path)
    try:
        yield database
    finally:
        database.close()


@pytest.fixture
def client(database_path: Path) -> Iterator[TestClient]:
    application = create_app(database_path, DATA_DIRECTORY)
    with TestClient(application) as test_client:
        yield test_client
