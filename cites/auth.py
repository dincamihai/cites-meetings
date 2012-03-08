import logging
import flask
import sugar

auth = flask.Blueprint("auth", __name__)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def initialize_app(app):
    app.register_blueprint(auth)


@auth.route("/login", methods=["GET", "POST"])
@sugar.templated("auth/login.html")
def login():
    login_email = flask.request.form.get("email", "")
    login_password = flask.request.form.get("password", "")
    next_url = flask.request.values.get("next", flask.url_for("participant.home"))

    if flask.request.method == "POST":
        app = flask.current_app
        for email, password in app.config.get("ACCOUNTS", []):
            if login_email == email and login_password == password:
                log.info("Authentication by %r", login_email)
                flask.session["logged_in_email"] = login_email
                return flask.redirect(next_url)
        else:
            flask.flash(u"Login failed", "error")

    return {
        "email": login_email,
        "next": next_url,
    }


@auth.route("/logout")
def logout():
    next_url = flask.request.values.get("next", flask.url_for("participant.home"))
    if "logged_in_email" in flask.session:
        del flask.session["logged_in_email"]
    return flask.redirect(next_url)
