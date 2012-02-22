import schema
import json
import csv
import re

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
                "type.sponsored",
                "type.credentials",
                "type.approval",
                "type.invitation",
                "personal.fee",
                "info.acknowledge",
                "info.verified",
                "info.attended",
                "representing.organization_show",
                "info.more_info",
                "updated",
                "pic_path"),

    "categories": ("id",
                   "name",
                   "stat",
                   "stat_sort",
                   "reg",
                   "room",
                   "room_sort",
                   "badge_color",
                   "credent",
                   "fee"),

    "regions": ("id",
                "name"),

    "country": ("id", "name"),
}

# from csv to json
def to_json(file, what="person"):
    with open(file, "r") as f:
        reader = csv.reader(f)
        keys = KEYS[what]
        out = [dict(zip(keys, property)) for property in reader]
        out.pop(0)
        # out = out[:1]

        # emails from dragos.catarahia @ eaudeweb.ro =>  dragos.catarahia@eaudeweb.ro
        for i in out:
            if "personal_email" in i:
                i["personal_email"] = re.sub(r"\s*@\s*", "@",  i["personal_email"])

        print json.dumps(out)

def data_import(file):
    with open(file, "r") as f:
        data = json.loads(f.read())
        for item in data:
            person = schema.Person.from_flat(item)
            import pdb; pdb.set_trace()
            if person.validate():
                print "am validat coaie"
            else:
                print "eroare frate"

