import flask
import schema
import database
import sugar

from jinja2 import Markup

participant = flask.Blueprint("participant", __name__)
MEETING_DESCRIPTION = "Sixty-first meeting of the Standing Committee"
MEETING_ADDRESS = "Geneva (Switzerland), 15-19 August 2011"

def initialize_app(app):
    _my_extensions = app.jinja_options["extensions"] + ["jinja2.ext.do"]
    app.jinja_options = dict(app.jinja_options, extensions=_my_extensions)
    app.register_blueprint(participant)


@participant.route("/")
@sugar.auth_required
@sugar.templated("participant/home.html")
def home():
    pass

@participant.route("/meeting/1/participant/<int:person_id>",
                methods=["GET", "DELETE"])
@sugar.auth_required
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
        "mk": sugar.MarkupGenerator(app.jinja_env.get_template("widgets_view.html")),
        "person_schema": person_schema,
        "person": person,
    }


@participant.route("/meeting/1/participant/<int:person_id>/credentials")
@sugar.auth_required
@sugar.templated("participant/credentials.html")
def credentials(person_id):
    return {
        "meeting_description": "Sixty-first meeting of the Standing Committee",
        "meeting_address": "Geneva (Switzerland), 15-19 August 2011",
        "person": schema.Person.get_or_404(person_id),
    }


@participant.route("/meeting/1/participant/<int:person_id>/badge")
@sugar.auth_required
@sugar.templated("participant/person_badge.html")
def badge(person_id):
    return {
        "meeting_description": Markup("61<sup>st</sup> meeting of the "
                                      "Standing Committee"),
        "meeting_address": "Geneva (Switzerland), 15-19 August 2011",
        "person": schema.Person.get_or_404(person_id),
    }


@participant.route("/meeting/1/participant/new",
                methods=["GET", "POST"])
@participant.route("/meeting/1/participant/<int:person_id>/edit",
                methods=["GET", "POST"])
@sugar.auth_required
def edit(person_id=None):
    app = flask.current_app
    session = database.get_session()

    if person_id is None:
        person_row = None
        template = "participant/person_create.html"
    else:
        person_row = database.get_person_or_404(person_id)
        template = "participant/person_edit.html"

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
        "mk": sugar.MarkupGenerator(app.jinja_env.get_template("widgets_edit.html")),
        "person_schema": person_schema,
        "person_id": person_id,
    })


@participant.route("/refdata/us-states")
@sugar.auth_required
@sugar.jsonify
def get_us_states():
    us_states = schema._load_json("refdata/us.states.json")
    return us_states


@participant.route("/meeting/1/participant/<int:person_id>/edit_photo",
                methods=["GET", "POST"])
@sugar.auth_required
@sugar.templated("participant/photo.html")
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
            url = flask.url_for("participant.view", person_id=person_id)
            return flask.redirect(url)

        else:
            flask.flash("Please select a photo", "error")

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
@sugar.auth_required
@sugar.templated("participant/send_mail.html")
def send_mail(person_id):
    app = flask.current_app
    session = database.get_session()

    person = schema.Person.get_or_404(person_id)
    phrases = {item["id"]: item["name"]  for item in
               schema._load_json("refdata/phrases.json")}

    if flask.request.method == "POST":
        mail = Mail(app)
        # populate schema with data from POST
        mail_schema = schema.MailSchema.from_flat(flask.request.form.to_dict())

        if mail_schema.validate():
            # flatten schema
            mail_data = {}
            mail_data.update(mail_schema.flatten())

            # construct recipients from "to" and "cc"
            recipients = [mail_data["to"]]
            if mail_data["cc"]:
                recipients.append(mail_data["cc"])

            # recipients = ["dragos.catarahia@gmail.com"]

            # send email
            msg = Message(mail_data["subject"], sender="meeting@cites.edw.ro",
                          recipients=recipients, body=mail_data["message"])

            pdf = sugar.generate_pdf_from_html(
                flask.render_template("participant/credentials.html", **{
                    "person": schema.Person.get_or_404(person_id),
                    "meeting_description": MEETING_DESCRIPTION,
                    "meeting_address": MEETING_ADDRESS,
                })
            )
            msg.attach("credentials.pdf", "application/pdf", pdf)

            if app.config["SEND_REAL_EMAILS"]:
                mail.send(msg)

                # flash a success message
                success_msg = u"Mail sent to %s" % mail_data["to"]
                if mail_data["cc"]:
                    success_msg += u" and to %s" % mail_data["cc"]
                flask.flash(success_msg, "success")

            else:
                flask.flash(u"This is a demo, no real email was sent", "info")

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
        "mk": sugar.MarkupGenerator(app.jinja_env.get_template("widgets_mail.html")),
        "person": person,
        "mail_schema": mail_schema,
    }


@participant.route("/meeting/1/participant/<int:person_id>/credentials.pdf",
                methods=["GET", "POST"])
@sugar.auth_required
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


