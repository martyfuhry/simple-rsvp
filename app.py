
# Simple Flask RSVP App (Docker-ready)
# Stores RSVPs in a JSON file, has basic .htaccess-style admin view, and CSV export

from flask import Flask, request, render_template_string, redirect, url_for, Response
import json, os, csv
from functools import wraps

app = Flask(__name__)

DATA_FILE = "rsvps.json"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "letmein")

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

def load_rsvps():
    with open(DATA_FILE) as f:
        return json.load(f)

def save_rsvp(entry):
    data = load_rsvps()
    data.append(entry)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def check_auth(pw):
    return pw == ADMIN_PASSWORD

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        pw = request.args.get("pw")
        if not check_auth(pw):
            return "Unauthorized", 403
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return render_template_string("""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css"><title>RSVP</title></head><body><main class="container">
    <h2>RSVP Form</h2>
    <form action='/submit' method='post'>
        Name: <input name='name' required><br>
        Adults: <input name='adults' type='number' min='0' required><br>
        Kids: <input name='kids' type='number' min='0' required><br>
        Notes: <textarea name='notes'></textarea><br>
        <button type='submit'>Submit RSVP</button>
    </form>
    </main></body></html>""")

@app.route("/submit", methods=["POST"])
def submit():
    entry = {
        "name": request.form["name"],
        "adults": int(request.form["adults"]),
        "kids": int(request.form["kids"]),
        "notes": request.form.get("notes", "")
    }
    save_rsvp(entry)
    return "RSVP received. Thank you!"

@app.route("/admin")
@require_auth
def admin():
    data = load_rsvps()
    rows = "".join(
        f"<tr><td>{r['name']}</td><td>{r['adults']}</td><td>{r['kids']}</td><td>{r['notes']}</td></tr>"
        for r in data
    )
    return render_template_string(f"""
    <h2>Admin RSVP List</h2>
    <a href='/export.csv?pw={{request.args.get("pw")}}'>Download CSV</a>
    <table border=1>
        <tr><th>Name</th><th>Adults</th><th>Kids</th><th>Notes</th></tr>
        {rows}
    </table>
    </main></body></html>""")

@app.route("/export.csv")
@require_auth
def export_csv():
    data = load_rsvps()
    def generate():
        output = csv.StringIO()
        writer = csv.DictWriter(output, fieldnames=["name", "adults", "kids", "notes"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        return output.getvalue()
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=rsvps.csv"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
