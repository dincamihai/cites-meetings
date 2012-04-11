import flask
from jinja2 import Markup
from flaskext.mail import Mail, Message

from auth import auth_required
import schema
import database
import sugar

participant = flask.Blueprint("participant", __name__)
MEETING_DESCRIPTION = "Sixty-first meeting of the Standing Committee"
MEETING_ADDRESS = "Geneva (Switzerland), 15-19 August 2011"

def initialize_app(app):
    _my_extensions = app.jinja_options["extensions"] + ["jinja2.ext.do"]
    app.jinja_options = dict(app.jinja_options, extensions=_my_extensions)
    app.register_blueprint(participant)


@participant.route("/participant/home")
@auth_required
@sugar.templated("participant/home.html")
def home():
    pass

@participant.route("/meeting/1/participant/<int:person_id>",
                methods=["GET", "DELETE"])
@auth_required
@sugar.templated("participant/view.html")
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

    return {
        "mk": sugar.MarkupGenerator(
            app.jinja_env.get_template("widgets/widgets_view.html")
        ),
        "person_schema": person_schema,
        "person": person,
    }


@participant.route("/meeting/1/participant/<int:person_id>/credentials")
@auth_required
@sugar.templated("participant/credentials.html")
def credentials(person_id):
    return {
        "meeting_description": "Sixty-first meeting of the Standing Committee",
        "meeting_address": "Geneva (Switzerland), 15-19 August 2011",
        "person": schema.Person.get_or_404(person_id),
    }


@participant.route("/meeting/1/participant/<int:person_id>/badge")
@auth_required
@sugar.templated("participant/person_badge.html")
def badge(person_id):
    return {
        "meeting_description": Markup("61<sup>st</sup> meeting of the "
                                      "Standing Committee"),
        "meeting_address": "Geneva (Switzerland), 15-19 August 2011",
        "person": schema.Person.get_or_404(person_id),
    }

@participant.route("/meeting/1/participant/<int:person_id>/label")
@auth_required
@sugar.templated("participant/person_label.html")
def label(person_id):
    return {
        "person": schema.Person.get_or_404(person_id),
    }


@participant.route("/meeting/1/participant/<int:person_id>/envelope")
@auth_required
@sugar.templated("participant/print_envelope.html")
def envelope(person_id):
    return {
        "secretariat": schema.secretariat,
        "person": schema.Person.get_or_404(person_id),
    }


@participant.route("/meeting/1/participant/new",
                   methods=["GET", "POST"])
@participant.route("/meeting/1/participant/<int:person_id>/edit",
                   methods=["GET", "POST"])
@auth_required
def edit(person_id=None):
    app = flask.current_app
    session = database.get_session()

    if person_id is None:
        person_row = None
        template = "participant/create.html"
    else:
        person_row = database.get_person_or_404(person_id)
        template = "participant/edit.html"

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
            view_url = flask.url_for("participant.view", person_id=person_row.id)
            return flask.redirect(view_url)

        else:
            flask.flash(u"Errors in person information", "error")

    else:
        if person_row is None:
            person_schema = schema.PersonSchema()
        else:
            person_schema = schema.PersonSchema.from_flat(person_row)

    return flask.render_template(template, **{
        "mk": sugar.MarkupGenerator(
            app.jinja_env.get_template("widgets/widgets_edit.html")
        ),
        "person_schema": person_schema,
        "person_id": person_id,
    })


@participant.route("/refdata/us-states")
@auth_required
def get_us_states():
    us_states = schema._load_json("refdata/us.states.json")
    return flask.Response(response=flask.json.dumps(us_states),
                          mimetype="application/json")


@participant.route("/meeting/1/participant/<int:person_id>/edit_photo",
                methods=["GET", "POST"])
