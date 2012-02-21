import flatland as fl
import os
import json

def _load_json(name):
    with open(os.path.join(os.path.dirname(__file__), name), "rb") as f:
        return json.load(f)

def valid_enum(element, state):
    if not element.valid_value(element, element.value):
        element.add_error(u"Selected value is not valid")
        return False
    return True


countries = _load_json("data/countries.json")

Person = fl.Dict.of(
    fl.String.named('name_title').using(optional=True) \
        .with_properties(label=u"Personal title"),

    fl.String.named('first_name') \
        .with_properties(label=u"First name"),

    fl.String.named('last_name') \
        .with_properties(label=u"Last name"),

    fl.String.named('address').using(optional=True) \
        .with_properties(label=u"Address",
                         widget='textarea'),

    fl.Enum.named("country").valued(*sorted(countries.keys())) \
        .using(validators=[valid_enum]) \
        .with_properties(label=u"Country", widget="select",
                         value_labels=countries),

    fl.String.named('phone').using(optional=True) \
        .with_properties(label=u"Telephone"),

    fl.Boolean.named('invitation') \
        .with_properties(label=u"Invitation"),
)
