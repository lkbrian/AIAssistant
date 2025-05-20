from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models import db
from routes import groq, auth, langchain
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(groq)
    app.register_blueprint(auth)
    app.register_blueprint(langchain)
    # Create database tables
    with app.app_context():
        # Enable pgvector extension
        from sqlalchemy import text

        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.session.commit()

        # Create tables
        db.create_all()

    @app.route("/")
    def index():
        return {"message": "Welcome to MarketAI API", "version": "1.0.0"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", debug=True)
