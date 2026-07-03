# FuturePath Assignment 2

FuturePath is a nonprofit education-event website built with Flask and SQLite. It upgrades the Assignment 1 static prototype into a database-backed application with search, score matching, authentication, comments, event ownership and bookings. Teacher accounts also have a Manage Events workspace for reviewing, editing, cancelling and safely deleting their own events. Permanent deletion is limited to events without bookings or comments so participant history remains intact.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Open `http://127.0.0.1:5000/`.

## Demonstration accounts

- Teacher: `frank@example.com` / `FuturePath123!`
- Teacher: `chen@example.com` / `FuturePath123!`
- Student: `student@example.com` / `FuturePath123!`

The included `futurepath/database.sqlite` contains test users, categories, Open, Sold Out, Inactive and Cancelled events, comments and booking history.

## Automated tests

```bash
python -m unittest discover -v
```

The tests use a temporary SQLite database and do not modify the submitted demonstration database.
