import flask

from auth import auth_required
import database
import schema
import sugar

meeting = flask.Blueprint("meeting", __name__)


def initialize_app(app):
    app.jinja_env.globals['ref'] = {"category": schema.category}
    app.register_blueprint(meeting)


@meeting.route("/")
@auth_required
@sugar.templated("meeting/home.html")
def home():
    meetings = [(m.id, schema.MeetingSchema.from_flat(m).value)
                for m in database.get_all_meetings()]

    return {
        "meetings": meetings,
    }


@meeting.route("/meeting/new",  methods=["GET", "POST"])
@auth_required
@sugar.templated("meeting/new")
def new():
    app = flask.current_app
    session = database.get_session()

    if flask.request.method == "POST":
        form_data = dict(schema.MeetingSchema.from_defaults().flatten())
        form_data.update(flask.request.form.to_dict())

        meeting_schema = schema.MeetingSchema.from_flat(form_data)
        categories = schema.CategoriesSchema(schema.category.values())
        meeting_schema["meeting"]["categories"] = categories

        if meeting_schema.validate():
            meeting_row = database.MeetingRow()
            meeting_row.update(meeting_schema.flatten())

            session.save(meeting_row)
            session.commit()

            flask.flash("Meeting saved", "success")
            return flask.redirect(flask.url_for("meeting.home"))

        else:
            flask.flash(u"Errors in meeting information", "error")
    else:
        meeting_schema = schema.MeetingSchema()

    return flask.render_template("meeting/new.html", **{
        "mk": sugar.MarkupGenerator(
            app.jinja_env.get_template("widgets/widgets_edit.html")
        ),
        "meeting_schema": meeting_schema,
    })


@meeting.route("/meeting/<int:meeting_id>/delete")
@auth_required
def delete(meeting_id):
    session = database.get_session()
    session.table(database.MeetingRow).delete(meeting_id)
    session.commit()
    return flask.jsonify({"status": "success"})


@meeting.route("/meeting/<int:meeting_id>")
@auth_required
def view(meeting_id):
    return flask.redirect(flask.url_for("meeting.registration", meeting_id=meeting_id))


@meeting.route("/meeting/<int:meeting_id>/registration")
@auth_required
@sugar.templated("meeting/registration.html")
def registration(meeting_id):
    meeting_row = database.get_meeting_or_404(meeting_id)
    people = [(person_row.id, schema.PersonSchema.from_flat(person_row).value)
              for person_row in database.get_all_persons()]
    return {
        "people": people,
        "meeting_row": meeting_row,
    }


@meeting.route("/meeting/<int:meeting_id>/settings/phrases")
@auth_required
@sugar.templated("meeting/settings_phrases.html")
def settings_phrases(meeting_id):
    meeting_row = database.get_meeting_or_404(meeting_id)
    return {
        "phrases": schema._load_json("../refdata/phrases.json"),
        "meeting_row": meeting_row,
    }


@meeting.route("/meeting/<int:meeting_id>/settings/fees")
@auth_required
@sugar.templated("meeting/settings_fees.html")
def settings_fees(meeting_id):
    meeting_row = database.get_meeting_or_404(meeting_id)
    return {
        "fees": schema.fee,
        "meeting_row": meeting_row,
    }


@meeting.route("/meeting/<int:meeting_id>/settings/categories")
@auth_required
@sugar.templated("meeting/settings_categories.html")
def settings_categories(meeting_id):
    meeting_row = database.get_meeting_or_404(meeting_id)
    meeting = schema.Meeting.from_flat(meeting_row)["meeting"]

    return {
        "categories": meeting["categories"],
        "meeting_row": meeting_row,
    }
