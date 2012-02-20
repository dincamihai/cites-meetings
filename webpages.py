import flask
import flatland.out.markup
import schema


webpages = flask.Blueprint('webpages', __name__)


@webpages.route('/')
def home():
    return flask.render_template('layout.html', **{
        'content': "Hello world!"
    })


@webpages.route('/edit')
def edit():
    app = flask.current_app
    return flask.render_template('edit.html', **{
        'mk': MarkupGenerator(app.jinja_env.get_template('widgets.html')),
        'person': schema.Person(),
    })


class MarkupGenerator(flatland.out.markup.Generator):

    def __init__(self, template):
        super(MarkupGenerator, self).__init__('html')
        self.template = template

    def children_order(self, field):
        if isinstance(field, flatland.Mapping):
            return [kid.name for kid in field.field_schema]
        else:
            return []

    def widget(self, element, widget_name=None):
        if widget_name is None:
            widget_name = element.properties.get('widget', 'input')
        widget_macro = getattr(self.template.module, widget_name)
        return widget_macro(self, element)
