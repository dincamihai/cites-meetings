from functools import wraps
import logging
import collections
import itertools

import flask
import jinja2

import schema
import database

from flask.views import MethodView
from flaskext.mail import Mail, Message

from sugar import templated, generate_pdf_from_html

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

webpages = flask.Blueprint("webpages", __name__)




def initialize_app(app):
    _my_extensions = app.jinja_options["extensions"] + ["jinja2.ext.do"]
    app.jinja_options = dict(app.jinja_options, extensions=_my_extensions)
    app.jinja_env.globals['ref'] = {
        'category': schema.category,
    }

    app.register_blueprint(webpages)


# @webpages.route("/login", methods=["GET", "POST"])
# def login():
#     login_email = flask.request.form.get("email", "")
#     login_password = flask.request.form.get("password", "")
#     next_url = flask.request.values.get("next", flask.url_for("webpages.home"))

#     if flask.request.method == "POST":
#         app = flask.current_app
#         for email, password in app.config.get("ACCOUNTS", []):
#             if login_email == email and login_password == password:
#                 log.info("Authentication by %r", login_email)
#                 flask.session["logged_in_email"] = login_email
#                 return flask.redirect(next_url)
#         else:
#             flask.flash(u"Login failed", "error")

#     return flask.render_template("login.html", **{
#         "email": login_email,
#         "next": next_url,
#     })


# @webpages.route("/logout")
# def logout():
#     next_url = flask.request.values.get("next", flask.url_for("webpages.home"))
#     if "logged_in_email" in flask.session:
#         del flask.session["logged_in_email"]
#     return flask.redirect(next_url)


@webpages.route("/")
@auth_required
def home():
    return flask.render_template("home.html")


@webpages.route("/meeting/1/participant/<int:person_id>",
                methods=["GET", "DELETE"])
@auth_required
def view(person_id):
    app = flask.current_app

    if flask.request.method == "DELETE":
        session = database.get_session()
        session.table(database.PersonRow).delete(person_id)
        session.commit()
        return flask.jsonify({"status": "success"})

    person_row = database.get_person_or_404(person_id)
    person_schema = schema.PersonSchema.from_flat(person_row)
    person = person_schema.value
    person.id = person_id

    return flask.render_template("view.html", **{
        "mk": MarkupGenerator(app.jinja_env.get_template("widgets_view.html")),
        "person_schema": person_schema,
        "person": person,
    })


@webpages.route("/meeting/1/participant/<int:person_id>/credentials")
@auth_required
def credentials(person_id):
    return flask.render_template("credentials.html", **{
        "meeting_description": "Sixty-first meeting of the Standing Committee",
        "meeting_address": "Geneva (Switzerland), 15-19 August 2011",
        "person": schema.Person.get_or_404(person_id),
    })


@webpages.route("/meeting/1/participant/<int:person_id>/badge")
@auth_required
def badge(person_id):
    return flask.render_template("person_badge.html", **{
        "meeting_description": jinja2.Markup("61<sup>st</sup> meeting of the "
                                             "Standing Committee"),
        "meeting_address": "Geneva (Switzerland), 15-19 August 2011",
        "person": schema.Person.get_or_404(person_id),
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
        template = "person_create.html"
    else:
        person_row = database.get_person_or_404(person_id)
        template = "person_edit.html"

    if flask.request.method == "POST":
        form_data = dict(schema.PersonSchema.from_defaults().flatten())
        form_data.update(flask.request.form.to_dict())
        person_schema = schema.PersonSchema.from_flat(form_data)

        if person_schema.validate():
            if person_row is None:
                person_row = database.PersonRow()
            person_row.update(person_schema.flatten())
            session.save(person_row)
            session.commit()
            flask.flash("Person information saved", "success")
            view_url = flask.url_for("webpages.view", person_id=person_row.id)
            return flask.redirect(view_url)

        else:
            flask.flash(u"Errors in person information", "error")

    else:
        if person_row is None:
            person_schema = schema.PersonSchema()
        else:
            person_schema = schema.PersonSchema.from_flat(person_row)

    return flask.render_template(template, **{
        "mk": MarkupGenerator(app.jinja_env.get_template("widgets_edit.html")),
        "person_schema": person_schema,
        "person_id": person_id,
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
    if flask.request.method == "POST":
        photo_file = flask.request.files["photo"]

        if photo_file.filename != u'':
            session = database.get_session()

            db_file = session.get_db_file()
            db_file.save_from(photo_file)

            person_row = database.get_person_or_404(person_id)
            person_row["photo_id"] = str(db_file.id)
            session.save(person_row)

            session.commit()

            flask.flash("New photo saved", "success")
            url = flask.url_for("webpages.view", person_id=person_id)
            return flask.redirect(url)

        else:
            flask.flash("Please select a photo", "error")

    return flask.render_template("photo.html", **{
        "person": schema.Person.get_or_404(person_id),
    })


@webpages.route("/meeting/1/participant/<int:person_id>/photo")
def photo(person_id):
    session = database.get_session()
    person_row = database.get_person_or_404(person_id)
    try:
        db_file = session.get_db_file(int(person_row["photo_id"]))
    except KeyError:
        flask.abort(404)
    return flask.Response(''.join(db_file.iter_data()), # TODO stream response
                          mimetype="application/octet-stream")





