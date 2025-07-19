# Simple Flask RSVP App (Docker-ready)
# Stores RSVPs in a JSON file, editable event metadata, and CSV export

from flask import Flask, request, render_template_string, redirect, url_for, Response, send_from_directory
import json, os, csv
import html
from functools import wraps
from datetime import datetime, date
from PIL import Image

app = Flask(__name__)

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "rsvps.json")
EVENT_FILE = os.path.join(DATA_DIR, "event.json")

os.makedirs(DATA_DIR, exist_ok=True)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "letmein")

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

if not os.path.exists(EVENT_FILE):
    default_event = {
        "title": "Feast of the Assumption",
        "datetime": "2025-08-16T17:00:00",
        "location": "The Fuhry Homestead, Vienna, OH",
        "description": "Join us for food, fun, music, games, and a sunset bonfire. Bring a side dish if you'd like!",
        "active": True
    }
    with open(EVENT_FILE, 'w') as f:
        json.dump(default_event, f, indent=2)

def load_event():
    if not os.path.exists(EVENT_FILE):
        return None
    with open(EVENT_FILE) as f:
        return json.load(f)

def save_event(data):
    with open(EVENT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_rsvps():
    with open(DATA_FILE) as f:
        return json.load(f)

def save_rsvps(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def save_rsvp(entry):
    data = load_rsvps()
    data.append(entry)
    save_rsvps(data)

def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != "admin" or auth.password != ADMIN_PASSWORD:
            return Response(
                "Login required", 401,
                {"WWW-Authenticate": "Basic realm='RSVP Admin'"}
            )
        return f(*args, **kwargs)
    return decorated

def format_event_datetime(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%A, %B %d, %Y"), dt.strftime("%-I:%M %p")
    except:
        return "Invalid date", "Invalid time"

def find_cover_image():
    for ext in ["png", "jpg", "jpeg", "webp"]:
        path = f"cover.{ext}"
        if os.path.exists(f"static/{path}"):
            return path
    return None


@app.route("/upload", methods=["POST"])
@basic_auth_required
def upload_cover():
    file = request.files.get("cover")
    if file and file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        ext = file.filename.rsplit(".", 1)[-1].lower()
        img = Image.open(file.stream)
        img.thumbnail((1600, 900))
        os.makedirs("static", exist_ok=True)
        img.save(f"static/cover.{ext}")

        # Remove any other cover.* files in static/
        for other_ext in ["png", "jpg", "jpeg", "webp"]:
            if other_ext != ext:
                try:
                    os.remove(f"static/cover.{other_ext}")
                except FileNotFoundError:
                    pass

        return redirect("/admin")
    return "Invalid file", 400

@app.route("/export.csv")
@basic_auth_required
def export_csv():
    data = load_rsvps()

    def generate():
        yield "Name,Adults,Kids,Notes\n"
        for r in data:
            row = f"{r['name']},{r['adults']},{r['kids']},{r['notes'].replace(',', ';')}\n"
            yield row

    return Response(generate(), mimetype="text/csv", headers={
        "Content-Disposition": "attachment; filename=rsvps.csv"
    })

@app.route("/edit-rsvp", methods=["POST"])
@basic_auth_required
def edit_rsvp():
    index = int(request.form["index"])
    data = load_rsvps()
    if "delete" in request.form:
        data.pop(index)
    else:
        data[index] = {
            "name": request.form["name"],
            "adults": int(request.form["adults"]),
            "kids": int(request.form["kids"]),
            "notes": request.form.get("notes", "")
        }
    save_rsvps(data)
    return redirect("/admin")


@app.route("/admin/edit")
@basic_auth_required
def admin_edit():
    data = load_rsvps()
    total_adults = sum(int(r.get('adults', 0)) for r in data)
    total_kids = sum(int(r.get('kids', 0)) for r in data)
    total_guests = total_adults + total_kids

    rows = "".join(
        f"""
        <form method='post' action='/edit-rsvp' style='border: 1px solid #333; padding: 1em; border-radius: 8px; background: #111;'>
          <input type='hidden' name='index' value='{i}'>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1em; max-width: 700px;">
            <label>Name<input name='name' value='{html.escape(r['name'])}'></label>
            <label>Notes<input name='notes' value='{html.escape(r['notes'])}'></label>
            <label>Adults<input type='number' name='adults' value='{r['adults']}' min='0'></label>
            <label>Kids<input type='number' name='kids' value='{r['kids']}' min='0'></label>
          </div>

            <div class="grid" style="grid-template-columns: auto auto; justify-content: end; gap: 0.5em;">
              <button type="submit" class="primary">Save</button>
              <button type="button" class="secondary" style="background-color: #900;" onclick="this.nextElementSibling.style.display='inline'; this.style.display='none';">Delete</button>
              <button type="submit" name="delete" value="1" class="secondary" style="background-color: #900; display: none;">Confirm?</button>
            </div>
        </form>
        """
        for i, r in enumerate(data)
    )

    return render_template_string(f"""<!doctype html>
    <html lang='en'>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
      <title>Edit RSVPs</title>
    </head>
    <body>
      <main class="container">
        <h1>Edit RSVP List</h1>
        <p><strong>{total_guests} total guests</strong> ({total_kids} kids, {total_adults} adults)</p>
        <a href='/admin'>← Back to Admin</a>
        <div style="display: flex; flex-direction: column; gap: 1.5em; margin-top: 2em; max-width: 900px; margin-left: auto; margin-right: auto;">
          {rows}
        </div>
      </main>
    </body>
    </html>""")

@app.route("/admin")
@basic_auth_required
def admin():
    event = load_event()
    data = load_rsvps()
    total_adults = sum(int(r.get('adults', 0)) for r in data)
    total_kids = sum(int(r.get('kids', 0)) for r in data)
    total_guests = total_adults + total_kids

    rows = "".join(
        f"<tr><td>{html.escape(r['name'])}</td>"
        f"<td>{r['adults']}</td>"
        f"<td>{r['kids']}</td>"
        f"<td>{html.escape(r['notes'])}</td></tr>"
        for r in data
    )

    return render_template_string(f"""<!doctype html><html lang='en'>
    <head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
    <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
    <title>Admin</title></head><body><main class="container">
    <h1>{event['title']}</h1>
    <p><strong>Date:</strong> {event['datetime']}<br>
    <strong>Location:</strong> {event['location']}</p>
    <p>{event['description']}</p>

    <hr>
    <h2>RSVP List</h2>
    <p><strong>{total_guests} total guests</strong> ({total_kids} kids, {total_adults} adults)</p>
    <a href='/export.csv'>Download CSV</a> | <a href='/admin/edit'>✏️ Edit RSVPs</a>
    <table>
      <thead><tr><th>Name</th><th>Adults</th><th>Kids</th><th>Notes</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>

    <hr>
    <h2>Edit Event Info</h2>
    <form action="/update-event" method="post">
      <label>Title: <input name="title" value="{event['title']}" required></label>
      <label>Date & Time: <input name="datetime" type="datetime-local" value="{event['datetime'][:16]}" required></label>
      <label>Location: <input name="location" value="{event['location']}" required></label>
      <label>Description: <textarea name="description" required>{event['description']}</textarea></label>
      <label>
        <input type="checkbox" name="active" {'checked' if event.get('active', True) else ''}>
        Event is active
      </label>
      <button type="submit">Save Event Info</button>
    </form>

    <hr>
    <h2>Upload New Cover Image</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
      <input type="file" name="cover" accept="image/*" required>
      <button type="submit">Upload</button>
    </form>
    </main></body></html>""")

@app.route("/update-event", methods=["POST"])
@basic_auth_required
def update_event():
    new_data = {
        "title": request.form["title"],
        "datetime": request.form["datetime"],
        "location": request.form["location"],
        "description": request.form["description"],
        "active": request.form.get("active") == "on"
    }
    save_event(new_data)
    return redirect("/admin")

def safe_int(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0

@app.route("/rsvp", methods=["POST"])
def rsvp():
    entry = {
        "name": request.form['name'],
        "adults": safe_int(request.form.get('adults', 1)),
        "kids": safe_int(request.form.get('kids', 0)),
        "notes": request.form.get('notes', '')
    }
    save_rsvp(entry)
    event = load_event()
    formatted_date, formatted_time = format_event_datetime(event['datetime']) if event else "soon"
    return render_template_string(f"""
    <!doctype html>
    <html lang='en'>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <link rel='stylesheet' href='https://unpkg.com/@picocss/pico@latest/css/pico.min.css'>
      <title>RSVP Confirmation</title>
    </head>
    <body>
      <main class='container' style='text-align: center; padding-top: 4em;'>
        <h1>Thank you for the RSVP!</h1>
        <p style='font-size: 1.2em; margin-top: 1em;'>See you {formatted_date} at {formatted_time}.</p>
      </main>
    </body>
    </html>
    """)

@app.route("/")
def home():
    event = load_event()
    if not event or not event.get("active", True):
        return render_template_string("""
        <main class='container'>
          <h1 style='text-align: center'>No Upcoming Event</h1>
          <p style='text-align: center'>Check back later for updates!</p>
        </main>
        """)
    cover = find_cover_image()
    event_date = datetime.fromisoformat(event['datetime'])
    days_remaining = (event_date.date() - date.today()).days
    formatted_date, formatted_time = format_event_datetime(event['datetime'])
    countdown = "Today!" if days_remaining == 0 else (f"{days_remaining} days to go")
    is_past = days_remaining < 0

    return render_template_string(f"""
    <!doctype html><html lang='en'>
    <head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
    <link rel='stylesheet' href='https://unpkg.com/@picocss/pico@latest/css/pico.min.css'>
    <title>{event['title']}</title></head>
    <body><main class='container'>
      <h1 style='text-align: center'>{event['title']}</h1>
      {f'<div style="margin: 2em 0; text-align: center;"><img src="/static/{cover}" style="max-height: 400px; width: auto; border-radius: 12px;"></div>' if cover else ''}
      <h3 style='text-align: center'>{formatted_date}</h3>
      <h4 style='text-align: center'>Join us at {formatted_time}</h4>
      <h4 style='text-align: center'>{event['location']}</h4>
      <p style='text-align: center; margin-top: -0.5em'>
        <a href='https://www.google.com/maps/search/?api=1&query={event['location'].replace(' ', '+')}' target='_blank' style='font-size: 0.9em;'>📍 View on Google Maps</a>
      </p>
      <p style='text-align:center;font-weight: bold'>{countdown}</p>
      <p style='margin-top: 2em'>{event['description']}</p>
      {'' if is_past else '''
      <h2 style='text-align: center'>Please RSVP</h2>
      <form method="post" action="/rsvp">
        <label>Name<input name="name" required></label>
        <div style="display: flex; gap: 1em">
          <label style="flex:1">Adults<input type="number" name="adults" value="1" min="0"></label>
          <label style="flex:1">Kids<input type="number" name="kids" value="0" min="0"></label>
        </div>
        <label>Notes<input name="notes"></label>
        <button type="submit">Submit RSVP</button>
      </form>
      ''' if not is_past else '<h2 style="text-align: center">Thanks for coming!</h2>'}
    </main></body></html>
    """)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 3022))
    app.run(debug=True, host="0.0.0.0", port=port)
