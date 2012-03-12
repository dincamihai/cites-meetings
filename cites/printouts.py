from collections import OrderedDict, defaultdict

import flask

from auth import auth_required
import database
import schema
import sugar

printouts = flask.Blueprint("printouts", __name__)

MEETING = {
        "description": "Sixty-first meeting of the Standing Committee",
        "address": "Geneva (Switzerland), 15-19 August 2011"
}

def initialize_app(app):
    app.register_blueprint(printouts)


@printouts.route("/meeting/1/printouts")
@auth_required
@sugar.templated("printouts/printouts.html")
def home():
    pass


@printouts.route("/meeting/1/printouts/verified/short_list")
@auth_required
@sugar.templated("printouts/print_short_list_verified.html")
def verified_short_list():
    registered = defaultdict(list)

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


@printouts.route("/meeting/1/printouts/verified/meeting_room")
@auth_required
@sugar.templated("printouts/print_meeting_room_verified.html")
def verified_meeting_room():
    # get all room and sort them by room_sort
    # rooms => [(1, 'Members'), (3, 'Alternate members & Observers, Party')]
    rooms = [(c["room_sort"], c["room"]) for c in schema.category.values()
             if c["room_sort"] > 0]
    rooms = sorted(rooms)

    # dictionary with ordered items => OrderedDict([(u'Members', {'data': [], 'id': 1}),])
    participants_in_rooms = OrderedDict()
    for room in rooms:
        participants_in_rooms[room[1]] = {
            "id": room[0],
            "count": 0,
            "data": defaultdict(list),
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



@printouts.route("/meeting/1/printouts/verified/pigeon_holes")
@auth_required
@sugar.templated("printouts/print_pigeon_holes.html")
def verified_pigeon_holes():
    # get all room and sort them by room_sort
    # rooms => [(1, 'Members'), (3, 'Alternate members & Observers, Party')]
    rooms = [(c["room_sort"], c["room"]) for c in schema.category.values()
             if c["room_sort"] > 0]
    rooms = sorted(rooms)

    # dictionary with ordered items => OrderedDict([(u'Members', {'data': [], 'id': 1}),])
    participants_in_rooms = OrderedDict()
    for room in rooms:
        participants_in_rooms[room[1]] = {
            "id": room[0],
            "count": 0,
            "data": defaultdict(list),
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

    page_info = {
        "title": "Print list for pigeon holes (verified)",
        "url": "printouts.verified_pigeon_holes"
    }

    return {
        "page_info": page_info,
        "participants_in_rooms": participants_in_rooms,
    }

@printouts.route("/meeting/1/printouts/attended/pigeon_holes")
@auth_required
@sugar.templated("printouts/print_pigeon_holes.html")
def attended_pigeon_holes():
    # get all room and sort them by room_sort
    # rooms => [(1, 'Members'), (3, 'Alternate members & Observers, Party')]
    rooms = [(c["room_sort"], c["room"]) for c in schema.category.values()
             if c["room_sort"] > 0]
    rooms = sorted(rooms)

    # dictionary with ordered items => OrderedDict([(u'Members', {'data': [], 'id': 1}),])
    participants_in_rooms = OrderedDict()
    for room in rooms:
        participants_in_rooms[room[1]] = {
            "id": room[0],
            "count": 0,
            "data": defaultdict(list),
        }

    for person_row in database.get_all_persons():
        category = schema.category[person_row["personal_category"]]
        if (not person_row["meeting_flags_attended"] and
            not category["registered"]):
            continue

        person = schema.Person.from_flat(person_row)
        if person.room_list:
            participants_in_rooms[category["room"]]["data"][person.room_list] \
                .append(person)
            participants_in_rooms[category["room"]]["count"] += 1

    page_info = {
        "title": "Print list for pigeon holes (attended)",
        "url": "printouts.attended_pigeon_holes"
    }

    return {
        "page_info": page_info,
        "participants_in_rooms": participants_in_rooms,
    }


@printouts.route("/meeting/1/printouts/verified/document_distribution",
                defaults={"type": "verified"})
@printouts.route("/meeting/1/printouts/attended/document_distribution",
                defaults={"type": "attended"})
@auth_required
@sugar.templated("printouts/print_document_distribution.html")
def document_distribution(type):
    rooms = _sorted_rooms()
    participants = OrderedDict([
        (l, _participants_blueprint(rooms)) for l in schema.language.values()
    ])

    for person_row in database.get_all_persons():
        c =  schema.category[person_row["personal_category"]]
        if not person_row["meeting_flags_%s" % type] or not c["registered"]:
           continue

        p = schema.Person.from_flat(person_row)
        if p.ref_list and p.language:
            room =  participants[p.language][c["room"]]
            # count participants for rep_list
            room["data"][p.ref_list] = (room["data"][p.ref_list] or 0) + 1
            room["count"] += 1

    return {
        "meeting": MEETING,
        "participants": participants,
    }


@printouts.route("/meeting/1/printouts/attended/document_distribution")
@auth_required
@sugar.templated("printouts/print_list_for_verification.html")
def list_for_verification():

    # participants = defaultdict(list)
    participants = []
    for person_row in database.get_all_persons():
        c = schema.category[person_row["personal_category"]]
        if not person_row["meeting_flags_attended"] or not c["registered"]:
           continue

        p = schema.Person.from_flat(person_row)
        p["verifpart"] = p.verifpart
        participants.append(p)

    participants = sorted(participants, key=lambda k: k["personal"]["last_name"])

    return {
        "participants": participants
    }


# rooms => [(1, 'Members'), (3, 'Alternate members & Observers, Party')]
def _sorted_rooms():
    rooms = [(c["room_sort"], c["room"]) for c in schema.category.values()
             if c["room_sort"] > 0]
    return sorted(rooms)


# participants => {Members": {"id": 1, "count": 0, "data": []}}
def _participants_blueprint(rooms):
    return OrderedDict([
        (r[1], {"count": 0, "data": defaultdict(list)}) for r in rooms
    ])


