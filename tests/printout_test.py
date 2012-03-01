import unittest
from urlparse import urlparse
import flask
from common import create_mock_app, select


def parent(element, parent_tag):
    while element is not None:
        if element.tag == parent_tag:
            return element
        element = element.getparent()
    else:
        raise ValueError("No parent for %r with tag %r" % (element, parent_tag))

def value_for_label(html, label, text=True):
    [title] = select(html, 'div.title:contains("%s")' % label)
    [content] = select(parent(title, 'li'), 'div.content')
    if text:
        return content.text_content()
    else:
        return content


class CredentialsTest(unittest.TestCase):

    def setUp(self):
        self.app, app_teardown = create_mock_app()
        self.addCleanup(app_teardown)
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in_email"] = "tester@example.com"

    def _create_participant(self, category):
        return self.client.post('/meeting/1/participant/new', data={
            'personal_first_name': u"Joe",
            'personal_last_name': u"Smith",
            'personal_category': category,
            'personal_language': u"F", # "F": "French"
        })

    def test_common_fields(self):
        self._create_participant(u"10") # 10: "Member"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Joe Smith", value_for_label(resp.data, "Name and address"))
        self.assertIn(u"French", value_for_label(resp.data, "Language"))
        self.assertIn(u"Not required",
                      value_for_label(resp.data, "Invitation received"))
        self.assertIn(u"No", value_for_label(resp.data, "Web Alerts"))

    def test_member(self):
        self._create_participant(u"10") # 10: "Member"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Member", value_for_label(resp.data, "Category"))
