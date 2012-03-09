#!/usr/bin/env python

import os.path
import flask

import database
import auth
import meeting
import participant
import printouts

default_config = {
    "DATABASE_URI": "postgresql://localhost/cites",
    "TESTING_DATABASE_URI": "postgresql://localhost/cites_test",
    "SEND_REAL_EMAILS": False,
}


def create_app(instance_path=None):
    app = flask.Flask(__name__,
                      instance_path=instance_path,
                      instance_relative_config=True)
    app.config.update(default_config)
    app.config.from_pyfile("settings.py", silent=True)
    database.initialize_app(app)
    auth.initialize_app(app)
    participant.initialize_app(app)
    meeting.initialize_app(app)
    printouts.initialize_app(app)
    return app

