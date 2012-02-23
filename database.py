from flaskext.sqlalchemy import SQLAlchemy
from flask import json

adb = SQLAlchemy()


class Person(adb.Model):
    id = adb.Column(adb.Integer, primary_key=True)
    data = adb.Column(adb.Text)

    @property
    def data_json(self):
        self._data = getattr(self, "_data", None)
        if self._data is None:
            self._data = json.loads(self.data)
        return self._data
