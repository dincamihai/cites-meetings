import re
import psycopg2.pool, psycopg2.extras
import flask


class Person(dict):
    id = None


def save_person(person):
    cursor = get_cursor()
    cursor.execute("INSERT INTO person (data) VALUES (%s)", (person,))


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
        flask.g.psycopg2_conn = app._connection_pool.getconn()
        psycopg2.extras.register_hstore(flask.g.psycopg2_conn,
                                        globally=False, unicode=True)
    flask.g.psycopg2_conn
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
    app._connection_pool = psycopg2.pool.ThreadedConnectionPool(0, 5, **params)

    @app.teardown_request
    def finalize_connection(response):
        if hasattr(flask.g, 'psycopg2_conn'):
            app._connection_pool.putconn(flask.g.psycopg2_conn)
            del flask.g.psycopg2_conn
