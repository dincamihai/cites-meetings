import unittest
from urlparse import urlparse
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

    def test_new_participant_submit(self):
        form_resp = self.client.post('/meeting/1/participant/new', data={
            'personal_name_title': u"Mr",
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
        })
        url_path = urlparse(form_resp.location).path
        self.assertEqual(url_path, '/meeting/1/participant/1')

        view_resp = self.client.get(url_path)
        self.assertIn("Person information saved", view_resp.data)

        [first_name_th] = select(view_resp.data, 'tr th:contains("First name")')
        self.assertElementIn('td:contains("Joe")', first_name_th.getparent())

    def _create_participant(self):
        return self.client.post('/meeting/1/participant/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
        })

    def test_delete_participant(self):
        person_url = urlparse(self._create_participant().location).path
        resp1 = self.client.get(person_url)
        self.assertEqual(resp1.status_code, 200)

        del_resp = self.client.delete('/delete/1')
        self.assertEqual(del_resp.status_code, 200)

        resp2 = self.client.get(person_url)
        self.assertEqual(resp2.status_code, 404)
