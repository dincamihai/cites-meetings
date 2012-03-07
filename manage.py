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
