import re
import psycopg2.pool, psycopg2.extras
import flask


class Person(dict):
    id = None

    @property
    def name(self):
        return "%s %s %s" % (
            self["personal_name_title"],
            self["personal_first_name"],
            self["personal_last_name"],
        )


COPY_BUFFER_SIZE = 2**14
def _iter_file(src_file, close=False):
    try:
        while True:
            block = src_file.read()
            if not block:
                break
            yield block
    finally:
        if close:
            src_file.close()


class DbFile(object):

    def __init__(self, session, id):
        self.id = id
        self._session = session

    def save_from(self, in_file):
        lobject = self._session.conn.lobject(self.id, 'wb')
        try:
            for block in _iter_file(in_file):
                lobject.write(block)
        finally:
            lobject.close()

    def iter_data(self):
        lobject = self._session.conn.lobject(self.id, 'rb')
        return _iter_file(lobject, close=True)


class Session(object):

    def __init__(self, conn, debug=False):
        self._conn = conn
        self._debug = debug

    @property
    def conn(self):
        if self._conn is None:
            raise ValueError("Error: trying to use expired database session")
        return self._conn

    def _release_conn(self):
        conn = self._conn
        self._conn = None
        return conn

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
        person = Person(data)
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
            person = Person(person_data)
            person.id = person_id
            yield person

    def get_db_file(self, id=None):
        if id is None:
            id = self.conn.lobject(mode='n').oid
        return DbFile(self, id)

    def del_db_file(self, id):
        self.conn.lobject(id, mode='n').unlink()

    def create_all(self):
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE person("
                            "id SERIAL PRIMARY KEY, "
                            "data HSTORE)")
        cursor.connection.commit()

    def drop_all(self):
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE person")
        cursor.execute("SELECT DISTINCT loid FROM pg_largeobject")
        for [oid] in cursor:
            self.conn.lobject(oid, 'n').unlink()
        cursor.connection.commit()

    def commit(self):
        self.conn.commit()


def get_session():
    if not hasattr(flask.g, 'psycopg2_session'):
        pool = flask.current_app.extensions['psycopg2_pool']
        conn = pool.getconn()
        psycopg2.extras.register_hstore(conn, globally=False, unicode=True)
        session = Session(conn, debug=flask.current_app.debug)
        flask.g.psycopg2_session = session
    return flask.g.psycopg2_session


def transform_connection_uri(connection_uri):
    m = re.match(r"^postgresql://"
                 r"((?P<user>[^:]*)(:(?P<password>[^@]*))@?)?"
                 r"(?P<host>[^/]+)/(?P<db>[^/]+)$",
                 connection_uri)
    if m is None:
        raise ValueError("Can't parse connection URI %r" % connection_uri)
    return {
        'database': m.group('db'),
        'host': m.group('host'),
        'user': m.group('user'),
        'password': m.group('password'),
    }


def initialize_app(app):
    params = transform_connection_uri(app.config['DATABASE_URI'])
    pool = psycopg2.pool.ThreadedConnectionPool(0, 5, **params)
    app.extensions['psycopg2_pool'] = pool

    @app.teardown_request
    def finalize_connection(response):
        session = getattr(flask.g, 'psycopg2_session', None)
        if session is not None:
            app.extensions['psycopg2_pool'].putconn(session._release_conn())
            del flask.g.psycopg2_session
