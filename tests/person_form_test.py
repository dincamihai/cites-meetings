import unittest
import flask


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

    def _get_person_data(self):
        import database
        with self.app.test_request_context():
            return [flask.json.loads(person_row.data)
                    for person_row in database.Person.query.all()]

    def test_homepage(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_minimal_ok(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['personal_first_name'], u"Joe")
        self.assertEqual(data['personal_last_name'], u"Smith")

    def test_error_no_save(self):
        resp = self.client.post('/new', data={
        }, follow_redirects=True)

        self.assertIn("Errors in person information", resp.data)
        self.assertEqual(self._get_person_data(), [])

    def test_first_name_blank(self):
        resp = self.client.post('/new', data={
            'personal_last_name': u"Smith",
        }, follow_redirects=True)

        self.assertIn("First name is required", resp.data)
        self.assertEqual(self._get_person_data(), [])

    def test_bool_false(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'type_invitation': '',
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['type_invitation'], u"")

    def test_bool_true(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'type_invitation': 'on',
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['type_invitation'], u"1")

    def test_enum_blank(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['personal_country'], u"")

    def test_enum_value(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'personal_country': u"IT",
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['personal_country'], u"IT")

    def test_enum_invalid(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'personal_country': u"XKCD",
        }, follow_redirects=True)
        self.assertIn("XKCD is not a valid value for Country.", resp.data)

        self.assertEqual(self._get_person_data(), [])

    def test_date_empty(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'info_acknowledge': u"",
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['info_acknowledge'], u"")


    def test_date_err(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'info_acknowledge': u"2010-15-01", # year-day-month, should be invalid
        }, follow_redirects=True)

        self.assertIn("Date acknowledge is not a valid date", resp.data)
        self.assertEqual(self._get_person_data(), [])

    def test_date_ok(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'info_acknowledge': u"2010-01-15", # year-month-day, should be ok
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['info_acknowledge'], u"2010-01-15")
