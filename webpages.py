from functools import wraps
import logging
import flask
import flatland.out.markup
import schema
import database

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

webpages = flask.Blueprint("webpages", __name__)


def auth_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if flask.session.get("logged_in_email", None) is None:
            login_url = flask.url_for("webpages.login", next=flask.request.url)
            return flask.redirect(login_url)
        return view(*args, **kwargs)

    return wrapper


def initialize_app(app):
    app.register_blueprint(webpages)
    app.config.setdefault("ACCOUNTS", [])


@webpages.route("/login", methods=["GET", "POST"])
def login():
    login_email = flask.request.form.get("email", "")
    login_password = flask.request.form.get("password", "")
    next_url = flask.request.values.get("next", flask.url_for("webpages.home"))

    if flask.request.method == "POST":
        app = flask.current_app
        for email, password in app.config["ACCOUNTS"]:
            if login_email == email and login_password == password:
                log.info("Authentication by %r", login_email)
                flask.session["logged_in_email"] = login_email
                return flask.redirect(next_url)
        else:
            flask.flash(u"Login failed", "error")

    return flask.render_template("login.html", **{
        "email": login_email,
        "next": next_url,
    })

@webpages.route("/logout")
def logout():
    next_url = flask.request.values.get("next", flask.url_for("webpages.home"))
    if "logged_in_email" in flask.session:
        del flask.session["logged_in_email"]
    return flask.redirect(next_url)


@webpages.route("/")
@auth_required
def home():
    return flask.render_template("home.html", **{
        "people": list(database.get_session().get_all_persons()),
    })


@webpages.route("/view/<int:person_id>", methods=["GET"])
@auth_required
def view(person_id):
    app = flask.current_app

    # get the person
    person = database.get_session().get_person_or_404(person_id)
    # create data for flatland schema
    person_schema = schema.unflatten_with_defaults(schema.Person, person)

    return flask.render_template("view.html", **{
        "mk": MarkupGenerator(app.jinja_env.get_template("widgets_view.html")),
        "person": person,
        "person_schema": person_schema
    })

@webpages.route("/delete/<int:person_id>", methods=["DELETE"])
@auth_required
def delete(person_id):
    app = flask.current_app
    response = {"status": "success"}
    session = database.get_session()
    session.del_person(person_id)
    session.commit()

    return flask.jsonify(**response)

@webpages.route("/view/credentials/<int:person_id>")
def credentials(person_id):
    app = flask.current_app

    # get the person
    person = database.get_session().get_person_or_404(person_id)
    categories = schema._load_json("refdata/categories.json")
    category = [c for c in categories
        if c["id"] == person["personal_category"]][0]

    person._data.update({
        "meeting_description": "Sixty-first meeting of the Standing Committee",
        "meeting_address": "Geneva (Switzerland), 15-19 August 2011"
    })
    # create data for flatland schema
    person_schema = schema.unflatten_with_defaults(schema.Person, person)

    return flask.render_template("credentials.html", **{
        "person": person,
        "person_schema": person_schema,
        "category": category
    })

@webpages.route("/new", methods=["GET", "POST"])
@webpages.route("/edit/<int:person_id>", methods=["GET", "POST"])
@auth_required
def edit(person_id=None):
    app = flask.current_app
    session = database.get_session()

    if person_id is None:
        person_row = None
    else:
        person_row = session.get_person_or_404(person_id)

    if flask.request.method == "POST":
        form_data = dict(schema.Person.from_defaults().flatten())
        form_data.update(flask.request.form.to_dict())
        person = schema.Person.from_flat(form_data)

        if person.validate():
            if person_row is None:
                person_row = database.Person()
            person_row.clear()
            person_row.update(person.flatten())
            session.save_person(person_row)
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
            person = schema.Person.from_flat(person_row)

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
        "people": database.get_session().get_all_persons(),
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
