import flatland as fl
from flatland.validation import IsEmail, Converted

from cites import database
from common import *


_PersonSchemaDefinition = fl.Dict.with_properties(widget="schema") \
                                 .of(

    CommonDict.named("personal") \
              .using(label="") \
              .of(

        CommonEnum.named("name_title") \
                    .valued(*sorted(personal_title.keys())) \
                    .using(label=u"Personal title") \
                    .with_properties(attr={"autofocus": ""}),

        CommonString.named("first_name") \
                    .using(optional=False,
                           label=u"First name"),

        CommonString.named("last_name") \
                    .using(optional=False,
                           label=u"Last name"),

        CommonEnum.named("language") \
                  .valued(*sorted(language.keys())) \
                  .using(label=u"Language") \
                  .with_properties(value_labels=language),

        CommonString.named("address") \
                    .using(label=u"Address") \
                    .with_properties(widget="textarea"),

        CommonString.named("email") \
                    .using(label=u"Email") \
                    .including_validators(IsEmail()) \
                    .with_properties(attr={"type": "email"}),

        CommonString.named("phone") \
                    .using(label=u"Phone") \
                    .with_properties(attr={
                        "type": "tel",
                        "pattern": r"^\d+ \d+ \d+$",
                        "title": "(999 000 555)",
                    }),

        CommonString.named("cellular") \
                    .using(label=u"Cellular"),

        CommonString.named("fax") \
                    .using(label=u"Fax"),

        CommonString.named("place") \
                    .using(label=u"Place"),

        CommonEnum.named("country") \
                  .valued(*sorted_country_codes) \
                  .using(label=u"Country") \
                  .with_properties(value_labels=country),

        CommonEnum.named("category") \
                  .valued(*sorted(category.keys())) \
                  .using(label=u"Category") \
                  .with_properties(value_labels=category_labels),

        CommonEnum.named("fee") \
                  .using(label=u"Fee") \
                  .valued(*sorted(fee.keys())) \
                  .with_properties(value_labels=fee)
     ),

    CommonDict.named("representing") \
              .using(label=u"Representing") \
              .of(

        CommonEnum.named("country") \
                  .valued(*sorted_country_codes) \
                  .using(label=u"Country") \
                  .with_properties(value_labels=country),

        CommonEnum.named("region") \
                  .valued(*sorted_regions) \
                  .using(label=u"Region") \
                  .with_properties(value_labels=region),

        CommonString.named("organization") \
                    .using(label=u"Organization") \
                    .with_properties(widget="textarea"),

        CommonBoolean.named("organization_show") \
                     .using(label=u"Show in address"),
    ),

    CommonDict.named("meeting_flags") \
              .using(label=u"Meeting flags") \
              .of(

        CommonBoolean.named("sponsored") \
                     .using(label=u"Sponsored"),

        CommonBoolean.named("finance_subcommittee") \
                     .using(label=u"Finance Subcommittee"),

        CommonBoolean.named("credentials") \
                     .using(label=u"Credentials"),

        CommonBoolean.named("approval") \
                     .using(label=u"Approval"),

        CommonBoolean.named("invitation") \
                     .using(label=u"Invitation"),

        CommonBoolean.named("web_alert") \
                     .using(label=u"Web alert"),

        CommonBoolean.named("verified") \
                     .using(label=u"Verified"),

        fl.Date.named("acknowledged") \
               .using(label=u"Date acknowledged",
                      optional=True) \
               .including_validators(Converted(incorrect=u"%(label)s is not "
                                                          "a valid date")),

        CommonBoolean.named("attended") \
                     .using(label=u"Attended"),

    ),

    CommonDict.named("more_info") \
              .using(label=u"Additional information") \
              .of(

        CommonString.named("text") \
                    .using(label=u"") \
                    .with_properties(widget="textarea"),

    ),
)


class PersonSchema(_PersonSchemaDefinition):

    @property
    def value(self):
        return Person(super(PersonSchema, self).value)


class Person(dict):

    id = None

    @staticmethod
    def from_flat(person_row):
        person = PersonSchema.from_flat(person_row).value
        person.id = person_row.id
        return person

    @classmethod
    def get_or_404(cls, person_id):
        return cls.from_flat(database.get_person_or_404(person_id))

    @property
    def name(self):
        return "%s %s %s" % (
            self["personal"]["name_title"],
            self["personal"]["first_name"],
            self["personal"]["last_name"],
        )

    @property
    def has_photo(self):
        assert self.id is not None
        person_row = database.get_person_or_404(self.id)
        return bool(person_row.get("photo_id", ""))

    def representing(self, description=None):
        category_id = self["personal"]["category"]
        representing = ""

        if category_id  == "10":
            representing = "%s - %s" % (
                            region[self["representing"]["region"]],
                            country[self["representing"]["country"]],
                           )
        elif category_id in ["20", "30", "40"]:
            representing = country[self["representing"]["country"]]
        elif category_id in ["98", "99"]:
            representing = description or category[category_id]["name"]
        else:
            representing = self["representing"]["organization"]
        return representing

    @property
    def category(self):
        return category.get(self["personal"]["category"], "")

    @property
    def region(self):
        return region.get(self["representing"]["region"], "")

    @property
    def country(self):
        return country.get(self["representing"]["country"], "")

    @property
    def personal_country(self):
        return country.get(self["personal"]["country"], "")

    @property
    def fee(self):
        return fee.get(self["personal"]["fee"], "")

    @property
    def language(self):
        return language.get(self["personal"]["language"], "")

    @property
    def room_list(self):
        category_id = self["personal"]["category"]
        room_list = None

        if category_id == "10":
            room_list = "%s - %s" % (
                region[self["representing"]["region"]],
                country[self["representing"]["country"]],
           )
        elif category_id in ("20", "30", "40"):
            room_list = country[self["representing"]["country"]]
        elif category_id > 40:
            room_list = self["representing"]["organization"]

        return room_list

    @property
    def ref_list(self):
        category_id = self["personal"]["category"]
        ref_list = None

        if category_id == "10":
            ref_list = "%s-%s" % (
                region[self["representing"]["region"]],
                country[self["representing"]["country"]],
            )
        elif category_id in ("20", "30", "40"):
            ref_list = country[self["representing"]["country"]]
        elif category_id in ("98", "99"):
            ref_list = self["representing"]["organization"]

        return ref_list

    @property
    def verifpart(self):
        category_id = self["personal"]["category"]
        verifpart = None

        if category_id in ["10", "20", "30", "40"]:
            verifpart = country[self["representing"]["country"]]
        else:
            verifpart = self["representing"]["organization"]

        return verifpart

