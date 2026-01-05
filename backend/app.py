from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from datetime import datetime

app = Flask(__name__, static_folder = "static") # static_url_path="/static")

# The database file will live in backend/movies.db
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///movies.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # silence warnings

print("Using DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])  # ← here

db = SQLAlchemy(app)

with app.app_context():
    try:
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith("sqlite"):
            db.create_all()
        else:
            db.session.execute(text("SELECT 1"))
    except OperationalError as e:
        print("DB connectivity issue on startup:", repr(e))

class Movie(db.Model):
    __tablename__ = 'movie'
    rating_id = db.Column(db.Integer, primary_key=True)      # unique id for each row
    rating = db.Column(db.Integer, nullable=False)   # movie rating
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # NEW
    valid_from = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valid_thru = db.Column(db.DateTime, nullable=True)  # None = still current
    movie_name = db.relationship("MovieTitle")
    title_id = db.Column(db.Integer, db.ForeignKey("movie_title.title_id"), nullable=False)

class MovieTitle(db.Model):
    __tablename__ = 'movie_title'
    title_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)

with app.app_context():
    db.create_all()

@app.route("/titles", methods=["GET"]) 
def titles(): 
    titles = MovieTitle.query.order_by(MovieTitle.title).all() 
    return jsonify([{
        "title_id": t.title_id, "title": t.title} 
        for t in titles
    ])

@app.route("/add", methods=["POST"])
def add_movie():
    data = request.get_json()
    rating = int(data["rating"])
    title_id = int(data["title_id"])

    now = datetime.utcnow()

    # Make sure the title exists
    title = MovieTitle.query.get_or_404(title_id)

    # Find any active current row for this movie
    existing = Movie.query.filter_by(title_id=title_id, is_active=True).first()
    if existing:
        existing.is_active = False
        existing.valid_thru = now  # close out the old version

    new_movie = Movie(
        rating=rating, 
        valid_from=now,
        is_active=True,
        title_id = title_id
    )
    db.session.add(new_movie)
    db.session.commit()
    return jsonify({"message": f"Recorded {title.title} with rating {rating}"}), 201

@app.route("/movies/<int:rating_id>", methods=["DELETE"])
def delete_movie(rating_id):
    movie = Movie.query.get_or_404(rating_id)
    movie.is_active = False          # soft delete
    movie.valid_thru = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": f"Rating {rating_id} deactivated"}), 200

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    movies = (
            Movie.query
            .filter_by(is_active=True)
            .order_by(Movie.rating.desc())
            .all()  # sorted by rating
    )
    movie_list = [
        {
            "rating_id":m.rating_id ,
            "name": m.movie_name.title, # comes from movie_title via relationship
            "rating": m.rating
        } 
        for m in movies
    ]
    return jsonify(movie_list)

@app.route("/")
def serve_frontend():
    return app.send_static_file("index.html")

@app.route("/history", methods=["GET"])
def history():
    rows = Movie.query.order_by(Movie.valid_from).all()
    data = [
        {
            "name": m.movie_name.title,
            "rating": m.rating,
            "valid_from": m.valid_from.isoformat(),
            "valid_thru": m.valid_thru.isoformat() if m.valid_thru else None,
        }
        for m in rows
    ]
    return jsonify(data)

@app.route("/health")
def health():
    return "ok", 200

@app.route("/dbcheck")
def dbcheck():
    try:
        db.session.execute(text("SELECT 1"))
        return {"db":"ok"}, 200
    except Exception as e:
        return {"db":"error","detail":repr(e)}, 500

if __name__ == "__main__":
    #app.run(debug=True, port=5000)
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
