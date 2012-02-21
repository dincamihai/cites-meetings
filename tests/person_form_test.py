import unittest


_testing_db_uri = None
def _get_testing_db_uri():
    global _testing_db_uri
    from app import create_app
    if _testing_db_uri is None:
        tmp_app = create_app()
        _testing_db_uri = tmp_app.config['TESTING_SQLALCHEMY_DATABASE_URI']
    return _testing_db_uri


def _create_testing_app():
    from app import create_app
    import database

    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = _get_testing_db_uri()
    database.adb.init_app(app)
    with app.test_request_context():
        database.adb.create_all()

    def app_teardown():
        with app.test_request_context():
            database.adb.drop_all()

    return app, app_teardown


class PersonFormTest(unittest.TestCase):

    def setUp(self):
        self.app, app_teardown = _create_testing_app()
        self.addCleanup(app_teardown)
        self.client = self.app.test_client()

    def test_homepage(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
