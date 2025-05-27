from config import app, db
from sqlalchemy import text
from products.routes import products
from auth.routes import auth
from routes import category, business

app.register_blueprint(auth)
app.register_blueprint(business)
app.register_blueprint(products)
app.register_blueprint(category)

with app.app_context():
    db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    db.session.commit()
    db.create_all()


@app.route("/")
def index():
    return {"message": "Welcome to MarketAI API", "version": "1.0.0"}


if __name__ == "__main__":
    app.run(port=5000, debug=True)
