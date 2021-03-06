import unittest
from urlparse import urlparse
import flask
from common import create_mock_app, select


class ParticipantCrudWorkflowTest(unittest.TestCase):

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

    def test_remove_participant(self):
        person_url = urlparse(self._create_participant().location).path
        resp1 = self.client.get(person_url)
        self.assertEqual(resp1.status_code, 200)

        del_resp = self.client.delete('/meeting/1/participant/1')
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(flask.json.loads(del_resp.data),
                         {'status': 'success'})

        resp2 = self.client.get(person_url)
        self.assertEqual(resp2.status_code, 404)


class ParticipantEmailWorkflowTest(unittest.TestCase):

    def setUp(self):
        self.app, app_teardown = create_mock_app()
        self.addCleanup(app_teardown)
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in_email"] = "tester@example.com"
        self.client.post('/meeting/1/participant/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'personal_email': u"jsmith@example.com",
        })

    def test_send_email_page(self):
        view_resp = self.client.get('/meeting/1/participant/1')
        [link] = select(view_resp.data, 'a:contains("Acknowledge email")')
        email_url = '/meeting/1/participant/1/send_mail'
        self.assertEqual(link.attrib['href'], email_url)

        email_resp = self.client.get(email_url)
        self.assertEqual(email_resp.status_code, 200)

        [to_input] = select(email_resp.data, 'input[name=to]')
        self.assertEqual(to_input.attrib['value'], "jsmith@example.com")
