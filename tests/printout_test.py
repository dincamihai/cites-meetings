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
            'personal_fee': "5",
            'meeting_flags_invitation': True,
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

        [details_of_registration] = select(resp.data, ".subheader h3")
        details_of_registration = details_of_registration.text_content()
        self.assertIn(u"Member", details_of_registration)

        self.assertIn(u"Region", value_for_label(resp.data, "Representative of"))
        self.assertIn(u"Not required", value_for_label(resp.data, "Invitation received"))

    def test_alternate_member(self):
        self._create_participant(u"20") # 20: "Alternate Member"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Alternate member",
                      value_for_label(resp.data, "Category"))

        [details_of_registration] = select(resp.data, ".subheader h3")
        details_of_registration = details_of_registration.text_content()
        self.assertIn(u"Alternate member", details_of_registration)

        self.assertIn(u"Country", value_for_label(resp.data, "Representative of"))
        self.assertIn(u"Not required",
                      value_for_label(resp.data, "Invitation received"))

    def test_observer_party(self):
        self._create_participant(u"30") # 30: "Observer, Party"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Observer, Party",
                      value_for_label(resp.data, "Category"))

        [details_of_registration] = select(resp.data, ".subheader h3")
        details_of_registration = details_of_registration.text_content()
        self.assertIn(u"Observer, Party", details_of_registration)

        self.assertIn(u"Country",
                      value_for_label(resp.data, "Representative of"))
        self.assertIn(u"Not required",
                      value_for_label(resp.data, "Invitation received"))

    def test_observer_international(self):
        self._create_participant(u"80") # 80: "Observer, International NGO"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Observer, International NGO",
                    value_for_label(resp.data, "Category"))

        [details_of_registration] = select(resp.data, ".subheader h3")
        details_of_registration = details_of_registration.text_content()
        self.assertIn(u"Observer", details_of_registration)

        self.assertIn(u"Organisation",
                      value_for_label(resp.data, "Representative of"))
        self.assertIn(u"Yes",
                      value_for_label(resp.data, "Invitation received"))

    def test_conference_staff(self):
        self._create_participant(u"98") # 98: "Conference staff"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Conference staff",
                      value_for_label(resp.data, "Category"))

        [details_of_registration] = select(resp.data, ".subheader h3")
        details_of_registration = details_of_registration.text_content()
        self.assertIn(u"Observer", details_of_registration)
        self.assertIn(u"Description",
                      value_for_label(resp.data, "Representative of"))

    def test_visitor(self):
        self._create_participant(u"1") # 1: "Visitor"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Visitor", value_for_label(resp.data, "Category"))

    def test_observer_ngo(self):
        self._create_participant(u"80") # 80: "Observer, International NGO"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Observer, International NGO",
                      value_for_label(resp.data, "Category"))

    def test_special_guest_of_the_secretary_general(self):
        self._create_participant(u"0") # 0: "pecial_guest_of_the_secretary_general"
        resp = self.client.get("/meeting/1/participant/1/credentials")

        self.assertIn(u"Special guest of the Secretary General",
                      value_for_label(resp.data, "Category"))

