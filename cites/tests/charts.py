import flask
from common import _BaseTest

class ChartsTest(_BaseTest):

    def test_charts(self):
        from cites import charts
        i = 0
        while i < 10:
            self._create_participant(u"10")
            i += 1

        i = 0
        while i < 5:
            self._create_participant(u"20")
            i += 1

        self._create_participant(u"98")

        with self.app.test_request_context("/meeting/1/charts"):
            flask.session["logged_in_email"] = "tester@example.com"
            resp = charts.home.not_templated()

            categories = resp["categories"]
            self.assertEqual(categories,
                            [(u"Member", 62),
                             (u"Alternate member", 31),
                             (u"Conference staff", 6)])
