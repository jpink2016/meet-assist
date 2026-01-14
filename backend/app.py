
import os
from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect, and_
from sqlalchemy.exc import IntegrityError
from datetime import date

app = Flask(__name__, static_folder="static")

DB_PATH = os.environ.get("DB_PATH", "/data/meet_assist.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

print("USING DATABASE:", app.config["SQLALCHEMY_DATABASE_URI"], flush=True)

db = SQLAlchemy(app)

CURRENT_ORG_ID = int(os.environ.get("CURRENT_ORG_ID", "1"))
CURRENT_ORG_NAME = os.environ.get("CURRENT_ORG_NAME", "Demo Org")

def parse_bool(v, default=False):
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v != 0
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {"true", "1", "yes", "y", "on"}:
            return True
        if s in {"false", "0", "no", "n", "off", ""}:
            return False
    raise ValueError("must be a boolean")

    db.session.add_all(to_add)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        # If anything already exists (shouldn't on brand-new meet), ignore gracefully

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
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {"event_group_id": self.event_group_id, "name": self.name}


class Athlete(db.Model):
    __tablename__ = "athletes"

    athlete_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    org_id = db.Column(db.Integer, nullable=False, default=CURRENT_ORG_ID)

    team_id = db.Column(db.Integer, nullable=False, default=1)
    event_group_id = db.Column(db.Integer, nullable=False, default=1)

    varsity = db.Column(db.Boolean, nullable=False, default=False)   # Y/N
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(1), nullable=False)  # M/F/X

    unavailable = db.Column(db.Boolean, nullable=False, default=False) 
    expected_return = db.Column(db.String(10), nullable=True)           # YYYY-MM-DD
    grad_year = db.Column(db.Integer, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)    # soft delete

    def to_dict(self):
        return {
            "athlete_id": self.athlete_id,
            "org_id": self.org_id,
            "team_id": self.team_id,
            "event_group_id": self.event_group_id,
            "varsity": self.varsity,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "gender": self.gender,
            "unavailable": self.unavailable,
            "expected_return": self.expected_return,
            "grad_year": self.grad_year,
            "is_active": self.is_active,
        }

class Event(db.Model):
    __tablename__ = "events"
    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    event_group_id = db.Column(db.Integer, db.ForeignKey("event_groups.event_group_id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)  # "100m", "Long Jump"
    event_type = db.Column(db.String(10), nullable=False)  # track/field/relay
    venue_type = db.Column(db.String(10), nullable=False, default="both")  # indoor/outdoor/both
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "event_group_id": self.event_group_id,
            "name": self.name,
            "event_type": self.event_type,
            "venue_type": self.venue_type,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
        }

class Meet(db.Model):
    __tablename__ = "meets"
    meet_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    org_id = db.Column(db.Integer, nullable=False, default=CURRENT_ORG_ID, index=True)

    name = db.Column(db.String(120), nullable=False)
    meet_date = db.Column(db.String(10), nullable=True)  # 'YYYY-MM-DD'
    location = db.Column(db.String(120), nullable=True)

    is_varsity = db.Column(db.Boolean, nullable=False, default=False)
    venue_type = db.Column(db.String(10), nullable=False, default="outdoor")  # indoor/outdoor
    is_archived = db.Column(db.Boolean, nullable=False, default=False)

    season_id = db.Column(db.Integer, db.ForeignKey("seasons.season_id"), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "meet_id": self.meet_id,
            "org_id": self.org_id,
            "name": self.name,
            "meet_date": self.meet_date,
            "location": self.location,
            "is_varsity": self.is_varsity,
            "venue_type": self.venue_type,
            "is_archived": self.is_archived,
            "notes": self.notes,
        }

class MeetEvent(db.Model):
    __tablename__ = "meet_events"
    meet_event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    meet_id = db.Column(db.Integer, db.ForeignKey("meets.meet_id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.event_id"), nullable=False, index=True)

    gender = db.Column(db.String(1), nullable=False)  # M/F
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    max_entries = db.Column(db.Integer, nullable=True)
    is_scored = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint("meet_id", "event_id", "gender", name="uq_meet_event"),
    )

    def to_dict(self):
        return {
            "meet_event_id": self.meet_event_id,
            "meet_id": self.meet_id,
            "event_id": self.event_id,
            "gender": self.gender,
            "sort_order": self.sort_order,
            "max_entries": self.max_entries,
            "is_scored": self.is_scored,
        }

