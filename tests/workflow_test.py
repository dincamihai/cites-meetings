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

    def assertElementIn(self, selector, html):
        error_message = "No element matching %r found in page" % (selector,)
        self.assertTrue(len(select(html, selector)) > 0, error_message)

    def test_access_form(self):
        resp = self.client.get('/meeting/1', follow_redirects=True)
        self.assertElementIn('a[href="/meeting/1/participant/new"]', resp.data)

    def test_new_participant_page(self):
        resp = self.client.get('/meeting/1/participant/new')
        self.assertElementIn('h1:contains("New participant")', resp.data)
        self.assertElementIn('form[method="post"] '
                             'input[name="personal_name_title"]',
                             resp.data)
