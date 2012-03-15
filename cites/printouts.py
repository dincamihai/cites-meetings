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
def short_list():
    registered = defaultdict(list)

    for person_row in database.get_all_persons():
        if person_row["meeting_flags_verified"]:
            p = schema.Person.from_flat(person_row)
            if p.category["registered"]:
                registered[p.category["id"]].append(p)

    meeting = {
        "description": "Sixty-first meeting of the Standing Committee",
        "address": "Geneva (Switzerland), 15-19 August 2011"
    }

    page_info = {
        "title": "Print list of registered participants (verified)",
        "url": "printouts.short_list",
    }

    return {
        "page_info": page_info,
        "registered": registered,
        "registered_total": sum(len(cat) for cat in registered.values()),
        "meeting": meeting
    }


@printouts.route("/meeting/1/printouts/verified/meeting_room")
@auth_required
@sugar.templated("printouts/print_meeting_room_verified.html")
def meeting_room():
    rooms = _sorted_rooms()
    participants = _participants_blueprint(rooms)

    for p in _person_row_for_printouts(type="verified"):
        if p.room_list:
            room = participants[p.category["room"]]
            room["data"][p.room_list] = (room["data"][p.room_list] or 0) + 1
            room["count"] += 1

    meeting = {
        "description": "Sixty-first meeting of the Standing Committee",
        "address": "Geneva (Switzerland), 15-19 August 2011"
    }

    page_info = {
        "title": "Print list of delegations (to prepare the meeting room)",
        "url": "printouts.meeting_room",
    }

    return {
        "page_info": page_info,
        "meeting": meeting,
        "participants": participants,
    }


@printouts.route("/meeting/1/printouts/verified/pigeon_holes",
                 defaults={"type": "verified"})
@printouts.route("/meeting/1/printouts/attended/pigeon_holes",
                 defaults={"type": "attended"})
@auth_required
@sugar.templated("printouts/print_pigeon_holes.html")
def pigeon_holes(type):
    rooms = _sorted_rooms()
    participants = _participants_blueprint(rooms)
    for p in _person_row_for_printouts(type):
        if p.room_list:
            room =  participants[p.category["room"]]
            room["data"][p.room_list] = (room["data"][p.room_list] or 0) + 1
            room["count"] += 1

    page_info = {
        "title": "Print list for pigeon holes (%s)" % type,
        "url": "printouts.pigeon_holes",
        "type": type,
    }

    return {
        "page_info": page_info,
        "participants": participants,
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

    for p in _person_row_for_printouts(type):
        if p.ref_list and p.language:
            room =  participants[p.language][p.category["room"]]
            # count participants for rep_list
            room["data"][p.ref_list] = (room["data"][p.ref_list] or 0) + 1
            room["count"] += 1

    page_info = {
        "title": "Distribution of documents",
        "url": "printouts.document_distribution",
        "type": type,
    }

    return {
        "page_info": page_info,
        "meeting": MEETING,
        "participants": participants,
    }


@printouts.route("/meeting/1/printouts/attended/list_for_verification")
@auth_required
@sugar.templated("printouts/print_list_for_verification.html")
def list_for_verification():
    participants = []
    for p in _person_row_for_printouts(type="attended"):
        # we need to group by verifpart in template
        p["verifpart"] = p.verifpart
        participants.append(p)

    participants = sorted(participants, key=lambda k: k["personal"]["last_name"])

    page_info = {
        "title": "List of participants for checking",
        "url": "printouts.list_for_verification",
    }

    return {
        "page_info": page_info,
        "participants": participants,
    }


def _person_row_for_printouts(type):
    for person_row in database.get_all_persons():
        p = schema.Person.from_flat(person_row)
        c = p.category
        if not person_row["meeting_flags_%s" % type] or not c["registered"]:
           continue
        yield p

def _sorted_rooms():
    """
    returns::
        [(1, 'Members'), (3, 'Alternate members & Observers, Party')]
    """
    return [c["room"] for c in sorted(schema.category.values(),
                                      key=lambda k: k["room_sort"])
            if c["room_sort"] > 0]


def _participants_blueprint(rooms):
    """
    returns::
        {Members": {"id": 1, "count": 0, "data": []}}
    """
    return OrderedDict([
        (r, {"count": 0, "data": defaultdict(list)}) for r in rooms
    ])


