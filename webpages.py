import functools import wraps
import flask
import flatland.out.markup
import schema
import database

webpages = flask.Blueprint("webpages", __name__)


def auth_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if flask.session.get("logged_in_email", None) is None:
            login_url = flask.url_for("webpages.login")
            return flask.redirect(login_url)
        return view(*args, **kwargs)

    return wrapper


def initialize_app(app):
    app.register_blueprint(webpages)



@webpages.route("/login")
def login():
    return flask.render_template("login.html")


@webpages.route("/")
@auth_required
def home():
    return flask.render_template("home.html", **{
        "people": database.Person.query.all(),
    })

@webpages.route("/view/<int:person_id>", methods=["GET"])
@auth_required
def view(person_id):
    app = flask.current_app

    # get the person
    person = database.Person.query.get_or_404(person_id)
    # create data for flatland schema
    schema_data = dict(schema.Person.from_defaults().flatten())
    schema_data.update(person.data_json)
    person_schema = schema.Person.from_flat(schema_data)

    return flask.render_template("view.html", **{
        "mk": MarkupGenerator(app.jinja_env.get_template("widgets_view.html")),
        "person": person,
        "person_schema": person_schema
    })

@webpages.route("/new", methods=["GET", "POST"])
@webpages.route("/edit/<int:person_id>", methods=["GET", "POST"])
@auth_required
def edit(person_id=None):
    app = flask.current_app

    if person_id is None:
        person_row = None
    else:
        person_row = database.Person.query.get_or_404(person_id)

    if flask.request.method == "POST":
        form_data = dict(schema.Person.from_defaults().flatten())
        form_data.update(flask.request.form.to_dict())
        person = schema.Person.from_flat(form_data)

        if person.validate():
            if person_row is None:
                person_row = database.Person()
            session = database.adb.session
            person_row.data = flask.json.dumps(dict(person.flatten()))
            session.add(person_row)
            session.commit()
            flask.flash("Person information saved", "success")
            view_url = flask.url_for("webpages.view", person_id=person_row.id)
            return flask.redirect(view_url)

        else:
            flask.flash(u"Errors in person information", "error")

    else:
        if person_row is None:
            person = schema.Person()
        else:
            person = schema.Person.from_flat(flask.json.loads(person_row.data))

    return flask.render_template("edit.html", **{
        "mk": MarkupGenerator(app.jinja_env.get_template("widgets_edit.html")),
        "person": person,
    })


@webpages.route("/meeting/1")
@auth_required
def meeting():
    return flask.redirect(flask.url_for('webpages.meeting_registration'))


@webpages.route("/meeting/1/registration")
@auth_required
def meeting_registration():
    return flask.render_template("meeting_registration.html", **{
        "people": database.Person.query.all(),
    })


@webpages.route("/meeting/1/printouts")
@auth_required
def meeting_printouts():
    return flask.render_template("meeting_printouts.html")


@webpages.route("/meeting/1/settings/phrases")
@auth_required
def meeting_settings_phrases():
    return flask.render_template("meeting_settings_phrases.html")


@webpages.route("/meeting/1/settings/fees")
@auth_required
def meeting_settings_fees():
    return flask.render_template("meeting_settings_fees.html")


@webpages.route("/meeting/1/settings/categories")
@auth_required
def meeting_settings_categories():
    return flask.render_template("meeting_settings_categories.html")


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
