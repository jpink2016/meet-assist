from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from datetime import datetime

app = Flask(__name__, static_folder = "static") # static_url_path="/static")

# The database file will live in backend/movies.db
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///meet-assist.db")
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
