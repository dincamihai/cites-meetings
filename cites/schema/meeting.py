import flatland as fl
from cites import database
from .common import *


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
                           label=u"Venue")
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
