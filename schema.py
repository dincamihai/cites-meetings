import flatland as fl


countries = ['it', 'no']


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

    fl.Enum.named('country').valued(*countries) \
        .with_properties(label=u"Country"),

    fl.String.named('phone').using(optional=True) \
        .with_properties(label=u"Telephone"),

    fl.Boolean.named('invitation') \
        .with_properties(label=u"Invitation"),
)
