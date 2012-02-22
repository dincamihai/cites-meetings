import flatland as fl
from flatland.validation import IsEmail, Converted, Validator
import os
import json
import re

date_re = re.compile(
    r"^(0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])[- /.](19|20)\d\d$"
)
def _load_json(name):
    with open(os.path.join(os.path.dirname(__file__), name), "rb") as f:
        return json.load(f)

# takes a list [{"id": 1, "name": "Test"}] => {1: "Test"}
def _switch_id_name_to_key_value(lst):
    lst = { item["id"]: item["name"]  for item in lst }
    return lst

class EnumValue(Validator):

    fail = fl.validation.base.N_(u'%(u)s is not a valid value for %(label)s.')

    def validate(self, element, state):
        if element.valid_values:
            if element.value not in element.valid_values:
                return self.note_error(element, state, 'fail')
        return True


countries = _load_json("refdata/countries.json")
countries = _switch_id_name_to_key_value(countries)

languages = _load_json("refdata/languages.json")

categories = _load_json("refdata/categories.json")
categories = _switch_id_name_to_key_value(categories)

regions = _load_json("refdata/regions.json")
regions = _switch_id_name_to_key_value(regions)

fee = []


CommonString = fl.String.using(optional=True)
CommonEnum = fl.Enum.using(optional=True) \
                    .including_validators(EnumValue()) \
                    .with_properties(widget="select")
# CommonBoolean has optional=False because booleans are
# required to be True or False (None is not allowed)
CommonBoolean = fl.Boolean.with_properties(widget="checkbox")
CommonDict = fl.Dict.with_properties(widget="group")


Person = fl.Dict.of(

    CommonDict.named("personal") \
              .using(label="Personal") \
              .of(

        CommonString.named("name_title") \
                    .using(label=u"Personal title"),

        CommonString.named("first_name") \
                    .using(optional=False, label=u"First name"),

        CommonString.named("last_name") \
                    .using(optional=False, label=u"Last name"),

        CommonEnum.named("language") \
                  .valued(*sorted(languages.keys())) \
                  .using(label=u"Language") \
                  .with_properties(value_labels=languages),

        CommonString.named("address") \
                    .using(label=u"Address") \
                    .with_properties(widget="textarea"),

        CommonString.named("email") \
                    .using(label=u"Email") \
                    .including_validators(IsEmail()),

        CommonString.named("phone") \
                    .using(label=u"Phone"),

        CommonString.named("cellular") \
                    .using(label=u"Cellular"),

        CommonString.named("fax") \
                    .using(label=u"Fax"),

        CommonString.named("place") \
                    .using(label=u"Place"),

        CommonEnum.named("country") \
                  .valued(*sorted(countries.keys())) \
                  .using(label=u"Country") \
                  .with_properties(value_labels=countries),

        CommonEnum.named("category") \
            .valued(*sorted(categories.keys())) \
            .using(label=u"Category") \
            .with_properties(value_labels=categories),


        CommonEnum.named("fee").using(label=u"Fee").valued(*fee)

     ),

    CommonDict.named("representing") \
              .using(label=u"Representing") \
              .of(

        CommonEnum.named("country") \
                  .valued(*sorted(countries.keys())) \
                  .using(label=u"Country") \
                  .with_properties(value_labels=countries),

        CommonEnum.named("region") \
                  .valued(*sorted(regions.keys())) \
                  .using(label=u"Region") \
                  .with_properties(value_labels=regions),

        CommonString.named("organization") \
                    .using(label=u"Organization") \
                    .with_properties(widget="textarea"),

    ),

    CommonDict.named("type") \
              .using(label=u"Type") \
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

    ),

    CommonDict.named("info") \
              .using(label=u"More info") \
              .of(

        CommonString.named("more_info") \
                    .using(label=u"More Info"),

        CommonBoolean.named("alert") \
                     .using(label=u"Web alert"),

        CommonBoolean.named("verified") \
                     .using(label=u"Verified"),

        fl.Date.named("acknowledge") \
               .using(label=u"Date acknowledge",
                      optional=True) \
               .including_validators(Converted(incorrect=u"%(label)s is not "
                                                          "a valid date")),

        CommonBoolean.named("attended") \
                     .using(label=u"Attended"),

    )
)

from flatland.signals import validator_validated
from flatland.schema.base import NotEmpty
@validator_validated.connect
def validated(sender, element, result, **kwargs):
    if sender is NotEmpty:
        if not result:
            label = getattr(element, 'label', element.name)
            element.add_error(u"%s is required" % label)
