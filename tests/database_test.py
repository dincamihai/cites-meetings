import unittest
from StringIO import StringIO
import flask
from common import create_mock_app


class PersonModelTest(unittest.TestCase):

    def setUp(self):
        self.app, app_teardown = create_mock_app()
        self.addCleanup(app_teardown)
        self.client = self.app.test_client()

    def test_save(self):
        import database
        with self.app.test_request_context():
            session = database.get_session()
            session.save_person(database.PersonRow(hello="world"))
            session.commit()

        with self.app.test_request_context():
            cursor = database.get_session().conn.cursor()
            cursor.execute("SELECT * FROM person")
            [row] = list(cursor)
            self.assertEqual(row[1], {u"hello": u"world"})

    def test_autoincrement_id(self):
        import database
        with self.app.test_request_context():
            p1 = database.PersonRow()
            p2 = database.PersonRow()
            session = database.get_session()
            session.save_person(p1)
            session.save_person(p2)
            session.commit()
            self.assertEqual(p1.id, 1)
            self.assertEqual(p2.id, 2)

        with self.app.test_request_context():
            cursor = database.get_session().conn.cursor()
            cursor.execute("SELECT * FROM person")
            [row1, row2] = list(cursor)
            self.assertEqual(row1[0], 1)
            self.assertEqual(row2[0], 2)

    def test_load(self):
        import database
        with self.app.test_request_context():
            session = database.get_session()
            session.save_person(database.PersonRow(hello="world"))
            session.commit()

        with self.app.test_request_context():
            person = database.get_session().get_person(1)
            self.assertEqual(person, {"hello": "world"})

    def test_load_not_found(self):
        import database
        with self.app.test_request_context():
            with self.assertRaises(KeyError) as e:
                database.get_session().get_person(13)

    def test_load404_ok(self):
        import database
        with self.app.test_request_context():
            session = database.get_session()
            session.save_person(database.PersonRow(hello="world"))
            session.commit()

        with self.app.test_request_context():
            person = database.get_session().get_person_or_404(1)
            self.assertEqual(person.id, 1)
            self.assertEqual(person, {"hello": "world"})

    def test_load404_error(self):
        import database
        import werkzeug.exceptions
        with self.app.test_request_context():
            with self.assertRaises(werkzeug.exceptions.NotFound) as e:
                database.get_session().get_person_or_404(13)

    def test_load_all(self):
        import database
        with self.app.test_request_context():
            session = database.get_session()
            session.save_person(database.PersonRow(hello="world"))
            session.save_person(database.PersonRow(x="y"))
            session.commit()

        with self.app.test_request_context():
            all_persons = list(database.get_session().get_all_persons())
            self.assertEqual(len(all_persons), 2)
            self.assertEqual(all_persons[0], {'hello': "world"})
            self.assertEqual(all_persons[0].id, 1)
            self.assertEqual(all_persons[1], {'x': "y"})
            self.assertEqual(all_persons[1].id, 2)

    def test_update(self):
        import database
        with self.app.test_request_context():
            session = database.get_session()
            session.save_person(database.PersonRow(k1="v1", k2="v2", k3="v3"))
            session.commit()

        with self.app.test_request_context():
            session = database.get_session()
            person = session.get_person(1)
            del person["k1"] # remove value
            person["k2"] = "vX" # change value
            # person["k3"] unchanged
            person["k4"] = "v4" # add value
            session.save_person(person)
            session.commit()

        with self.app.test_request_context():
            person = database.get_session().get_person(1)
            self.assertEqual(person, {"k2": "vX", "k3": "v3", "k4": "v4"})

    def test_delete(self):
        import database
        with self.app.test_request_context():
            session = database.get_session()
            session.save_person(database.PersonRow(hello="world"))
            session.commit()

        with self.app.test_request_context():
            session = database.get_session()
            session.del_person(1)
            session.commit()

        with self.app.test_request_context():
            cursor = database.get_session().conn.cursor()
            cursor.execute("SELECT * FROM person")
            self.assertEqual(list(cursor), [])

    def test_large_file(self):
        import database
        with self.app.test_request_context():
            session = database.get_session()
            db_file = session.get_db_file()
            db_file.save_from(StringIO("hello large data"))
            session.commit()
            db_file_id = db_file.id

        with self.app.test_request_context():
            session = database.get_session()
            db_file = session.get_db_file(db_file_id)
            data = ''.join(db_file.iter_data())
            self.assertEqual(data, "hello large data")

    def test_large_file_error(self):
        import database
        import psycopg2
        with self.app.test_request_context():
            db_file = database.get_session().get_db_file(13)
            with self.assertRaises(psycopg2.OperationalError):
                data = ''.join(db_file.iter_data())

        with self.app.test_request_context():
            db_file = database.get_session().get_db_file(13)
            with self.assertRaises(psycopg2.OperationalError):
                db_file.save_from(StringIO("bla bla"))

    def test_remove_large_file(self):
        import database
        with self.app.test_request_context():
            session = database.get_session()
            db_file = session.get_db_file()
            db_file.save_from(StringIO("hello large data"))
            session.commit()
            db_file_id = db_file.id

        with self.app.test_request_context():
            session = database.get_session()
            session.del_db_file(db_file_id)
            session.commit()

        with self.app.test_request_context():
            cursor = database.get_session().conn.cursor()
            cursor.execute("SELECT DISTINCT loid FROM pg_largeobject")
            self.assertEqual(list(cursor), [])
