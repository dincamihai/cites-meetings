
import unittest

class _BaseTest(unittest.TestCase):

    def setUp(self):
        self.app, app_teardown = create_mock_app()
        self.addCleanup(app_teardown)
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["logged_in_email"] = "tester@example.com"

    def _create_participant(self, category, default_data={}):
        data = {
            "personal_first_name": u"Joe",
            "personal_last_name": u"Smith",
            "personal_category": category,
            "personal_language": u"F", # "F": "French"
            "personal_fee": "1",
            "meeting_flags_invitation": True,
            "meeting_flags_credentials": False,
            "meeting_flags_verified": True,
            "representing_region": "4",
            "representing_country": u"RO",
            "representing_organization": u"International Environmental Law Project",
        }
        data.update(default_data)
        return self.client.post('/meeting/1/participant/new', data=data)


_testing_db_uri = None
def _get_testing_db_uri():
    global _testing_db_uri
    from cites.app import create_app
    if _testing_db_uri is None:
        tmp_app = create_app()
        _testing_db_uri = tmp_app.config['TESTING_DATABASE_URI']
    return _testing_db_uri


def create_mock_app():
    from cites.app import create_app
    from cites import database

    app = create_app()
    app.config["DATABASE_URI"] = _get_testing_db_uri()
    app.config["TESTING"] = True
    app.config["MAIL_SUPPRESS_SEND"] = True
    database.initialize_app(app)
    with app.test_request_context():
        database.get_session().create_all()

    def app_teardown():
        with app.test_request_context():
            database.get_session().drop_all()

    return app, app_teardown


def select(container, selector):
    """ Select elements using CSS """
    import lxml.html, lxml.cssselect
    if isinstance(container, basestring):
        doc = lxml.html.fromstring(container)
    else:
        doc = container
    xpath = lxml.cssselect.CSSSelector(selector)
    return xpath(doc)

