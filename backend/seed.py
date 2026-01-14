# backend/seed.py
import os
from backend.app import (
    app, db,
    Organization, Team, EventGroup, Event, Athlete, Season,
    CURRENT_ORG_ID, CURRENT_ORG_NAME,
    get_event_group_id,
)

from sqlalchemy import and_

def seed_athletes():
    # Only seed if no athletes exist for this org
    if Athlete.query.filter_by(org_id=CURRENT_ORG_ID).count() > 0:
        return

    # Grab teams
    teams = Team.query.filter_by(org_id=CURRENT_ORG_ID).order_by(Team.team_id).all()
    varsity_team_id = teams[0].team_id if teams else 1
    jv_team_id = teams[1].team_id if len(teams) > 1 else varsity_team_id

    # Pick a default event group (required FK)
    sprints = EventGroup.query.filter_by(name="Sprints").first()
    event_group_id = sprints.event_group_id if sprints else 1

    athletes = [
        # ---- Males ----
        ("Liam", "Carter", "M", True,  varsity_team_id, 2026),
        ("Noah", "Reed",   "M", False, jv_team_id,      2027),
        ("Ethan","Brooks", "M", True,  varsity_team_id, 2025),
        ("Jack", "Miller", "M", False, jv_team_id,      2028),
        ("Owen", "Hayes",  "M", True,  varsity_team_id, 2026),

        # ---- Females ----
        ("Ava",  "Nguyen", "F", True,  varsity_team_id, 2026),
        ("Mia",  "Parker", "F", False, jv_team_id,      2027),
        ("Zoe",  "Johnson","F", True,  varsity_team_id, 2025),
        ("Ella", "Brown",  "F", False, jv_team_id,      2028),
        ("Lily", "Martinez","F", True, varsity_team_id, 2026),

        # ---- X ----
        ("Riley","Jordan", "X", False, jv_team_id,      2027),
    ]

    for first, last, gender, varsity, team_id, grad_year in athletes:
        db.session.add(Athlete(
            org_id=CURRENT_ORG_ID,
            team_id=team_id,
            event_group_id=event_group_id,
            varsity=varsity,
            first_name=first,
            last_name=last,
            gender=gender,
            unavailable=False,
            expected_return=None,
            grad_year=grad_year,
            is_active=True,
        ))

    db.session.commit()

def seed():
    seed_athletes()
    seasons = [
        {"name": "2024 Outdoor", "year": 2024, "discipline": "outdoor"},
        {"name": "2024 Indoor",  "year": 2024, "discipline": "indoor"},
        {"name": "2025 Outdoor", "year": 2025, "discipline": "outdoor"},
    ]

    for s in seasons:
        exists = (
            Season.query
            .filter_by(
                name=s["name"],
                year=s["year"],
                discipline=s["discipline"]
            )
            .first()
        )
        if not exists:
            db.session.add(Season(**s))

    db.session.commit()


    group_orders = {
        "Sprints": 10,
        "Hurdles": 20,
        "Mid Distance": 30,
        "Distance": 40,
        "Relays": 50,
        "Jumps": 60,
        "PV": 70,
        "Throws": 80,
        "Multi": 90,
    }

    # Seed current org
    org = Organization.query.filter_by(org_id=CURRENT_ORG_ID).first()
    if not org:
        db.session.add(Organization(org_id=CURRENT_ORG_ID, name=CURRENT_ORG_NAME))
        db.session.commit()

    # Seed teams
    if Team.query.filter_by(org_id=CURRENT_ORG_ID).count() == 0:
        for name in ["Varsity", "JV", "Freshman"]:
            db.session.add(Team(org_id=CURRENT_ORG_ID, name=name))
        db.session.commit()

    # Seed event groups
    if EventGroup.query.count() == 0:
        for name in ["Sprints", "Mid Distance", "Distance", "Throws", "Jumps", "PV", "Multi", "Relays", "Hurdles"]:
            db.session.add(EventGroup(name=name))
        db.session.commit()

    # Apply sort orders (idempotent)
    for name, order in group_orders.items():
        eg = EventGroup.query.filter_by(name=name).first()
        if eg:
            eg.sort_order = order
    db.session.commit()

    seed_demo = os.environ.get("SEED_DEMO_DATA", "1") == "1"
    if not seed_demo:
        return

    # ---- Seed events if enabled ----
    if os.environ.get("SEED_EVENTS", "0") == "1":
        def upsert_event(group_name, name, event_type, venue_type="both", sort_order=0):
            eg_id = get_event_group_id(group_name)
            existing = Event.query.filter_by(event_group_id=eg_id, name=name).first()
            if existing:
                existing.event_type = event_type
                existing.venue_type = venue_type
                existing.sort_order = sort_order
                existing.is_active = True
            else:
                db.session.add(Event(
                    event_group_id=eg_id,
                    name=name,
                    event_type=event_type,
                    venue_type=venue_type,
                    sort_order=sort_order,
                    is_active=True,
                ))
        upsert_event("Sprints", "100m", "track", "outdoor", 10)
        upsert_event("Sprints", "200m", "track", "both", 20)
        upsert_event("Sprints", "400m", "track", "both", 30)

        upsert_event("Hurdles", "110H/100H", "track", "outdoor", 40)
        upsert_event("Hurdles", "300H", "track", "outdoor", 50)

        upsert_event("Mid Distance", "800m", "track", "both", 60)
        upsert_event("Distance", "1600m", "track", "both", 70)
        upsert_event("Distance", "3200m", "track", "both", 80)

        upsert_event("Relays", "4x100", "relay", "outdoor", 90)
        upsert_event("Relays", "4x400", "relay", "outdoor", 100)
        upsert_event("Relays", "4x800", "relay", "outdoor", 110)

        upsert_event("Jumps", "Long Jump", "field", "both", 120)
        upsert_event("Jumps", "Triple Jump", "field", "both", 130)
        upsert_event("Jumps", "High Jump", "field", "both", 140)
        upsert_event("PV", "Pole Vault", "field", "both", 150)

        upsert_event("Throws", "Shot Put", "field", "both", 160)
        upsert_event("Throws", "Discus", "field", "outdoor", 170)
        db.session.commit()

if __name__ == "__main__":
    with app.app_context():   # ✅ this is the key
        seed()
    print("Seed complete.")
