from flaskext.sqlalchemy import SQLAlchemy


adb = SQLAlchemy()


class Person(adb.Model):
    id = adb.Column(adb.Integer, primary_key=True)
    data = adb.Column(adb.Text)
