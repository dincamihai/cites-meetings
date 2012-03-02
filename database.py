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
    if not hasattr(flask.g, 'psycopg2_session'):
        pool = flask.current_app.extensions['psycopg2_pool']
        conn = pool.getconn()
        htables.psycopg2.extras.register_hstore(conn, globally=False, unicode=True)
        session = htables.Session(htables_schema, conn, debug=flask.current_app.debug)
        flask.g.psycopg2_session = session
    return flask.g.psycopg2_session


def initialize_app(app):
    params = htables.transform_connection_uri(app.config['DATABASE_URI'])
    pool = htables.psycopg2.pool.ThreadedConnectionPool(0, 5, **params)
    app.extensions['psycopg2_pool'] = pool

    @app.teardown_request
    def finalize_connection(response):
        session = getattr(flask.g, 'psycopg2_session', None)
        if session is not None:
            app.extensions['psycopg2_pool'].putconn(session._release_conn())
            del flask.g.psycopg2_session
