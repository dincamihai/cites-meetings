import flatland as fl
from cites import database
from .common import *


_CategoriesSchemaDefinition = fl.Dict.with_properties(widget="schema") \
                                     .named("categories") \
                                     .of(
    CommonString.named("stat").using(label=u"Stat"),

    CommonBoolean.named("fee").using(label=u"Fee"),

    CommonString.named("name").using(label=u"Name"),

    CommonString.named("representative").using(label=u"Representative"),

    CommonInteger.named("credent").using(label=u"Credent"),

    CommonInteger.named("room_sort").using(label=u"Room sort"),

    CommonBoolean.named("registered").using(label=u"Registered"),

    CommonString.named("details_of_registration")
                .using(label=u"Details of registration"),

    CommonInteger.named("id").using(label=u"Id"),

    CommonString.named("invitation_received")
                .using(label=u"Invitation received"),

    CommonInteger.named("reg_sort").using(label=u"Reg sort"),

    CommonBoolean.named("registration_fee").using(label=u"Registration fee"),

    CommonString.named("badge_color").using(label=u"Badge color"),

    CommonInteger.named("stat_sort").using(label=u"Stat sort"),

    CommonString.named("reg").using(label=u"Reg"),

    CommonString.named("room").using(label=u"Room")
)

_MeetingSchemaDefinition = fl.Dict.with_properties(widget="schema") \
                                  .of(
    CommonDict.named("meeting") \
              .using(label="") \
              .of(

        CommonString.named("description") \
                    .using(optional=False, \
                           label=u"Description") \
                    .with_properties(attr={"autofocus": ""}),

        CommonString.named("venue") \
                    .using(optional=False,
                           label=u"Venue"),

        _CategoriesSchemaDefinition.using(label="") \
                                   .with_properties(widget="hide")
    )
)


class MeetingSchema(_MeetingSchemaDefinition):

    @property
    def value(self):
        return Meeting(super(MeetingSchema, self).value)


class Meeting(dict):

    id = None

    @staticmethod
    def from_flat(meeting_row):
        meeting = MeetingSchema.from_flat(meeting_row).value
        meeting.id = meeting_row.id
        return meeting

    @classmethod
    def get_or_404(cls, meeting_id):
        return cls.from_flat(database.get_meeting_or_404(meeting_id))

    @property
    def description(self):
        return self["meeting"]["description"]

    @property
    def venue(self):
        return self["meeting"]["venue"]
