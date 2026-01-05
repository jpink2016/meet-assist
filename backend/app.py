import os
from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder="static")

# Persist DB to a file. In Docker, this path is inside the container unless you bind-mount it.
DB_PATH = os.environ.get("DB_PATH", "/app/backend/meet_assist.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Athlete(db.Model):
    __tablename__ = "athletes"
    athlete_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    team_id = db.Column(db.Integer, nullable=False, default=1)          # placeholder for now
    varsity = db.Column(db.String(1), nullable=False, default="N")      # Y/N

    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)

    unavailable_yn = db.Column(db.String(1), nullable=False, default="N")   # Y/N
    expected_return = db.Column(db.String(10), nullable=True)               # keep as text "YYYY-MM-DD" for now
    grad_year = db.Column(db.Integer, nullable=True)

    is_active = db.Column(db.String(1), nullable=False, default="Y")        # Y/N (soft delete)

    def to_dict(self):
        return {
            "athlete_id": self.athlete_id,
            "team_id": self.team_id,
            "varsity": self.varsity,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "unavailable_yn": self.unavailable_yn,
            "expected_return": self.expected_return,
            "grad_year": self.grad_year,
            "is_active": self.is_active,
        }


# Create tables on startup (fine for now; later we’ll switch to migrations)
with app.app_context():
    db.create_all()

@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.get("/athletes")
def athletes_page():
    return send_from_directory(app.static_folder, "athletes.html")

@app.get("/api/athletes")
def list_athletes():
    athletes = Athlete.query.order_by(Athlete.athlete_id.asc()).all()
    return jsonify([a.to_dict() for a in athletes]), 200

@app.post("/api/athletes")
def create_athlete():
    data = request.get_json(silent=True) or {}
    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()

    if not first or not last:
        return {"error": "first_name and last_name are required"}, 400

    a = Athlete(
        first_name=first,
        last_name=last,
        team_id=1,
        varsity="N",
        unavailable_yn="N",
        expected_return=None,
        grad_year=None,
        is_active="Y")

    db.session.add(a)
    db.session.commit()
    return jsonify(a.to_dict()), 201
