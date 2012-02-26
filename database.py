import re
import psycopg2.pool, psycopg2.extras
import flask


class Person(dict):
    id = None


def save_person(person):
    cursor = get_cursor()
    if person.id is None:
        cursor.execute("INSERT INTO person (data) VALUES (%s)", (person,))
        cursor.execute("SELECT CURRVAL('person_id_seq')")
        [(person.id,)] = list(cursor)
    else:
        cursor.execute("UPDATE person SET data = %s WHERE id = %s",
                       (person, person.id))


def get_person(person_id):
    cursor = get_cursor()
    cursor.execute("SELECT data FROM person WHERE id = %s", (person_id,))
    rows = list(cursor)
    if len(rows) == 0:
        raise KeyError("No person with id=%d" % person_id)
    [(data,)] = rows
    person = Person(data)
    person.id = person_id
    return person


def del_person(person_id):
    assert isinstance(person_id, int)
    cursor = get_cursor()
    cursor.execute("DELETE FROM person WHERE id = %s", (person_id,))


def transform_connection_uri(connection_uri):
    m = re.match(r"^postgresql://(?P<host>[^/]+)/(?P<db>[^/]+)$", connection_uri)
    if m is None:
        raise ValueError("Can't parse connection URI %r" % connection_uri)
    return {
        'database': m.group('db'),
        'host': m.group('host'),
    }


def get_cursor():
    if not hasattr(flask.g, 'psycopg2_conn'):
        app = flask.current_app
        flask.g.psycopg2_conn = app.extensions['psycopg2_pool'].getconn()
        psycopg2.extras.register_hstore(flask.g.psycopg2_conn,
                                        globally=False, unicode=True)
    return flask.g.psycopg2_conn.cursor()


def create_all():
    cursor = get_cursor()
    cursor.execute("CREATE TABLE person("
                        "id SERIAL PRIMARY KEY, "
                        "data HSTORE)")
    cursor.connection.commit()

def drop_all():
    cursor = get_cursor()
    cursor.execute("DROP TABLE person")
    cursor.connection.commit()


def commit():
    get_cursor().connection.commit()


def initialize_app(app):
    params = transform_connection_uri(app.config['DATABASE_URI'])
    pool = psycopg2.pool.ThreadedConnectionPool(0, 5, **params)
    app.extensions['psycopg2_pool'] = pool

    @app.teardown_request
    def finalize_connection(response):
        conn = getattr(flask.g, 'psycopg2_conn', None)
        if conn is not None:
            app.extensions['psycopg2_pool'].putconn(conn)
            del flask.g.psycopg2_conn
