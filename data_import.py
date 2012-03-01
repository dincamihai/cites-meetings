from flask import json
import schema
import database
import logging
import csv
import re

log = logging.getLogger("data-import")
log.setLevel(logging.INFO)

PERSON = [
    "id",
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
    "meeting_flags_web_alert",
    "sc_fin",
    "representing_region",
    "meeting_flags_sponsored",
    "meeting_flags_credentials",
    "meeting_flags_approval",
    "meeting_flags_invitation",
    "personal_fee",
    "meeting_flags_acknowledge",
    "meeting_flags_verified",
    "meeting_flags_attended",
    "representing_organization_show",
    "more_info_text",
    "updated",
    "pic_path",
]
def person_to_json(file):
    out = get_csv(file, fieldnames=PERSON)
    for i in out:
        i["personal_email"] = re.sub(r"\s*@\s*", "@", i["personal_email"])
        i["meeting_flags_web_alert"] = bool(i["meeting_flags_web_alert"])
        i["meeting_flags_sponsored"] = bool(i["meeting_flags_sponsored"])
        i["meeting_flags_credentials"] = bool(i["meeting_flags_credentials"])
        i["meeting_flags_approval"] = bool(i["meeting_flags_approval"])
        i["meeting_flags_invitation"] = bool(i["meeting_flags_invitation"])
        i["meeting_flags_attended"] = bool(i["meeting_flags_attended"])
        i["meeting_flags_verified"] = bool(i["meeting_flags_verified"])
        i["representing_organization_show"] = bool(i["representing_organization_show"])
    print json.dumps(out, indent=2)

CATEGORY = (
    "id",
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
    "invitation_received",
    "registered",
)
def category_to_json(file):
    out = get_csv(file, fieldnames=CATEGORY)
    for i in out:
        i["stat_sort"] = int(i["stat_sort"])
        i["reg_sort"] = int(i["reg_sort"])
        i["room_sort"] = int(i["room_sort"])
        i["credent"] = int(i["credent"])
        i["fee"] = bool(i["fee"])
        i["registered"] = bool(i["registered"])
    print json.dumps(out, indent=2)

FEE = (
    "id",
    "name",
)
def fee_to_json(file):
    out = get_csv(file, fieldnames=FEE)
    print json.dumps(out, indent=2)

REGION = (
    "id",
    "name_en_sp_fr",
    "name",
)
def region_to_json(file):
    out = get_csv(file, fieldnames=REGION)
    print json.dumps(out, indent=2)

COUNTRY = (
    "id",
    "name",
)
def country_to_json(file):
    out = get_csv(file, fieldnames=COUNTRY)
    print json.dumps(out, indent=2)

DISPATCH = {
    "person": person_to_json,
    "fee": fee_to_json,
    "region": region_to_json,
    "country": country_to_json,
    "category": category_to_json,
}
def to_json(file, what="person"):
    if what in DISPATCH:
        return DISPATCH[what](file)
    else:
        print "Value for -w not valid"

def get_csv(file, fieldnames):
    with open(file) as f:
        out = csv.DictReader(f, fieldnames=fieldnames, restkey="restkey",
                             restval="restval")
        out = list(out)[1:] # remove column headers
    return out

def data_import(file):
    logging.basicConfig()

    with open(file, "r") as f:
        data = json.loads(f.read())
        session = database.get_session()

        for item in data:
            # NULL objects for country => ""
            if item["personal_country"].strip() == "NULL":
                item["personal_country"] = ""
            if item["representing_country"].strip() == "NULL":
                item["representing_country"] = ""

            person = schema.PersonSchema.from_flat(item)
            if person.validate():
                log.info("Person %r added." %
                         person.find("personal/first_name")[0].value)

                session.save_person(database.PersonRow(person.flatten()))
            else:
               # import pdb; pdb.set_trace()
               log.error("Person is not valid.")
               log.error("%s" % item)
               for element in person.all_children:
                   log.error("%r, %r" % (element.name, element.errors))

        session.commit()