class MeetEntry(db.Model):
    __tablename__ = "meet_entries"
    meet_entry_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    meet_event_id = db.Column(
        db.Integer,
        db.ForeignKey("meet_events.meet_event_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    athlete_id = db.Column(
        db.Integer,
        db.ForeignKey("athletes.athlete_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    entry_status = db.Column(db.String(12), nullable=False, default="entered")  # entered/scratched

    seed_time = db.Column(db.String(20), nullable=True)
    seed_mark = db.Column(db.String(20), nullable=True)
    heat = db.Column(db.Integer, nullable=True)
    lane = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("meet_event_id", "athlete_id", name="uq_meet_entry"),
    )

    def to_dict(self):
        return {
            "meet_entry_id": self.meet_entry_id,
            "meet_event_id": self.meet_event_id,
            "athlete_id": self.athlete_id,
            "entry_status": self.entry_status,
            "seed_time": self.seed_time,
            "seed_mark": self.seed_mark,
            "heat": self.heat,
            "lane": self.lane,
        }

class Season(db.Model):
    __tablename__ = "seasons"
    season_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)          # "2025 Outdoor"
    year = db.Column(db.Integer, nullable=False)             # 2025
    discipline = db.Column(db.String(20), nullable=False)    # "outdoor"/"indoor"/"xc"

def autopopulate_meet_events(meet: "Meet"):
    # optional: don't double-populate
    if MeetEvent.query.filter_by(meet_id=meet.meet_id).first():
        return

    q = Event.query.filter_by(is_active=True)

    venue = (meet.venue_type or "outdoor").strip().lower()
    if venue == "indoor":
        q = q.filter(Event.venue_type.in_(["indoor", "both"]))
    else:
        q = q.filter(Event.venue_type.in_(["outdoor", "both"]))

    events = q.order_by(Event.sort_order.asc()).all()

    to_add = []
    for gender in ("M", "F"):
        for ev in events:
            to_add.append(MeetEvent(
                meet_id=meet.meet_id,
                event_id=ev.event_id,
                gender=gender,
                sort_order=ev.sort_order,
                is_scored=True,
            ))

    db.session.add_all(to_add)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # ignore duplicates if it somehow runs twice
        return

def get_event_group_id(name: str) -> int:
    eg = EventGroup.query.filter_by(name=name).first()
    if not eg:
        eg = EventGroup(name=name)
        db.session.add(eg)
        db.session.flush()  # gets eg.event_group_id without commit
    return eg.event_group_id

@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.get("/")
def home():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/athletes")
def athletes_page():
    return send_from_directory(app.static_folder, "athletes.html")

@app.get("/meets")
def meets_page():
    return send_from_directory(app.static_folder, "meets.html")

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
        q = q.filter(Athlete.is_active == True)

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
    varsity = data.get("varsity", False)
    unavailable = data.get("unavailable", False)
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

    try:
        varsity = parse_bool(data.get("varsity"), default=False)
    except ValueError:
        return {"error": "varsity must be True/False"}, 400

    try:
        unavailable = parse_bool(data.get("unavailable"), default=False)
    except ValueError:
        return {"error": "unavailable must be True/False"}, 400

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
        varsity=varsity,
        first_name=first,
        last_name=last,
        gender=gender,
        unavailable=unavailable,
        expected_return=expected_return,
        grad_year=grad_year,
        is_active=True,
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
        "varsity",
        "first_name",
        "last_name",
        "gender",
        "unavailable",
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

        if k in {"varsity", "unavailable", "is_active"}:
            try:
                v = parse_bool(v)
            except ValueError:
                return {"error": f"{k} must be True or False"}, 400

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

# ------- meet apis ---------

@app.get("/api/meets")
def list_meets():
    meets = (Meet.query
             .filter_by(org_id=CURRENT_ORG_ID, is_archived=False)
             .order_by(Meet.meet_date.desc().nullslast(), Meet.meet_id.desc())
             .all())
    return jsonify([m.to_dict() for m in meets])

@app.post("/api/meets")
def create_meet():
    data = request.get_json(force=True) or {}
    m = Meet(
        org_id=CURRENT_ORG_ID,
        name=(data.get("name") or "New Meet").strip(),
        meet_date=data.get("meet_date"),
        location=data.get("location"),
        is_varsity=parse_bool(data.get("is_varsity"), False),
        venue_type=(data.get("venue_type") or "outdoor").strip().lower(),
        notes=(str(data.get("notes")).strip() or None) if data.get("notes") is not None else None,
    )
    db.session.add(m)
    db.session.commit()
    autopopulate_meet_events(m)
    return jsonify(m.to_dict()), 201

# ------ events -----
@app.get("/api/events")
def list_events():
    events = (Event.query
              .filter_by(is_active=True)
              .order_by(Event.sort_order.asc())
              .all())
    return jsonify([e.to_dict() for e in events])

# add events to meet
@app.post("/api/meets/<int:meet_id>/meet-events")
def add_meet_event(meet_id):
    data = request.get_json(force=True) or {}
    gender = (data.get("gender") or "").strip().upper()
    if gender not in {"M", "F"}:
        return jsonify({"error": "gender must be M or F"}), 400

    event_id = data.get("event_id")
    if not event_id:
        return jsonify({"error": "event_id required"}), 400

    me = MeetEvent(
        meet_id=meet_id,
        event_id=int(event_id),
        gender=gender,
        sort_order=int(data.get("sort_order") or 0),
    )
    db.session.add(me)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "event already added for this meet+gender (or invalid ids)"}), 400

    return jsonify(me.to_dict()), 201

