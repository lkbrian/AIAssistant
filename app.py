from config import app, db
from routes import groq, auth
from sqlalchemy import text
from langchain_pipeline.routes import langchain

app.register_blueprint(groq)
app.register_blueprint(auth)
app.register_blueprint(langchain)

with app.app_context():
    db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    db.session.commit()
    db.create_all()


@app.route("/")
def index():
    return {"message": "Welcome to MarketAI API", "version": "1.0.0"}


if __name__ == "__main__":
    app.run(port=5000, debug=True)
