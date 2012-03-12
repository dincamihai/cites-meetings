from urlparse import urlparse
from copy import deepcopy

import unittest
import flask

from cites import database
from cites import schema

from common import _BaseTest, create_mock_app, select
from mock import patch


CATEGORY_MOCK = {
    "1": {
        "name": "Visitor",
        "room_sort": 0,
        "registered": False,
        "id": "1",
        "reg_sort": 0,
        "room": "NULL"

    },
    "10" : {
        "name": "Member",
        "room_sort": 1,
        "registered": True,
        "id": "10",
        "room": "Members"
    },
    "20": {
        "name": "Alternate member",
        "room_sort": 3,
        "registered": True,
        "id": "20",
        "room": "Alternate members & Observers, Party"
    },

    "99" :{
        "name": "CITES Secretariat",
        "room_sort": 0,
        "id": "99",
        "reg_sort": 0,
        "stat_sort": 3,
        "room": "NULL"
    }
}


def parent(element, parent_tag):
    while element is not None:
        if element.tag == parent_tag:
            return element
        element = element.getparent()
    else:
        raise ValueError("No parent for %r with tag %r" % (element, parent_tag))

def value_for_label(html, label, text=True):
    [title] = select(html, 'td.title:contains("%s")' % label)
    [content] = select(parent(title, 'tr'), 'td.content')
    if text:
        return content.text_content()
    else:
        return content


