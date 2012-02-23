import flask
import flatland.out.markup
import schema
import database

webpages = flask.Blueprint("webpages", __name__)

@webpages.route("/")
def home():
    return flask.render_template("home.html", **{
        "people": [flask.json.loads(r.data)
                   for r in database.Person.query.all()],
    })

@webpages.route("/new", methods=["GET", "POST"])
@webpages.route("/edit/<int:person_id>", methods=["GET", "POST"])
def edit(person_id=None):
    app = flask.current_app

    if person_id is None:
        person_row = None
    else:
        person_row = database.Person.query.get_or_404(person_id)

    if flask.request.method == "POST":
        form_data = dict(schema.Person.from_defaults().flatten())
        form_data.update(flask.request.form.to_dict())
        person = schema.Person.from_flat(form_data)

        if person.validate():
            if person_row is None:
                person_row = database.Person()
            session = database.adb.session
            person_row.data = flask.json.dumps(dict(person.flatten()))
            session.add(person_row)
            session.commit()
            flask.flash("Person information saved", "success")
            edit_url = flask.url_for("webpages.edit", person_id=person_row.id)
            return flask.redirect(edit_url)

        else:
            flask.flash(u"Errors in person information", "error")

    else:
        if person_row is None:
            person = schema.Person()
        else:
            person = schema.Person.from_flat(flask.json.loads(person_row.data))

    return flask.render_template("edit.html", **{
        "mk": MarkupGenerator(app.jinja_env.get_template("widgets.html")),
        "person": person,
    })

class MarkupGenerator(flatland.out.markup.Generator):

    def __init__(self, template):
        super(MarkupGenerator, self).__init__("html")
        self.template = template

    def children_order(self, field):
        if isinstance(field, flatland.Mapping):
            return [kid.name for kid in field.field_schema]
        else:
            return []

    def widget(self, element, widget_name=None):
        if widget_name is None:
            widget_name = element.properties.get("widget", "input")
        widget_macro = getattr(self.template.module, widget_name)
        return widget_macro(self, element)
