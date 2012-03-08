import collections

import flask
import sugar

import database
import schema

meeting = flask.Blueprint("meeting", __name__)


def initialize_app(app):
    app.jinja_env.globals['ref'] = {"category": schema.category}
    app.register_blueprint(meeting)


@meeting.route("/meeting/1")
@sugar.auth_required
def home():
    return flask.redirect(flask.url_for("meeting.registration"))


@meeting.route("/meeting/1/registration")
@sugar.auth_required
@sugar.templated("meeting/registration.html")
def registration():
    people = [(person_row.id, schema.PersonSchema.from_flat(person_row).value)
              for person_row in database.get_all_persons()]
    return {
        "people": people,
    }


@meeting.route("/meeting/1/printouts")
@sugar.auth_required
@sugar.templated("meeting/printouts.html")
def printouts():
    pass


@meeting.route("/meeting/1/printouts/verified/short_list")
@sugar.auth_required
@sugar.templated("meeting/print_short_list_verified.html")
def verified_short_list():
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

    return {
        "registered": registered,
        "registered_total": sum(len(cat) for cat in registered.values()),
        "meeting": meeting
    }


@meeting.route("/meeting/1/printouts/verified/meeting_room")
@sugar.auth_required
@sugar.templated("meeting/print_meeting_room_verified.html")
def verified_meeting_room():
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
@sugar.templated("meeting/settings_phrases.html")
def settings_phrases():
    return {
        "phrases": schema._load_json("refdata/phrases.json")
    }


@meeting.route("/meeting/1/settings/fees")
@sugar.auth_required
@sugar.templated("meeting/settings_fees.html")
def settings_fees():
    return {
        "fees": schema.fee,
    }


@meeting.route("/meeting/1/settings/categories")
@sugar.auth_required
@sugar.templated("meeting/settings_categories.html")
def settings_categories():
    return {
        "categories": schema.category,
    }
