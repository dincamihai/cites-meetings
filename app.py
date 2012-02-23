#!/usr/bin/env python

import os.path
import flask
import flaskext.script
import database
import webpages

from data_import import to_json, data_import

default_config = {
    'DATABASE_URI': 'postgresql://localhost/cites',
    'TESTING_DATABASE_URI': 'postgresql://localhost/cites_test',
}

def create_app():
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.update(default_config)
    app.config.from_pyfile('settings.py', silent=True)
    database.initialize_app(app)
    app.register_blueprint(webpages.webpages)
    return app

manager = flaskext.script.Manager(create_app)

@manager.command
def resetdb():
    database.drop_all()

@manager.command
def syncdb():
    database.create_all()

to_json = manager.command(to_json)
data_import = manager.command(data_import)

def _error_log(error_log_path):
    import logging
    error_handler = logging.FileHandler(error_log_path)
    log_fmt = logging.Formatter("[%(asctime)s] %(module)s "
                                "%(levelname)s %(message)s")
    error_handler.setFormatter(log_fmt)
    error_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(error_handler)

class FcgiCommand(flaskext.script.Command):

    def handle(self, app):
        _error_log(os.path.join(app.instance_path, 'error.log'))
        from flup.server.fcgi import WSGIServer
        sock_path = os.path.join(app.instance_path, 'fcgi.sock')
        server = WSGIServer(app, bindAddress=sock_path, umask=0)
        server.run()

manager.add_command('fcgi', FcgiCommand())

if __name__ == '__main__':
    manager.run()
