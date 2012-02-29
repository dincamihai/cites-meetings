_testing_db_uri = None
def _get_testing_db_uri():
    global _testing_db_uri
    from app import create_app
    if _testing_db_uri is None:
        tmp_app = create_app()
        _testing_db_uri = tmp_app.config['TESTING_DATABASE_URI']
    return _testing_db_uri


def create_mock_app():
    from app import create_app
    import database

    app = create_app()
    app.config['DATABASE_URI'] = _get_testing_db_uri()
    database.initialize_app(app)
    with app.test_request_context():
        database.get_session().create_all()

    def app_teardown():
        with app.test_request_context():
            database.get_session().drop_all()

    return app, app_teardown


def select(html, selector):
    """ Select elements using CSS """
    import lxml.html, lxml.cssselect
    doc = lxml.html.fromstring(html)
    xpath = lxml.cssselect.CSSSelector(selector)
    return xpath(doc)
