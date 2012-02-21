import flatland as fl
import os
import json
import re

# django regex for email validation
email_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    # quoted-string, see also http://tools.ietf.org/html/rfc2822#section-3.2.5
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"'
    r')@((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$)'  # domain
    r'|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$',
    re.IGNORECASE
)

date_re = re.compile(
    r"^(0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])[- /.](19|20)\d\d$"
)
def _load_json(name):
    with open(os.path.join(os.path.dirname(__file__), name), "rb") as f:
        return json.load(f)

def valid_enum(element, state):
    if not element.valid_value(element, element.value) and element.valid_values:
        element.add_error(u"Selected value is not valid.")
        return False
    return True

def valid_email(element, state):
    if not email_re.search(element.value):
        element.add_error(u"Email is not valid.")
        return False
    return True

def valid_date(element, state):
    if not date_re.search(element.value):
        element.add_error(u"Not a valid date")
        return False
    return True

countries = _load_json("refdata/countries.json")
languages = _load_json("refdata/languages.json")
categories = ["Observer, Party"]
regions = []
fee = []

CommonString = fl.String.using(optional=True)
CommonEnum = fl.Enum.using(validators=[valid_enum]) \
                    .with_properties(widget="select")
CommonDict = fl.Dict.with_properties(widget="group")
CommonBoolean = fl.Boolean.using(optional=True).with_properties(widget="checkbox")

Person = fl.Dict.of(
    CommonDict.named("personal").of(
        CommonString.named("name_title").using(label=u"Personal title"),

        CommonString.named("first_name") \
            .using(optional=False, label=u"First name"),

        CommonString.named("last_name") \
            .using(optional=False, label=u"Last name"),

        CommonEnum.named("language").valued(*sorted(languages.keys())) \
            .using(label=u"Language") \
            .with_properties(value_labels=languages),

        CommonString.named("address") \
            .using(label=u"Address") \
            .with_properties(widget="textarea"),

        CommonString.named("email") \
            .using(optional=False, label=u"Email", validators=[valid_email]),

        CommonString.named("phone").using(label=u"Phone"),
        CommonString.named("cellular").using(label=u"Cellular"),
        CommonString.named("fax").using(label=u"Fax"),

        CommonString.named("place").using(label=u"Place"),

        CommonEnum.named("country").valued(*sorted(countries.keys())) \
            .using(label=u"Country") \
            .with_properties(value_labels=countries),

        CommonEnum.named("category").valued(*categories) \
            .using(label=u"Category"),

        CommonEnum.named("fee").using(optional=True, label=u"Fee").valued(*fee)
     ).using(label="Personal"),

    CommonDict.named("representing").of(
        CommonEnum.named("country").valued(*sorted(countries.keys())) \
            .using(label=u"Country") \
            .with_properties(value_labels=countries),

        CommonEnum.named("region").valued(*regions) \
            .using(optional=True, label=u"Region") \
            .with_properties(value_labels=regions),

        CommonString.named("organization") \
            .using(optional=True, label=u"Organization") \
            .with_properties(widget="textarea"),
    ).using(label=u"Representing"),

    CommonDict.named("type").of(
        CommonBoolean.named("sponsored").using(label=u"Sponsored"),
        CommonBoolean.named("finance_subcommittee") \
            .using(label=u"Finance Subcommittee"),
        CommonBoolean.named("credentials").using(label=u"Credentials"),
        CommonBoolean.named("approval").using(label=u"Approval"),
        CommonBoolean.named("invitation").using(label=u"Invitation"),
    ).using(label=u"Type"),

    CommonDict.named("info").of(
        CommonString.named("more_info").using(optional=True, label=u"More Info"),
        CommonBoolean.named("web_alert").using(label=u"Web alert"),
        CommonBoolean.named("verified").using(label=u"Verified"),
        CommonString.named("date") \
            .using(label=u"Date acknowledge", optional=True, validators=[valid_date]),
        CommonBoolean.named("attended").using(label=u"Attended"),
    ).using(label=u"More info")

)
