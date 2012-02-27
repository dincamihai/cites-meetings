import unittest
import flask
from common import create_mock_app


class PersonFormTest(unittest.TestCase):

    def setUp(self):
        self.app, app_teardown = create_mock_app()
        self.addCleanup(app_teardown)
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in_email"] = "tester@example.com"

    def _get_person_data(self):
        import database
        with self.app.test_request_context():
            return list(database.get_session().get_all_persons())

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
            'meeting_flags_invitation': '',
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['meeting_flags_invitation'], u"")

    def test_bool_true(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'meeting_flags_invitation': 'on',
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['meeting_flags_invitation'], u"1")

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
            'meeting_flags_acknowledged': u"",
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['meeting_flags_acknowledged'], u"")


    def test_date_err(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'meeting_flags_acknowledged': u"2010-15-01", # year-day-month, should be invalid
        }, follow_redirects=True)

        self.assertIn("Date acknowledged is not a valid date", resp.data)
        self.assertEqual(self._get_person_data(), [])

    def test_date_ok(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'meeting_flags_acknowledged': u"2010-01-15", # year-month-day, should be ok
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['meeting_flags_acknowledged'], u"2010-01-15")

    def test_phone_empty(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'personal_cellular': u"",
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['personal_cellular'], u"")


    def test_phone_err(self):
        from nose import SkipTest
        raise SkipTest()

        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'personal_cellular': u"xkcd",
        }, follow_redirects=True)

        self.assertIn("Cellular is not valid", resp.data)
        self.assertEqual(self._get_person_data(), [])

    def test_phone_ok(self):
        resp = self.client.post('/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'personal_cellular': u"123 45 6789",
        }, follow_redirects=True)
        self.assertIn("Person information saved", resp.data)

        [data] = self._get_person_data()
        self.assertEqual(data['personal_cellular'], u"123 45 6789")


class PhoneValidatorTest(unittest.TestCase):

    ok_values = [
        '123 456 7890',
        '1 2 3',
        '12 3456 7890',
    ]

    bad_values = [
        'xzzx',
        '+123 456 7890',
        '(123) 456 7890',
    ]

    def test_ok_values(self):
        from schema import IsPhone, CommonString
        PhoneField = CommonString.including_validators(IsPhone())

        for value in self.ok_values:
            element = PhoneField(value)
            self.assertTrue(element.validate(),
                            "Valid phone %r triggered error" % value)

    def test_bad_values(self):
        from schema import IsPhone, CommonString
        PhoneField = CommonString.including_validators(IsPhone())

        for value in self.bad_values:
            element = PhoneField(value)
            self.assertFalse(element.validate(),
                             "Invalid phone %r did not trigger error" % value)
