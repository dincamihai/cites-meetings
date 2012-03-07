import flask
import sugar

import database
import schema

meeting = flask.Blueprint("meeting", __name__)

MEETING_DESCRIPTION = "Sixty-first meeting of the Standing Committee"
MEETING_ADDRESS = "Geneva (Switzerland), 15-19 August 2011"

def initialize_app(app):
    app.register_blueprint(meeting)


@meeting.route("/meeting/1")
@sugar.auth_required
def meeting_home():
    return flask.redirect(flask.url_for('webpages.meeting_registration'))


@meeting.route("/meeting/1/registration")
@sugar.auth_required
def meeting_registration():
    people = [(person_row.id, schema.PersonSchema.from_flat(person_row).value)
              for person_row in database.get_all_persons()]
    return flask.render_template("meeting/meeting_registration.html", **{
        "people": people,
    })


@meeting.route("/meeting/1/printouts")
@sugar.auth_required
def meeting_printouts():
    return flask.render_template("meeting/meeting_printouts.html")


@meeting.route("/meeting/1/printouts/verified/short_list")
@sugar.auth_required
def meeting_verified_short_list():
    registered = collections.defaultdict(list)

    for person_row in database.get_all_persons():
        if person_row["meeting_flags_verified"]:
            category = schema.category[person_row["personal_category"]]
            if category["registered"]:
                person = schema.Person.from_flat(person_row)
                registered[person_row['personal_category']].append(person)

    meeting = {
        "description": "Sixty-first meeting of the Standing Committee",
        "address": "Geneva (Switzerland), 15-19 August 2011"
    }

    return flask.render_template("meeting/print_short_list_verified.html", **{
        "registered": registered,
        "registered_total": sum(len(cat) for cat in registered.values()),
        "meeting": meeting
    })


@meeting.route("/meeting/1/printouts/verified/meeting_room")
@sugar.auth_required
@sugar.templated("print_meeting_room_verified.html")
def meeting_verified_meeting_room():
    # get all room and sort them by room_sort
    # rooms => [(1, 'Members'), (3, 'Alternate members & Observers, Party')]
    rooms = [(c["room_sort"], c["room"]) for c in schema.category.values()
             if c["room_sort"] > 0]
    rooms = sorted(rooms)

    # dictionary with ordered items => OrderedDict([(u'Members', {'data': [], 'id': 1}),])
    participants_in_rooms = collections.OrderedDict()
    for room in rooms:
        participants_in_rooms[room[1]] = {
            "id": room[0],
            "count": 0,
            "data": collections.defaultdict(list),
        }

    for person_row in database.get_all_persons():
        category = schema.category[person_row["personal_category"]]
        if (not person_row["meeting_flags_verified"] and
            not category["registered"]):
            continue
        person = schema.Person.from_flat(person_row)
        if person.room_list:
            participants_in_rooms[category["room"]]["data"][person.room_list] \
                .append(person)
            participants_in_rooms[category["room"]]["count"] += 1

    meeting = {
        "description": "Sixty-first meeting of the Standing Committee",
        "address": "Geneva (Switzerland), 15-19 August 2011"
    }

    return {
        "meeting": meeting,
        "participants_in_rooms": participants_in_rooms,
    }


@meeting.route("/meeting/1/settings/phrases")
@sugar.auth_required
def meeting_settings_phrases():
    phrases = schema._load_json("refdata/phrases.json")
    return flask.render_template("meeting/meeting_settings_phrases.html", **{
        "phrases": phrases
    })


@meeting.route("/meeting/1/settings/fees")
@sugar.auth_required
def meeting_settings_fees():
    return flask.render_template("meeting/meeting_settings_fees.html", **{
        "fees": schema.fee,
    })


@meeting.route("/meeting/1/settings/categories")
@sugar.auth_required
def meeting_settings_categories():
    return flask.render_template("meeting/meeting_settings_categories.html", **{
        "categories": schema.category,
    })


@meeting.route("/meeting/1/participant/<int:person_id>/send_mail",
                methods=["GET", "POST"])
@sugar.auth_required
def meeting_send_mail(person_id):
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

            pdf = generate_pdf_from_html(
                flask.render_template("meeting/credentials.html", **{
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

    return flask.render_template("meeting/meeting_send_mail.html", **{
        "mk": sugar.MarkupGenerator(app.jinja_env.get_template("widgets_mail.html")),
        "person": person,
        "mail_schema": mail_schema,
    })


@meeting.route("/meeting/1/participant/<int:person_id>/credentials.pdf",
                methods=["GET", "POST"])
@sugar.auth_required
def meeting_view_pdf(person_id):
    app = flask.current_app
    pdf = generate_pdf_from_html(
        flask.render_template("meeting/credentials.html", **{
            "person": schema.Person.get_or_404(person_id),
            "meeting_description": MEETING_DESCRIPTION,
            "meeting_address": MEETING_ADDRESS,
        })
    )
    return flask.Response(response=pdf, mimetype="application/pdf")
