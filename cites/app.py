#!/usr/bin/env python

import os.path
import flask

import database
import webpages
import auth
import meeting

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
    app.config.from_pyfile("settings.py")
    database.initialize_app(app)
    webpages.initialize_app(app)
    auth.initialize_app(app)
    meeting.initialize_app(app)
    return app


def _production_logging(app):
    import logging
    log_fmt = logging.Formatter("[%(asctime)s] %(module)s "
                                "%(levelname)s %(message)s")

    error_log_path = os.path.join(app.instance_path, 'error.log')
    error_handler = logging.FileHandler(error_log_path)
    error_handler.setFormatter(log_fmt)
    error_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(error_handler)

    info_log_path = os.path.join(app.instance_path, 'info.log')
    info_handler = logging.FileHandler(info_log_path)
    info_handler.setFormatter(log_fmt)
    info_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(info_handler)

