import re
import psycopg2.pool, psycopg2.extras


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


class TableRow(dict):

    id = None


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


class Table(object):

    def __init__(self, row_cls, session):
        self._session = session
        self._row_cls = row_cls
        self._name = row_cls._table

    def save(self, obj):
        cursor = self._session.conn.cursor()
        if self._session._debug:
            for key, value in obj.iteritems():
                assert isinstance(key, basestring), \
                    "Key %r is not a string" % key
                assert isinstance(value, basestring), \
                    "Value %r for key %r is not a string" % (value, key)
        if obj.id is None:
            cursor.execute("INSERT INTO " + self._name + " (data) VALUES (%s)",
                           (obj,))
            cursor.execute("SELECT CURRVAL(%s)", (self._name + '_id_seq',))
            [(obj.id,)] = list(cursor)
        else:
            cursor.execute("UPDATE " + self._name + " SET data = %s WHERE id = %s",
                           (obj, obj.id))

    def get(self, obj_id):
        cursor = self._session.conn.cursor()
        cursor.execute("SELECT data FROM " + self._name + " WHERE id = %s",
                       (obj_id,))
        rows = list(cursor)
        if len(rows) == 0:
            raise KeyError("No %r with id=%d" % (self._row_cls, obj_id))
        [(data,)] = rows
        obj = self._row_cls(data)
        obj.id = obj_id
        return obj

    def delete(self, obj_id):
        assert isinstance(obj_id, int)
        cursor = self._session.conn.cursor()
        cursor.execute("DELETE FROM " + self._name + " WHERE id = %s", (obj_id,))

    def get_all(self):
        cursor = self._session.conn.cursor()
        cursor.execute("SELECT id, data FROM " + self._name)
        for ob_id, ob_data in cursor:
            ob = self._row_cls(ob_data)
            ob.id = ob_id
            yield ob


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

    def get_db_file(self, id=None):
        if id is None:
            id = self.conn.lobject(mode='n').oid
        return DbFile(self, id)

    def del_db_file(self, id):
        self.conn.lobject(id, mode='n').unlink()

    def commit(self):
        self.conn.commit()

    def table(self, obj_or_cls):
        if isinstance(obj_or_cls, TableRow):
            row_cls = type(obj_or_cls)
        elif issubclass(obj_or_cls, TableRow):
            row_cls = obj_or_cls
        else:
            raise ValueError("Can't determine table type from %r" %
                             (obj_or_cls,))
        return Table(row_cls, self)


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
