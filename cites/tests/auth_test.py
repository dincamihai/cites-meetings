from common import _BaseTest


PROTECTED_ROUTES = (
    "/",
    "/meeting/1/participant/1",
    "/meeting/1/participant/1/credentials",
    "/meeting/1/participant/1/badge",
    "/meeting/1/participant/new",
    "/meeting/1/participant/1/edit",
    "/refdata/us-states",
    "/meeting/1/participant/1/edit_photo",
    "/meeting/1/participant/1/send_mail",
    "/meeting/1/participant/1/credentials.pdf",
    "/meeting/1",
    "/meeting/1/registration",
    "/meeting/1/printouts",
    "/meeting/1/printouts/verified/short_list",
    "/meeting/1/printouts/verified/meeting_room",
    "/meeting/1/printouts/verified/pigeon_holes_verified",
    "/meeting/1/printouts/verified/pigeon_holes_attended",
    "/meeting/1/settings/phrases",
    "/meeting/1/settings/fees",
    "/meeting/1/settings/categories",
)

class AuthTest(_BaseTest):

    def test_protected_routes(self):
        with self.client.session_transaction() as session:
            session["logged_in_email"] = None
        self._create_participant(u"10")

        for route in PROTECTED_ROUTES:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/login?next", resp.headers["Location"])

    def test_loggin_route(self):
        resp = self.client.get(PROTECTED_ROUTES[0])
        self.assertEqual(resp.status_code, 200)


