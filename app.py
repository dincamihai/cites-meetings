#!/usr/bin/env python

import flask
import flaskext.script
import database
import webpages


default_config = {
    'SQLALCHEMY_DATABASE_URI': 'mysql://cites:cites@localhost/cites',
    'TESTING_SQLALCHEMY_DATABASE_URI': 'mysql://cites:cites@localhost/cites_test',
}


def create_app():
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.update(default_config)
    app.config.from_pyfile('settings.py', silent=True)
    database.adb.init_app(app)
    app.register_blueprint(webpages.webpages)
    return app


manager = flaskext.script.Manager(create_app)


@manager.command
def resetdb():
    database.adb.drop_all()


@manager.command
def syncdb():
    database.adb.create_all()


if __name__ == '__main__':
    manager.run()