@app.get("/api/meets/<int:meet_id>/page")
def meet_page_bootstrap(meet_id):
    gender = (request.args.get("gender") or "M").upper()
    if gender not in {"M", "F"}:
        return jsonify({"error": "gender must be M or F"}), 400

    meet = Meet.query.filter_by(meet_id=meet_id, org_id=CURRENT_ORG_ID).first_or_404()

    # meet events for tab
    meet_events = (db.session.query(MeetEvent, Event, EventGroup)
        .join(Event, MeetEvent.event_id == Event.event_id)
        .outerjoin(EventGroup, Event.event_group_id == EventGroup.event_group_id)
        .filter(MeetEvent.meet_id == meet_id, MeetEvent.gender == gender)
        .order_by(MeetEvent.sort_order.asc(), Event.sort_order.asc(), Event.name.asc())
        .all()
    )
    meet_event_ids = [me.meet_event_id for (me, e, g) in meet_events]

    # entries for those meet events
    entries = []
    if meet_event_ids:
        entries = (db.session.query(MeetEntry, Athlete)
            .join(Athlete, MeetEntry.athlete_id == Athlete.athlete_id)
            .filter(MeetEntry.meet_event_id.in_(meet_event_ids), Athlete.org_id == CURRENT_ORG_ID)
            .order_by(Athlete.last_name.asc(), Athlete.first_name.asc())
            .all()
        )

    entries_by_meet_event = {}
    for ent, ath in entries:
        entries_by_meet_event.setdefault(ent.meet_event_id, []).append({
            "athlete_id": ath.athlete_id,
            "first_name": ath.first_name,
            "last_name": ath.last_name,
            "gender": ath.gender,
            "unavailable": ath.unavailable,
        })


    # athlete list for right side (with names)
    ath_rows = (db.session.query(Athlete, Team, EventGroup)
        .outerjoin(Team, and_(Athlete.team_id == Team.team_id, Team.org_id == CURRENT_ORG_ID))
        .outerjoin(EventGroup, Athlete.event_group_id == EventGroup.event_group_id)
        .filter(
            Athlete.org_id == CURRENT_ORG_ID,
            Athlete.is_active == True,
            Athlete.gender == gender,
        )
        .order_by(EventGroup.sort_order.asc(), Athlete.last_name.asc(), Athlete.first_name.asc())
        .all()
    )

    payload_athletes = []
    for a, t, g in ath_rows:
        payload_athletes.append({
            **a.to_dict(),
            "team_name": (t.name if t else None),
            "event_group_name": (g.name if g else None),
        })


    payload_meet_events = []
    for me, ev, grp in meet_events:
        payload_meet_events.append({
            "meet_event_id": me.meet_event_id,
            "event_id": ev.event_id,
            "event_name": ev.name,
            "event_group": (grp.name if grp else None),
            "sort_order": me.sort_order,
            "entries": entries_by_meet_event.get(me.meet_event_id, []),
        })

    return jsonify({
        "meet": meet.to_dict(),
        "gender": gender,
        "meet_events": payload_meet_events,
        "athletes": payload_athletes,
    })


