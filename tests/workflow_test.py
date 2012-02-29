import unittest
import flask
from common import create_mock_app, select


class ParticipantWorkflowTest(unittest.TestCase):

    def setUp(self):
        self.app, app_teardown = create_mock_app()
        self.addCleanup(app_teardown)
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in_email"] = "tester@example.com"

    def test_access_form(self):
        resp = self.client.get('/meeting/1', follow_redirects=True)
        links = select(resp.data, 'a[href="/meeting/1/participant/new"]')
        self.assertEqual(len(links), 1)
