import flask

from auth import auth_required
import database
import schema
import sugar

meeting = flask.Blueprint("meeting", __name__)


def initialize_app(app):
    app.jinja_env.globals['ref'] = {"category": schema.category}
    app.register_blueprint(meeting)


@meeting.route("/meeting/1")
@auth_required
def home():
    return flask.redirect(flask.url_for("meeting.registration"))


@meeting.route("/meeting/1/registration")
@auth_required
@sugar.templated("meeting/registration.html")
def registration():
    people = [(person_row.id, schema.PersonSchema.from_flat(person_row).value)
              for person_row in database.get_all_persons()]
    return {
        "people": people,
    }


@meeting.route("/meeting/1/settings/phrases")
@auth_required
@sugar.templated("meeting/settings_phrases.html")
def settings_phrases():
    return {
        "phrases": schema._load_json("refdata/phrases.json")
    }


@meeting.route("/meeting/1/settings/fees")
@auth_required
@sugar.templated("meeting/settings_fees.html")
def settings_fees():
    return {
        "fees": schema.fee,
    }


@meeting.route("/meeting/1/settings/categories")
@auth_required
@sugar.templated("meeting/settings_categories.html")
def settings_categories():
    return {
        "categories": schema.category,
    }
