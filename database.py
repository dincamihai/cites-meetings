import flask
import htables


class PersonRow(htables.TableRow):
    pass


class AppSession(htables.Session):

    def save_person(self, person):
        cursor = self.conn.cursor()
        if self._debug:
            for key, value in person.iteritems():
                assert isinstance(key, basestring), \
                    "Key %r is not a string" % key
                assert isinstance(value, basestring), \
                    "Value %r for key %r is not a string" % (value, key)
        if person.id is None:
            cursor.execute("INSERT INTO person (data) VALUES (%s)", (person,))
            cursor.execute("SELECT CURRVAL('person_id_seq')")
            [(person.id,)] = list(cursor)
        else:
            cursor.execute("UPDATE person SET data = %s WHERE id = %s",
                           (person, person.id))

    def get_person(self, person_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM person WHERE id = %s", (person_id,))
        rows = list(cursor)
        if len(rows) == 0:
            raise KeyError("No person with id=%d" % person_id)
        [(data,)] = rows
        person = PersonRow(data)
        person.id = person_id
        return person

    def get_person_or_404(self, person_id):
        try:
            return self.get_person(person_id)
        except KeyError:
            flask.abort(404)

    def del_person(self, person_id):
        assert isinstance(person_id, int)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM person WHERE id = %s", (person_id,))

    def get_all_persons(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, data FROM person")
        for person_id, person_data in cursor:
            person = PersonRow(person_data)
            person.id = person_id
            yield person

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
