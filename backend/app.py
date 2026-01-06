import os
from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text,inspect

app = Flask(__name__, static_folder="static")

# SQLite file path (bind-mount backend/ to persist it on your machine)
DB_PATH = os.environ.get("DB_PATH", "/app/backend/meet_assist.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

CURRENT_ORG_ID = int(os.environ.get("CURRENT_ORG_ID", "1"))
CURRENT_ORG_NAME = os.environ.get("CURRENT_ORG_NAME", "Demo Org")

class Organization(db.Model):
    __tablename__ = "organizations"

    org_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    def to_dict(self):
        return {"org_id": self.org_id, "name": self.name}

class Athlete(db.Model):
    __tablename__ = "athletes"

    athlete_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    org_id = db.Column(db.Integer, nullable=False, default=CURRENT_ORG_ID)
    team_id = db.Column(db.Integer, nullable=False, default=1)
    varsity_yn = db.Column(db.String(1), nullable=False, default="N")      # Y/N

    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)

    available_yn = db.Column(db.String(1), nullable=False, default="Y")    # Y/N
    expected_return = db.Column(db.String(10), nullable=True)              # "YYYY-MM-DD" (string for now)
    grad_year = db.Column(db.Integer, nullable=True)

    # Background soft-delete marker (not shown in UI)
    is_active = db.Column(db.String(1), nullable=False, default="Y")        # Y/N

    def to_dict(self):
        return {
            "athlete_id": self.athlete_id,
            "org_id": self.org_id,
            "team_id": self.team_id,
            "varsity_yn": self.varsity_yn,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "available_yn": self.available_yn,
            "expected_return": self.expected_return,
            "grad_year": self.grad_year,
            # leave is_active available to API; UI ignores it
            "is_active": self.is_active,
        }


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
    # default: only active athletes; allow include_inactive=true
    include_inactive = (request.args.get("include_inactive") or "").lower() in {"1", "true", "yes", "y"}
    q = Athlete.query.filter(Athlete.org_id == CURRENT_ORG_ID)
    if not include_inactive:
        q = q.filter(Athlete.is_active == "Y")
    athletes = q.order_by(Athlete.athlete_id.asc()).all()
    return jsonify([a.to_dict() for a in athletes]), 200


@app.post("/api/athletes")
def create_athlete():
    data = request.get_json(silent=True) or {}

    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()
    if not first or not last:
        return {"error": "first_name and last_name are required"}, 400

    team_id = data.get("team_id", 1)
    varsity_yn = data.get("varsity_yn", "N")
    available_yn = data.get("available_yn", "Y")
    expected_return = data.get("expected_return") or None
    grad_year = data.get("grad_year", None)

    # validate types/values
    try:
        team_id = int(team_id)
        if team_id < 1:
            raise ValueError()
    except (TypeError, ValueError):
        return {"error": "team_id must be a positive integer"}, 400

    if varsity_yn not in {"Y", "N"}:
        return {"error": "varsity_yn must be 'Y' or 'N'"}, 400
    if available_yn not in {"Y", "N"}:
        return {"error": "available_yn must be 'Y' or 'N'"}, 400

    if grad_year in ("", None):
        grad_year = None
    else:
        try:
            grad_year = int(grad_year)
        except (TypeError, ValueError):
            return {"error": "grad_year must be an integer"}, 400

    if expected_return == "":
        expected_return = None

    a = Athlete(
        org_id=CURRENT_ORG_ID,
        first_name=first,
        last_name=last,
        team_id=team_id,
        varsity_yn=varsity_yn,
        available_yn=available_yn,
        expected_return=expected_return,
        grad_year=grad_year,
        is_active="Y",
    )
    db.session.add(a)
    db.session.commit()
    return jsonify(a.to_dict()), 201


@app.patch("/api/athletes/<int:athlete_id>")
def update_athlete(athlete_id: int):
    a = Athlete.query.filter_by(athlete_id=athlete_id, org_id=CURRENT_ORG_ID).first()
    if not a:
        return {"error": "Not found"}, 404

    data = request.get_json(silent=True) or {}
    allowed = {
        "team_id",
        "varsity_yn",
        "first_name",
        "last_name",
        "available_yn",
        "expected_return",
        "grad_year",
        # keep for soft delete later (not shown in UI)
        "is_active",
    }

    for k, v in data.items():
        if k not in allowed:
            continue

        if k in {"team_id", "grad_year"}:
            if v in ("", None):
                v = None
            else:
                try:
                    v = int(v)
                except (TypeError, ValueError):
                    return {"error": f"{k} must be an integer"}, 400
                if k == "team_id" and v < 1:
                    return {"error": "team_id must be a positive integer"}, 400

        if k in {"varsity_yn", "available_yn", "is_active"}:
            if v not in {"Y", "N"}:
                return {"error": f"{k} must be 'Y' or 'N'"}, 400

        if k in {"first_name", "last_name"}:
            v = (v or "").strip()
            if not v:
                return {"error": f"{k} is required"}, 400

        if k == "expected_return" and (v == "" or v is None):
            v = None

        setattr(a, k, v)

    db.session.commit()
    return jsonify(a.to_dict()), 200


if __name__ == "__main__":
    # For local non-docker runs
    app.run(host="0.0.0.0", port=5000, debug=True)
