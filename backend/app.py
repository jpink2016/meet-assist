
import os
from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect
from datetime import date

app = Flask(__name__, static_folder="static")

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


class Team(db.Model):
    __tablename__ = "teams"
    team_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {"team_id": self.team_id, "org_id": self.org_id, "name": self.name}


class EventGroup(db.Model):
    __tablename__ = "event_groups"
    event_group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    def to_dict(self):
        return {"event_group_id": self.event_group_id, "name": self.name}


class Athlete(db.Model):
    __tablename__ = "athletes"

    athlete_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    org_id = db.Column(db.Integer, nullable=False, default=CURRENT_ORG_ID)

    team_id = db.Column(db.Integer, nullable=False, default=1)
    event_group_id = db.Column(db.Integer, nullable=False, default=1)

    varsity_yn = db.Column(db.String(1), nullable=False, default="N")   # Y/N
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(1), nullable=False)  # M/F/X

    available_yn = db.Column(db.String(1), nullable=False, default="Y") # Y/N
    expected_return = db.Column(db.String(10), nullable=True)           # YYYY-MM-DD
    grad_year = db.Column(db.Integer, nullable=True)

    is_active = db.Column(db.String(1), nullable=False, default="Y")    # soft delete

    def to_dict(self):
        return {
            "athlete_id": self.athlete_id,
            "org_id": self.org_id,
            "team_id": self.team_id,
            "event_group_id": self.event_group_id,
            "varsity_yn": self.varsity_yn,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "gender": self.gender,
            "available_yn": self.available_yn,
            "expected_return": self.expected_return,
            "grad_year": self.grad_year,
            "is_active": self.is_active,
        }


def bootstrap_db():
    db.create_all()

    insp = inspect(db.engine)

    # Add missing columns to existing athletes table (SQLite)
    if "athletes" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("athletes")}

        if "org_id" not in cols:
            db.session.execute(text("ALTER TABLE athletes ADD COLUMN org_id INTEGER NOT NULL DEFAULT 1"))
            db.session.commit()

        if "event_group_id" not in cols:
            db.session.execute(text("ALTER TABLE athletes ADD COLUMN event_group_id INTEGER NOT NULL DEFAULT 1"))
            db.session.commit()
        if "gender" not in cols:
            db.session.execute(text("ALTER TABLE athletes ADD COLUMN gender TEXT NOT NULL DEFAULT 'X'"))
            db.session.commit()

    # Seed current org
    org = Organization.query.filter_by(org_id=CURRENT_ORG_ID).first()
    if not org:
        org = Organization(org_id=CURRENT_ORG_ID, name=CURRENT_ORG_NAME)
        db.session.add(org)
        db.session.commit()

    # Seed teams for org if none exist
    if Team.query.filter_by(org_id=CURRENT_ORG_ID).count() == 0:
        seeds = ["Varsity","JV","Freshman"]
        for name in seeds:
            db.session.add(Team(org_id=CURRENT_ORG_ID, name=name))
        db.session.commit()

    # Seed event groups if none exist
    if EventGroup.query.count() == 0:
        for name in ["Sprints", "Mid Distance", "Distance", "Throws", "Jumps", "PV", "Multi"]:
            db.session.add(EventGroup(name=name))
        db.session.commit()


with app.app_context():
    bootstrap_db()


@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.get("/athletes")
def athletes_page():
    return send_from_directory(app.static_folder, "athletes.html")


# ---------- Lookup APIs ----------

@app.get("/api/teams")
def list_teams():
    teams = Team.query.filter_by(org_id=CURRENT_ORG_ID).order_by(Team.name.asc()).all()
    return jsonify([t.to_dict() for t in teams]), 200


@app.get("/api/event-groups")
def list_event_groups():
    groups = EventGroup.query.order_by(EventGroup.event_group_id.asc()).all()
    return jsonify([g.to_dict() for g in groups]), 200


# ---------- Athletes APIs ----------

@app.get("/api/athletes")
def list_athletes():
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
    
    # TODO make sure the M in data.get doesn't cause error
    gender = data.get("gender", "M")
    if gender not in {"M", "F", "X"}:
        return {"error": "gender must be 'M' or 'F'"}, 400

    # team/event group come from dropdowns; still validate
    team_id = data.get("team_id")
    event_group_id = data.get("event_group_id")
    varsity_yn = data.get("varsity_yn", "N")
    available_yn = data.get("available_yn", "Y")
    expected_return = data.get("expected_return") or None
    grad_year = data.get("grad_year", None)

    try:
        team_id = int(team_id)
    except (TypeError, ValueError):
        return {"error": "team_id must be an integer"}, 400

    if Team.query.filter_by(team_id=team_id, org_id=CURRENT_ORG_ID).first() is None:
        return {"error": "team_id is not valid for this organization"}, 400

    try:
        event_group_id = int(event_group_id)
    except (TypeError, ValueError):
        return {"error": "event_group_id must be an integer"}, 400

    if EventGroup.query.filter_by(event_group_id=event_group_id).first() is None:
        return {"error": "event_group_id is not valid"}, 400

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
        team_id=team_id,
        event_group_id=event_group_id,
        varsity_yn=varsity_yn,
        first_name=first,
        last_name=last,
        gender=gender,
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
        "event_group_id",
        "varsity_yn",
        "first_name",
        "last_name",
        "gender",
        "available_yn",
        "expected_return",
        "grad_year",
        "is_active",  # background for soft delete later
    }

    for k, v in data.items():
        if k not in allowed:
            continue

        if k in {"team_id", "event_group_id", "grad_year"}:
            if v in ("", None):
                v = None
            else:
                try:
                    v = int(v)
                except (TypeError, ValueError):
                    return {"error": f"{k} must be an integer"}, 400

            if k == "team_id":
                if v is None or Team.query.filter_by(team_id=v, org_id=CURRENT_ORG_ID).first() is None:
                    return {"error": "team_id is not valid for this organization"}, 400

            if k == "event_group_id":
                if v is None or EventGroup.query.filter_by(event_group_id=v).first() is None:
                    return {"error": "event_group_id is not valid"}, 400

        if k in {"varsity_yn", "available_yn", "is_active"}:
            if v not in {"Y", "N"}:
                return {"error": f"{k} must be 'Y' or 'N'"}, 400

        if k in {"first_name", "last_name"}:
            v = (v or "").strip()
            if not v:
                return {"error": f"{k} is required"}, 400
        
        if k == "gender":
            if v not in {"M", "F", "X"}:
                return {"error": "gender must be 'M' or 'F' or 'X'"}, 400

        if k == "expected_return" and (v == "" or v is None):
            v = None

        setattr(a, k, v)

    db.session.commit()
    return jsonify(a.to_dict()), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
