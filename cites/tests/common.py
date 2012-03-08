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
    app.config['DATABASE_URI'] = _get_testing_db_uri()
    app.config['SEND_REAL_EMAILS'] = False
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