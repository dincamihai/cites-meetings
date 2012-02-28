from functools import wraps
import logging
import flask
import flatland.out.markup
import schema
import database

from flask.views import MethodView
from flaskext.mail import Mail, Message

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

webpages = flask.Blueprint("webpages", __name__)

def auth_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if 'ACCOUNTS' not in flask.current_app.config:
            pass
        elif flask.session.get("logged_in_email", None) is None:
            login_url = flask.url_for("webpages.login", next=flask.request.url)
            return flask.redirect(login_url)
        return view(*args, **kwargs)

    return wrapper


def initialize_app(app):
    _my_extensions = app.jinja_options['extensions'] + ['jinja2.ext.do']
    app.jinja_options = dict(app.jinja_options, extensions=_my_extensions)
    app.jinja_env.globals['ref'] = {
        'country': schema.country,
    }

    app.register_blueprint(webpages)


@webpages.route("/login", methods=["GET", "POST"])
def login():
    login_email = flask.request.form.get("email", "")
    login_password = flask.request.form.get("password", "")
    next_url = flask.request.values.get("next", flask.url_for("webpages.home"))

    if flask.request.method == "POST":
        app = flask.current_app
        for email, password in app.config.get("ACCOUNTS", []):
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


@webpages.route("/meeting/1/participant/<int:person_id>", methods=["GET"])
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
        "person_schema": person_schema,
        "has_photo": bool(person.get("photo_id", "")),
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

@webpages.route("/meeting/1/participant/<int:person_id>/credentials")
@auth_required
def credentials(person_id):
    app = flask.current_app

    # get the person
    person = database.get_session().get_person_or_404(person_id)
    category = {c["id"]: c for c in
                schema._load_json("refdata/categories.json")}

    person.update({
        "meeting_description": "Sixty-first meeting of the Standing Committee",
        "meeting_address": "Geneva (Switzerland), 15-19 August 2011"
    })
    # create data for flatland schema
    person_schema = schema.unflatten_with_defaults(schema.Person, person)

    return flask.render_template("credentials.html", **{
        "person": person,
        "person_schema": person_schema,
        "category": category,
        "has_photo": bool(person.get("photo_id", "")),
    })

@webpages.route("/meeting/1/participant/<int:person_id>/badge/normal")
@auth_required
def normal_badge(person_id):
    app = flask.current_app

    # get the person
    person = database.get_session().get_person_or_404(person_id)
    categories = schema._load_json("refdata/categories.json")
    category = [c for c in categories
        if c["id"] == person["personal_category"]][0]

    import jinja2
    person.update({
        "meeting_description": jinja2.Markup("61<sup>st</sup> meeting of the Standing Committee"),
        "meeting_address": "Geneva (Switzerland), 15-19 August 2011"
    })
    # create data for flatland schema
    person_schema = schema.unflatten_with_defaults(schema.Person, person)

    return flask.render_template("normal_badge.html", **{
        "person": person,
        "person_schema": person_schema,
        "category": category
    })

@webpages.route("/meeting/1/participant/new",
                methods=["GET", "POST"])
@webpages.route("/meeting/1/participant/<int:person_id>/edit",
                methods=["GET", "POST"])
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


@webpages.route("/refdata/us-states")
@auth_required
def get_us_states():
    us_states = schema._load_json("refdata/us.states.json")
    response = flask.json.dumps(us_states)
    return flask.Response(response=response, mimetype="application/json")


@webpages.route("/meeting/1/participant/<int:person_id>/edit_photo",
                methods=["GET", "POST"])
@auth_required
def edit_photo(person_id):
    session = database.get_session()
    person_row = session.get_person_or_404(person_id)

    if flask.request.method == "POST":
        photo_file = flask.request.files["photo"]
        if photo_file.filename != u'':
            db_file = session.get_db_file()
            db_file.save_from(photo_file)
            person_row["photo_id"] = str(db_file.id)
            session.save_person(person_row)
            session.commit()
            flask.flash("New photo saved", "success")
            url = flask.url_for("webpages.view", person_id=person_id)
            return flask.redirect(url)
        else:
            flask.flash("Please select a photo", "error")

    return flask.render_template("photo.html", **{
        "person": person_row,
        "has_photo": bool(person_row.get("photo_id", "")),
    })


@webpages.route("/meeting/1/participant/<int:person_id>/photo")
def photo(person_id):
    session = database.get_session()
    person_row = session.get_person_or_404(person_id)
    try:
        db_file = session.get_db_file(int(person_row["photo_id"]))
    except KeyError:
        flask.abort(404)
    return flask.Response(''.join(db_file.iter_data()), # TODO stream response
                          mimetype="application/octet-stream")


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


@webpages.route("/meeting/1/printouts/verified/short_list")
@auth_required
def meeting_verified_short_list():
    app = flask.current_app

    registered = []
    for person in database.get_session().get_all_persons():
        if person["meeting_flags_verified"]:
            category = schema.categories_map[person["personal_category"]]
            if category['registered'] == '1':
                registered.append(person)

    meeting = {
        "description": "Sixty-first meeting of the Standing Committee",
        "address": "Geneva (Switzerland), 15-19 August 2011"
        }

    # create data for flatland schema
    person_schema = schema.unflatten_with_defaults(schema.Person, person)

    return flask.render_template("print_short_list_verified.html", **{
        "registered": registered,
        "meeting": meeting
    })


@webpages.route("/meeting/1/settings/phrases")
@auth_required
def meeting_settings_phrases():
    phrases = schema._load_json("refdata/phrases.json")
    return flask.render_template("meeting_settings_phrases.html", **{
        "phrases": phrases
    })


@webpages.route("/meeting/1/settings/fees")
@auth_required
def meeting_settings_fees():
    return flask.render_template("meeting_settings_fees.html", **{
        "fees": schema.fee,
    })

@webpages.route("/meeting/1/settings/categories")
@auth_required
def meeting_settings_categories():
    return flask.render_template("meeting_settings_categories.html", **{
        "categories": schema.category,
    })

@webpages.route("/email/<int:person_id>",  methods=["GET", "POST"])
@auth_required
def send_mail(person_id):
    app = flask.current_app
    session = database.get_session()

    person = session.get_person_or_404(person_id)
    phrases = {item["id"]: item["name"]  for item in
               schema._load_json("refdata/phrases.json")}

    if flask.request.method == "POST":
        mail = Mail(app)
        # populate schema with data from POST
        mail_schema = schema.Mail.from_flat(flask.request.form.to_dict())

        if mail_schema.validate():
            # flatten schema
            mail_data = {}
            mail_data.update(mail_schema.flatten())

            # construct recipients from "to" and "cc"
            recipients = [mail_data["to"]]
            if mail_data["cc"]:
                recipients.append(mail_data["cc"])

            # send email
            msg = Message(mail_data["subject"], sender="meeting@cites.edw.ro",
                          recipients=recipients, body=mail_data["message"])
            mail.send(msg)

            # flash a success message
            success_msg = u"Mail sent to %s" % mail_data["to"]
            if mail_data["cc"]:
                success_msg += u" and to %s" % mail_data["cc"]
            flask.flash(success_msg, "success")

        else:
            flask.flash(u"Errors in mail information", "error")

    else:
        # create a schema with default data
        mail_schema = schema.Mail.from_flat({
            "to": "cornel@eaudeweb.ro",
            "subject": phrases["EM_Subj"],
            "message": phrases["Intro"],
        })

    return flask.render_template("send_mail.html", **{
        "mk": MarkupGenerator(app.jinja_env.get_template("widgets_mail.html")),
        "person": person,
        "mail_schema": mail_schema,
    })

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
