import flatland as fl


countries = ['it', 'no']


person = fl.Dict.of(
    fl.String.named('name_title').using(optional=True),
    fl.String.named('first_name'),
    fl.String.named('last_name'),
    fl.String.named('address').using(optional=True),
    fl.Enum.named('country').valued(*countries),
    fl.String.named('phone').using(optional=True),
    fl.Boolean.named('invitation'),
)
