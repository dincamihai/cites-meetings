#!/usr/bin/env python

import flask
import flaskext.script
import webpages


default_config = {
}


def create_app():
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.update(default_config)
    app.config.from_pyfile('settings.py', silent=True)
    app.register_blueprint(webpages.webpages)
    return app


manager = flaskext.script.Manager(create_app)


if __name__ == '__main__':
    manager.run()
