import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_jwt_extended import JWTManager

load_dotenv()


app = Flask(__name__)

app.secret_key = os.environ.get("JWT_SECRET_KEY", "default-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@db:5432/marketai"
)
app.config["EMBEDDING_MODEL"] = "embed-v4.0"
app.config["COHERE_API_KEY"] = os.environ.get("COHERE_API_KEY")
app.config["GROQ_API_KEY"] = os.environ.get("GROQ_API_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(weeks=1)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "default-jwt-secret")
app.config["EMBEDDING_DIMENSION"] = 1024
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

app.json.compact = False
metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)


db = SQLAlchemy(metadata=metadata)
db.init_app(app)
blacklist = set()
jwt = JWTManager()
jwt.init_app(app)
migrate = Migrate(app, db)
CORS(app)


@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    return jwt_payload["jti"] in blacklist
