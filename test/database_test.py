from database import Database


db = Database()


def test_instance():
    assert isinstance(db, Database)


def test_initialize():
    db.initialize()
    assert db.db is not None