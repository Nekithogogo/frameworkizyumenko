import pytest

from db import database, import_json


@pytest.fixture
def sqlite_db(tmp_path, monkeypatch):
    """Временная база SQLite, заполненная из JSON-файлов проекта.

    Тесты не трогают рабочий файл data/certhub.sqlite: модуль
    db.database на время теста указывает на копию во временном каталоге.
    """
    db_path = tmp_path / "certhub_test.sqlite"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    import_json.main()
    return db_path
