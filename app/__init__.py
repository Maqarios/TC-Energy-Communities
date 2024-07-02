import flask


def create_app():
    app = flask.Flask(__name__)
    app.config.from_object("config.Config")

    from .routes import main

    app.register_blueprint(main)

    return app
