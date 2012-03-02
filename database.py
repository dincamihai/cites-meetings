import flask
import htables


htables_schema = htables.Schema()

PersonRow = htables_schema.define_table('PersonRow', 'person')


def get_person_or_404(person_id):
    try:
        return get_session().table(PersonRow).get(person_id)
    except KeyError:
        flask.abort(404)


def get_all_persons():
    return get_session().table(PersonRow).get_all()


def get_session():
    if not hasattr(flask.g, 'htables_session'):
        htables_pool = flask.current_app.extensions['htables']
        flask.g.htables_session = htables_pool.get_session()
    return flask.g.htables_session


def initialize_app(app):
    connection_uri = app.config['DATABASE_URI']
    app.extensions['htables'] = htables_schema.bind(connection_uri, app.debug)

    @app.teardown_request
    def finalize_connection(response):
        session = getattr(flask.g, 'htables_session', None)
        if session is not None:
            app.extensions['htables'].put_session(session)
            del flask.g.htables_session