class CredentialsTest(_BaseTest):

    def test_common_fields(self):
        self._create_participant(u"10") # 10: "Member"
        resp = self.client.get('/meeting/1/participant/1/credentials')
        self.assertIn(u"Joe Smith", value_for_label(resp.data, "Name and address"))
        self.assertIn(u"French", value_for_label(resp.data, "Language"))
        self.assertIn(u"Not required",
                      value_for_label(resp.data, "Invitation received"))
        self.assertIn(u"No", value_for_label(resp.data, "Web Alerts"))

        [credentials_content] = select(resp.data, ".credentials-content")
        # check to see if picture alert is present
        self.assertTrue(select(credentials_content, ".alert"))
        # check to see if phrases credentials is on page
        self.assertTrue(select(credentials_content, ".phrases-credentials"))

    def test_member(self):
        self._create_participant(u"10") # 10: "Member"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Member", value_for_label(resp.data, "Category"))

        [details_of_registration] = select(resp.data, ".subheader h3")
        details_of_registration = details_of_registration.text_content()
        self.assertIn(u"Member", details_of_registration)

        self.assertIn("%s - %s" % (schema.region["4"], schema.country["RO"]),
                      value_for_label(resp.data, "Representative of"))
        self.assertIn(u"Not required", value_for_label(resp.data, "Invitation received"))

    def test_alternate_member(self):
        self._create_participant(u"20") # 20: "Alternate Member"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Alternate member",
                      value_for_label(resp.data, "Category"))

        [details_of_registration] = select(resp.data, ".subheader h3")
        details_of_registration = details_of_registration.text_content()
        self.assertIn(u"Alternate member", details_of_registration)

        self.assertIn(schema.country["RO"],
                      value_for_label(resp.data, "Representative of"))
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

        self.assertIn(schema.country["RO"],
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

        self.assertIn(u"International Environmental Law Project",
                      value_for_label(resp.data, "Representative of"))
        self.assertIn(u"Yes",
                      value_for_label(resp.data, "Invitation received"))

        # check to see if phrases.fee and phrases.payment are present
        [credentials_content] = select(resp.data, ".credentials-content")
        [phrases_fee] = select(resp.data, ".phrases-fee")
        [phrases_fee] = select(resp.data, ".phrases-payment")
        [phrases_approval] = select(resp.data, ".phrases-approval")

    def test_conference_staff(self):
        self._create_participant(u"98") # 98: "Conference staff"
        resp = self.client.get('/meeting/1/participant/1/credentials')

        self.assertIn(u"Conference staff",
                      value_for_label(resp.data, "Category"))

        [details_of_registration] = select(resp.data, ".subheader h3")
        details_of_registration = details_of_registration.text_content()
        self.assertIn(u"Observer", details_of_registration)
        self.assertIn(schema.category["98"]["name"],
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


class ListOfParticipantsTest(_BaseTest):

    def test_list_of_participants(self):
        self._create_participant(u"10")
        self._create_participant(u"1")
        resp = self.client.get("/meeting/1/printouts/verified/short_list")

        # conditie: Verif and Cat>9 and Cat<98 and Cat["registered"] is Ture
        with self.app.test_request_context():
            person_row = database.get_person_or_404(1)
            category = schema.category[person_row["personal_category"]]
            self.assertTrue(category["registered"])

        with self.app.test_request_context():
            person_row = database.get_person_or_404(2)
            category = schema.category[person_row["personal_category"]]
            self.assertFalse(category["registered"])

        [representing] = select(resp.data, "table .printout-representing")
        representing = representing.text_content()
        self.assertIn(u"Europe", representing)
        self.assertIn(u"Romania", representing)

    def test_list_of_participants_columns(self):
        self._create_participant(u"10", default_data={
            "meeting_flags_credentials": True,
            "meeting_flags_approval": True,
            "meeting_flags_web_alert": True,
        })

        resp = self.client.get("/meeting/1/printouts/verified/short_list")

        self.assertTrue(select(resp.data, "table .printout-credentials .icon-check"))
        self.assertTrue(select(resp.data, "table .printout-approval .icon-check"))
        self.assertTrue(select(resp.data, "table .printout-webalert .icon-check"))


class BadgeTest(_BaseTest):

    def test_badge(self):
        self._create_participant(u"10")
        resp = self.client.get("/meeting/1/participant/1/badge")

        self.assertTrue(select(resp.data, ".badge-blue-stripe"))

        [person_name] = select(resp.data, ".person-name")
        person_name = person_name.text_content()
        self.assertIn(u"joe", person_name.lower())
        self.assertIn(u"smith", person_name.lower())

        [representative] = select(resp.data, ".person-representing")
        representative = representative.text_content()
        self.assertIn(u"Europe", representative)


class MeetingRoom(_BaseTest):

    @patch("cites.schema.category", deepcopy(CATEGORY_MOCK))
    def test_meeting_room(self):
        from cites import meeting

        self._create_participant(u"10")
        self._create_participant(u"10")
        self._create_participant(u"20")

        with self.app.test_request_context("/meeting/1/printouts/verified/meeting_room"):
            flask.session["logged_in_email"] = "tester@example.com"
            resp = meeting.verified_meeting_room.not_templated()
            participants_in_rooms = resp["participants_in_rooms"]

            # (Cat>9 and Cat<98)
            self.assertEqual(participants_in_rooms.keys(),
                            ["Members", "Alternate members & Observers, Party"])

            values =  participants_in_rooms.values()
            # first user should have region - country room list
            self.assertIn(u"Europe - Romania", values[0]["data"].keys())
            self.assertEqual(values[0]["count"], 2)

            # second user should have country room list
            self.assertIn(u"Romania", values[1]["data"].keys())
            self.assertEqual(values[1]["count"], 1)

    def test_meeting_room_qty(self):
        self._create_participant(u"10")
        self._create_participant(u"10")

        resp = self.client.get("/meeting/1/printouts/verified/meeting_room")
        [qty] = select(resp.data, ".qty")
        self.assertEqual(qty.text_content(), "2")

class PigeonHoles(_BaseTest):

    @patch("cites.schema.category", deepcopy(CATEGORY_MOCK))
    def test_verified_representing_country(self):
        from cites import meeting

        self._create_participant(u"10")
        self._create_participant(u"10")
        self._create_participant(u"20")

        with self.app.test_request_context("/meeting/1/printouts/verified/pigeon_holes_verified"):
            flask.session["logged_in_email"] = "tester@example.com"
            resp = meeting.verified_pigeon_holes.not_templated()
            participants_in_rooms = resp["participants_in_rooms"]

            # (Cat>9 and Cat<98)
            self.assertEqual(participants_in_rooms.keys(),
                            ["Members", "Alternate members & Observers, Party"])

            values =  participants_in_rooms.values()
            # first user should have region - country room list
            self.assertIn(u"Europe - Romania", values[0]["data"].keys())
            self.assertEqual(values[0]["count"], 2)

            # second user should have country room list
            self.assertIn(u"Romania", values[1]["data"].keys())
            self.assertEqual(values[1]["count"], 1)

    def test_qty(self):
        self._create_participant(u"10")
        self._create_participant(u"10")

        resp = self.client.get("/meeting/1/printouts/verified/pigeon_holes_verified")
        [qty] = select(resp.data, ".qty")
        self.assertEqual(qty.text_content(), "2E")