@app.post("/api/meet-events/<int:meet_event_id>/entries")
def add_entry(meet_event_id):
    data = request.get_json(force=True) or {}
    athlete_id = data.get("athlete_id")
    if not athlete_id:
        return jsonify({"error": "athlete_id required"}), 400

    me = MeetEvent.query.get_or_404(meet_event_id)
    ath = Athlete.query.filter_by(athlete_id=int(athlete_id), org_id=CURRENT_ORG_ID).first_or_404()

    if ath.gender != me.gender:
        return jsonify({"error": "athlete gender does not match event gender"}), 400

    entry = MeetEntry(meet_event_id=meet_event_id, athlete_id=ath.athlete_id)
    db.session.add(entry)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "athlete already entered in this event"}), 400

    return jsonify(entry.to_dict()), 201


@app.delete("/api/meet-events/<int:meet_event_id>/entries/<int:athlete_id>")
def remove_entry(meet_event_id, athlete_id):
    ent = MeetEntry.query.filter_by(meet_event_id=meet_event_id, athlete_id=athlete_id).first()
    if not ent:
        return jsonify({"ok": True})  # idempotent
    db.session.delete(ent)
    db.session.commit()
    return jsonify({"ok": True})

@app.patch("/api/meets/<int:meet_id>")
def patch_meet(meet_id):
    meet = Meet.query.filter_by(meet_id=meet_id, org_id=CURRENT_ORG_ID).first_or_404()
    data = request.get_json(force=True) or {}

    if "is_archived" in data:
        meet.is_archived = parse_bool(data.get("is_archived"), meet.is_archived)

    if "name" in data and data["name"] is not None:
        meet.name = str(data["name"]).strip() or meet.name

    if "is_varsity" in data:
        meet.is_varsity = parse_bool(data.get("is_varsity"), meet.is_varsity)

    if "venue_type" in data:
        meet.venue_type = (str(data["venue_type"]).strip() or None) if data["venue_type"] is not None else None

    if "meet_date" in data:
        meet.meet_date = (str(data["meet_date"]).strip() or None) if data["meet_date"] is not None else None

    if "location" in data:
        meet.location = (str(data["location"]).strip() or None) if data["location"] is not None else None

    if "season" in data:
        meet.season = (str(data["season"]).strip() or None) if data["season"] is not None else None

    if "notes" in data:
        meet.notes = (str(data["notes"]).strip() or None) if data["notes"] is not None else None
    db.session.commit()
    return jsonify(meet.to_dict())


@app.get("/api/debug/groups-and-events")
def debug_groups_and_events():
    rows = (db.session.query(EventGroup, Event)
        .join(Event, Event.event_group_id == EventGroup.event_group_id)
        .order_by(EventGroup.sort_order.asc(), Event.sort_order.asc(), Event.name.asc())
        .all()
    )
    out = []
    for g, e in rows:
        out.append({
            "group": g.name,
            "group_sort": g.sort_order,
            "event": e.name,
            "event_sort": e.sort_order,
        })
    return jsonify(out)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
