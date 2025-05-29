from config import app, db
from sqlalchemy import text
from products.routes import products
from auth.routes import auth
from foods.routes import foods
from accomodations.routes import accommodations
from routes import category, business

app.register_blueprint(auth)
app.register_blueprint(business)
app.register_blueprint(products)
app.register_blueprint(category)
app.register_blueprint(foods)
app.register_blueprint(accommodations)

with app.app_context():
    # db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    db.session.commit()
    db.create_all()


@app.route("/")
def index():
    return {"message": "Welcome to MarketAI API", "version": "1.0.0"}


if __name__ == "__main__":
    app.run(port=5000, debug=True)
