#!/usr/bin/env python

import os.path
import flask
import flaskext.script
import database
import webpages

from data_import import to_json, data_import

default_config = {
    "DATABASE_URI": "postgresql://localhost/cites",
    "TESTING_DATABASE_URI": "postgresql://localhost/cites_test",
    "MAIL_SERVER": "martini.edw.ro"
}

def create_app():
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.update(default_config)
    app.config.from_pyfile('settings.py', silent=True)
    database.initialize_app(app)
    webpages.initialize_app(app)
    return app

manager = flaskext.script.Manager(create_app)

@manager.command
def resetdb():
    database.get_session().drop_all()

@manager.command
def syncdb():
    database.get_session().create_all()

to_json = manager.command(to_json)
data_import = manager.command(data_import)

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

class FcgiCommand(flaskext.script.Command):

    def handle(self, app):
        _production_logging(app)
        from flup.server.fcgi import WSGIServer
        sock_path = os.path.join(app.instance_path, 'fcgi.sock')
        server = WSGIServer(app, bindAddress=sock_path, umask=0)
        server.run()

manager.add_command('fcgi', FcgiCommand())

if __name__ == '__main__':
    manager.run()
