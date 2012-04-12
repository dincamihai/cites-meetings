import os
import json
import re
from operator import itemgetter

import flatland as fl
from flatland.validation import Validator, ValueGreaterThan
from flatland.signals import validator_validated
from flatland.schema.base import NotEmpty


def _load_json(name):
    with open(os.path.join(os.path.dirname(__file__), name), "rb") as f:
        return json.load(f)

class EnumValue(Validator):

    fail = fl.validation.base.N_(u'%(u)s is not a valid value for %(label)s.')

    def validate(self, element, state):
        if element.valid_values:
            if element.value not in element.valid_values:
                return self.note_error(element, state, 'fail')
        return True

class IsPhone(Validator):

    fail = fl.validation.base.N_(
        u"%(label)s is not valid. "
         "Please enter three groups of digits separated by spaces.")
    phone_pattern = re.compile(r'^\d+ \d+ \d+$')

    def validate(self, element, state):
        if self.phone_pattern.match(element.value) is None:
            return self.note_error(element, state, 'fail')
        return True


CommonString = fl.String.using(optional=True)
CommonEnum = fl.Enum.using(optional=True) \
                    .including_validators(EnumValue()) \
                    .with_properties(widget="select")

# CommonBoolean has optional=False because booleans are
# required to be True or False (None is not allowed)
CommonBoolean = fl.Boolean.using(optional=True).with_properties(widget="checkbox")
CommonDict = fl.Dict.with_properties(widget="group")
CommonInteger = fl.Integer.using(optional=True) \
                          .including_validators(ValueGreaterThan(boundary=0))

# Data
country = {item["id"]: item["name"]  for item in
           _load_json("../refdata/countries.json")}
# sort by country name for select option
# [("iso code", "country_name"),]
sorted_country_codes = sorted(country.items(), key=itemgetter(1))
# ["iso_code", "iso_code"]
sorted_country_codes = [c[0] for c in sorted_country_codes]

personal_title = _load_json("../refdata/titles.json")
language = _load_json("../refdata/languages.json")
secretariat = _load_json("../refdata/secretariat.json")

category = {c["id"]: c for c in _load_json("../refdata/categories.json")}
category_labels = {c["id"]: c["name"] for c in category.values()}

region =  {item["id"]: item["name"]
           for item in _load_json("../refdata/regions.json")}

# sort by region name for select option
sorted_regions = sorted(region.items(), key=itemgetter(1))
sorted_regions = [r[0] for r in sorted_regions]

fee = {item["id"]: item["name"] for item in
       _load_json("../refdata/fee.json")}


@validator_validated.connect
def validated(sender, element, result, **kwargs):
    if sender is NotEmpty:
        if not result:
            label = getattr(element, 'label', element.name)
            element.add_error(u"%s is required" % label)