@auth_required
@sugar.templated("participant/photo.html")
def edit_photo(person_id):
    if flask.request.method == "POST":
        photo_file = flask.request.files["photo"]
        is_ajax = flask.request.form.get("is_ajax", None)
        response = {"status": "error"}

        if photo_file.filename != u'':
            session = database.get_session()

            db_file = session.get_db_file()
            db_file.save_from(photo_file)

            person_row = database.get_person_or_404(person_id)
            person_row["photo_id"] = str(db_file.id)
            session.save(person_row)

            session.commit()

            url = flask.url_for("participant.view", person_id=person_id)

            response["status"] = "success"
            response["url"] = flask.url_for("participant.photo", person_id=person_id)

            if not is_ajax:
                flask.flash("New photo saved", "success")
                return flask.redirect(url)
        else:
            response["error"] = "Please select a photo"
            if not is_ajax:
                flask.flash(response["error"], "error")

        if is_ajax:
            return flask.json.dumps(response)

    return {
        "person": schema.Person.get_or_404(person_id),
    }


@participant.route("/meeting/1/participant/<int:person_id>/photo")
def photo(person_id):
    session = database.get_session()
    person_row = database.get_person_or_404(person_id)
    try:
        db_file = session.get_db_file(int(person_row["photo_id"]))
    except KeyError:
        flask.abort(404)
    return flask.Response(''.join(db_file.iter_data()), # TODO stream response
                          mimetype="application/octet-stream")


@participant.route("/meeting/1/participant/<int:person_id>/send_mail",
                methods=["GET", "POST"])
@auth_required
@sugar.templated("participant/send_mail.html")
def send_mail(person_id):
    app = flask.current_app
    session = database.get_session()

    person = schema.Person.get_or_404(person_id)
    phrases = {item["id"]: item["name"]  for item in
               schema._load_json("../refdata/phrases.json")}

    if flask.request.method == "POST":
        mail = Mail(app)
        # populate schema with data from POST
        mail_schema = schema.MailSchema.from_flat(flask.request.form.to_dict())

        if mail_schema.validate():
            # flatten schema
            mail_data = {}
            mail_data.update(mail_schema.flatten())

            # construct recipients from "to"
            recipients = [mail_data["to"]]
            # recipients = ["dragos.catarahia@gmail.com"]

            # send email
            msg = Message(mail_data["subject"], sender="meeting@cites.edw.ro",
                          recipients=recipients, cc=[mail_data["cc"]],
                          body=mail_data["message"])

            pdf = sugar.generate_pdf_from_html(
                flask.render_template("participant/credentials.html", **{
                    "person": schema.Person.get_or_404(person_id),
                    "meeting_description": MEETING_DESCRIPTION,
                    "meeting_address": MEETING_ADDRESS,
                })
            )
            msg.attach("credentials.pdf", "application/pdf", pdf)
            mail.send(msg)

            if app.config["MAIL_SUPPRESS_SEND"]:
                flask.flash(u"This is a demo, no real email was sent", "info")
            else:
                # flash a success message
                success_msg = u"Mail sent to %s" % mail_data["to"]
                if mail_data["cc"]:
                    success_msg += u" and to %s" % mail_data["cc"]
                flask.flash(success_msg, "success")

        else:
            flask.flash(u"Errors in mail information", "error")

    else:
        # create a schema with default data
        mail_schema = schema.MailSchema({
            "to": person["personal"]["email"],
            "subject": phrases["EM_Subj"],
            "message": "\n\n\n%s" % phrases["Intro"],
        })

    return {
        "mk": sugar.MarkupGenerator(
            app.jinja_env.get_template("widgets/widgets_mail.html")
        ),
        "person": person,
        "mail_schema": mail_schema,
    }


@participant.route("/meeting/1/participant/<int:person_id>/credentials.pdf",
                methods=["GET", "POST"])
@auth_required
def view_pdf(person_id):
    app = flask.current_app
    pdf = sugar.generate_pdf_from_html(
        flask.render_template("participant/credentials.html", **{
            "person": schema.Person.get_or_404(person_id),
            "meeting_description": MEETING_DESCRIPTION,
            "meeting_address": MEETING_ADDRESS,
        })
    )
    return flask.Response(response=pdf, mimetype="application/pdf")
