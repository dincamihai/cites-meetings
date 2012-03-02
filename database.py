import flask
import htables


class PersonRow(htables.TableRow):
    _table = 'person'


class AppSession(htables.Session):

    def save_person(self, person):
        self.table(person).save(person)

    def get_person(self, person_id):
        return self.table(PersonRow).get(person_id)

    def get_person_or_404(self, person_id):
        try:
            return self.get_person(person_id)
        except KeyError:
            flask.abort(404)

    def del_person(self, person_id):
        self.table(PersonRow).delete(person_id)

    def get_all_persons(self):
        return self.table(PersonRow).get_all()

    def create_all(self):
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE person("
                            "id SERIAL PRIMARY KEY, "
                            "data HSTORE)")
        cursor.connection.commit()

    def drop_all(self):
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE person")
        cursor.execute("SELECT oid FROM pg_largeobject_metadata")
        for [oid] in cursor:
            self.conn.lobject(oid, 'n').unlink()
        cursor.connection.commit()


def get_session():
    if not hasattr(flask.g, 'psycopg2_session'):
        pool = flask.current_app.extensions['psycopg2_pool']
        conn = pool.getconn()
        htables.psycopg2.extras.register_hstore(conn, globally=False, unicode=True)
        session = AppSession(conn, debug=flask.current_app.debug)
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
