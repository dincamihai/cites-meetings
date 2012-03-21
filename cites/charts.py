from collections import defaultdict
import flask

from auth import auth_required
import database
import sugar
import schema

charts = flask.Blueprint("charts", __name__)

def initialize_app(app):
    app.register_blueprint(charts)


@charts.route("/meeting/1/charts")
@auth_required
@sugar.templated("charts/home.html")
def home():
    categories = defaultdict(int)

    persons = list(database.get_all_persons())
    for person_row in persons:
        person = schema.PersonSchema.from_flat(person_row).value
        categories[person.category["name"]] += 1

    total_count = len(persons)
    for category, count in categories.items():
        categories[category] = (count * 100) / total_count

    categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    labels = [c[0] for c in categories ]
    data = [c[1] for c in categories]

    return {
        "data": flask.json.dumps(data),
        "labels": flask.json.dumps(labels),
        "categories": categories,
    }
