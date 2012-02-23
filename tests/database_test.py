import unittest
import flask


_testing_db_uri = None
def _get_testing_db_uri():
    global _testing_db_uri
    from app import create_app
    if _testing_db_uri is None:
        tmp_app = create_app()
        _testing_db_uri = tmp_app.config['TESTING_DATABASE_URI']
    return _testing_db_uri


def _create_testing_app():
    from app import create_app
    import database

    app = create_app()
    app.config['DATABASE_URI'] = _get_testing_db_uri()
    database.initialize_app(app)
    with app.test_request_context():
        database.create_all()

    def app_teardown():
        with app.test_request_context():
            database.drop_all()

    return app, app_teardown


class PersonModelTest(unittest.TestCase):

    def setUp(self):
        self.app, app_teardown = _create_testing_app()
        self.addCleanup(app_teardown)
        self.client = self.app.test_client()

    def test_save(self):
        import database
        with self.app.test_request_context():
            p = database.Person()
            p["hello"] = "world"
            database.save_person(p)
            database.commit()

        with self.app.test_request_context():
            cursor = database.get_cursor()
            cursor.execute("SELECT * FROM person")
            [row] = list(cursor)
            self.assertEqual(row[1], {u"hello": u"world"})
