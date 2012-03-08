import os.path
import flask
import flaskext.script

from cites.data_import import to_json, data_import

def create_app():
    import cites.app
    instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance'))
    return cites.app.create_app(instance_path)

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
