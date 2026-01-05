from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='static')

@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.get("/athletes")
def athletes():
    return send_from_directory(app.static_folder, "athletes.html")

