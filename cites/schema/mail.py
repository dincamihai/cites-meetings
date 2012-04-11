import flatland as fl
from flatland.validation import IsEmail
from .common import CommonDict, CommonString


MailSchema = fl.Dict.with_properties(widget="mail") \
              .of(
    CommonString.named("to") \
                .using(label=u"To", optional=False) \
                .including_validators(IsEmail()) \
                .with_properties(widget="input"),

    CommonString.named("cc") \
                .using(label=u"Cc") \
                .including_validators(IsEmail())
                .with_properties(widget="input"),

    CommonString.named("subject") \
                .using(label=u"Subject", optional=False) \
                .with_properties(widget="input"),

    CommonString.named("message") \
                .using(label=u"Message",
                       optional=False,
                       strip=False) \
                .with_properties(widget="textarea")
)
