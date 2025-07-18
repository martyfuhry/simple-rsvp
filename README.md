# Simple RSVP App

A minimal, self-hosted RSVP form using Flask and JSON storage.

## Features

- Simple RSVP form (name, adults, kids, notes)
- Flat-file JSON storage
- Admin view with CSV export
- Runs with Docker Compose or locally with Python

## Setup

### With Docker

```bash
docker compose up
```

Then visit:

- `http://localhost:5000` — RSVP form
- `http://localhost:5000/admin?pw=letmein` — admin view
- `http://localhost:5000/export.csv?pw=letmein` — CSV export

### Locally

```bash
pip install flask
python app.py
```

## Customization

Change the password by setting the `ADMIN_PASSWORD` environment variable.
