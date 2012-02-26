import unittest
import flask


_testing_db_uri = None
def _get_testing_db_uri():
    global _testing_db_uri
    from app import create_app
    if _testing_db_uri is None:
        tmp_app = create_app()
        _testing_db_uri = tmp_app.config['TESTING_DATABASE_URI']
    return _testing_db_uri


def _create_testing_app():
    from app import create_app
    import database

    app = create_app()
    app.config['DATABASE_URI'] = _get_testing_db_uri()
    database.initialize_app(app)
    with app.test_request_context():
        database.create_all()

    def app_teardown():
        with app.test_request_context():
            database.drop_all()

    return app, app_teardown


class PersonModelTest(unittest.TestCase):

    def setUp(self):
        self.app, app_teardown = _create_testing_app()
        self.addCleanup(app_teardown)
        self.client = self.app.test_client()

    def test_save(self):
        import database
        with self.app.test_request_context():
            database.save_person(database.Person(hello="world"))
            database.commit()

        with self.app.test_request_context():
            cursor = database.get_cursor()
            cursor.execute("SELECT * FROM person")
            [row] = list(cursor)
            self.assertEqual(row[1], {u"hello": u"world"})

    def test_autoincrement_id(self):
        import database
        with self.app.test_request_context():
            p1 = database.Person()
            p2 = database.Person()
            database.save_person(p1)
            database.save_person(p2)
            database.commit()
            self.assertEqual(p1.id, 1)
            self.assertEqual(p2.id, 2)

        with self.app.test_request_context():
            cursor = database.get_cursor()
            cursor.execute("SELECT * FROM person")
            [row1, row2] = list(cursor)
            self.assertEqual(row1[0], 1)
            self.assertEqual(row2[0], 2)

    def test_load(self):
        import database
        with self.app.test_request_context():
            database.save_person(database.Person(hello="world"))
            database.commit()

        with self.app.test_request_context():
            person = database.get_person(1)
            self.assertEqual(person, {"hello": "world"})

    def test_load_not_found(self):
        import database
        with self.app.test_request_context():
            with self.assertRaises(KeyError) as e:
                database.get_person(13)

    def test_load_all(self):
        import database
        with self.app.test_request_context():
            database.save_person(database.Person(hello="world"))
            database.save_person(database.Person(x="y"))
            database.commit()

        with self.app.test_request_context():
            all_persons = list(database.get_all_persons())
            self.assertEqual(len(all_persons), 2)
            self.assertEqual(all_persons[0], {'hello': "world"})
            self.assertEqual(all_persons[0].id, 1)
            self.assertEqual(all_persons[1], {'x': "y"})
            self.assertEqual(all_persons[1].id, 2)

    def test_update(self):
        import database
        with self.app.test_request_context():
            database.save_person(database.Person(k1="v1", k2="v2", k3="v3"))
            database.commit()

        with self.app.test_request_context():
            person = database.get_person(1)
            del person["k1"] # remove value
            person["k2"] = "vX" # change value
            # person["k3"] unchanged
            person["k4"] = "v4" # add value
            database.save_person(person)
            database.commit()

        with self.app.test_request_context():
            person = database.get_person(1)
            self.assertEqual(person, {"k2": "vX", "k3": "v3", "k4": "v4"})

    def test_delete(self):
        import database
        with self.app.test_request_context():
            database.save_person(database.Person(hello="world"))
            database.commit()

        with self.app.test_request_context():
            database.del_person(1)
            database.commit()

        with self.app.test_request_context():
            cursor = database.get_cursor()
            cursor.execute("SELECT * FROM person")
            self.assertEqual(list(cursor), [])
