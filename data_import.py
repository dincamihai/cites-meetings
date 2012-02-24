from flask import json
import schema
import database
import logging
import csv
import re

log = logging.getLogger("data-import")
log.setLevel(logging.INFO)

KEYS = {
    "person":  ("id",
                "personal_name_title",
                "personal_first_name",
                "personal_last_name",
                "personal_address",
                "personal_place",
                "personal_country",
                "personal_phone",
                "personal_cellular",
                "personal_fax",
                "personal_email",
                "personal_language",
                "personal_category",
                "representing_country",
                "representing_organization",
                "entered",
                "meeting",
                "info_alert",
                "sc_fin",
                "representing.region",
                "meeting_flags.sponsored",
                "meeting_flags.credentials",
                "meeting_flags.approval",
                "meeting_flags.invitation",
                "personal.fee",
                "meeting_flags.acknowledge",
                "meeting_flags.verified",
                "meeting_flags.attended",
                "representing.organization_show",
                "more_info.text",
                "updated",
                "pic_path"),

    "categories": ("id",
                   "name",
                   "stat",
                   "stat_sort",
                   "reg",
                   "reg_sort",
                   "room",
                   "room_sort",
                   "badge_color",
                   "credent",
                   "fee",
                   "details_of_registration",
                   "representative",
                   "registration_fee",
                   "invitation_received"),

    "regions": ("id",
                "name"),

    "fee": ("id",
            "name"),

    "country": ("id", "name"),
}

# from csv to json
def to_json(file, what="person"):
    with open(file, "r") as f:
        reader = csv.reader(f)
        out = [dict(zip(KEYS[what], property)) for property in reader]
        out.pop(0) # remove csv headers
        # out = out[:1]

        # emails from dragos.catarahia @ eaudeweb.ro =>  dragos.catarahia@eaudeweb.ro
        for i in out:
            if "personal_email" in i:
                i["personal_email"] = re.sub(r"\s*@\s*", "@",
                                             i["personal_email"])

        print json.dumps(out)

def data_import(file):
    logging.basicConfig()

    with open(file, "r") as f:
        data = json.loads(f.read())
        session = database.adb.session

        for item in data:
            # NULL objects for country => ""
            if item["personal_country"].strip() == "NULL":
                item["personal_country"] = ""
            if item["representing_country"].strip() == "NULL":
                item["representing_country"] = ""

            person = schema.Person.from_flat(item)
            if person.validate():
                log.info("Person %r added." %
                         person.find("personal/first_name")[0].value)

                person_row = database.Person()
                person_row.data = json.dumps(dict(person.flatten()))
                session.add(person_row)
            else:
               # import pdb; pdb.set_trace()
               log.error("Person is not valid.")
               log.error("%s" % item)
               for element in person.all_children:
                   log.error("%r, %r" % (element.name, element.errors))

        session.commit()

