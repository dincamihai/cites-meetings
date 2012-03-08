from functools import wraps
import re

import flask
import flatland
import flatland.out.markup

def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = flask.request.endpoint \
                    .replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return flask.render_template(template_name, **ctx)
        decorated_function.no_templated = f
        return decorated_function
    return decorator



def jsonify(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        return flask.Response(flask.json.dumps(view(*args, **kwargs)),
                              mimetype='application/json')
    return wrapper


from xhtml2pdf import pisa
from cStringIO import StringIO
def generate_pdf_from_html(html):
    result = StringIO()
    pdf = pisa.CreatePDF(html, result)
    assert pdf.err == 0, "Error generating pdf."
    return result.getvalue()


def auth_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "ACCOUNTS" not in flask.current_app.config:
            pass
        elif flask.session.get("logged_in_email", None) is None:
            login_url = flask.url_for("auth.login", next=flask.flask.request.url)
            return flask.redirect(login_url)
        return view(*args, **kwargs)
    return wrapper


class MarkupGenerator(flatland.out.markup.Generator):

    def __init__(self, template):
        super(MarkupGenerator, self).__init__("html")
        self.template = template

    def children_order(self, field):
        if isinstance(field, flatland.Mapping):
            return [kid.name for kid in field.field_schema]
        else:
            return []

    def widget(self, element, widget_name=None):
        if widget_name is None:
            widget_name = element.properties.get("widget", "input")
        widget_macro = getattr(self.template.module, widget_name)
        return widget_macro(self, element)

    def properties(self, field, id=None):
        properties = {}

        if id:
            properties["id"] = id
        if field.properties.get("css_class", None):
            properties["class"] = field.properties["css_class"]
        if not field.optional:
            properties["required"] = ""
        if field.properties.get("attr", None):
            properties.update(field.properties["attr"])

        return properties
