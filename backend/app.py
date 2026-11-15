import sqlite3
from datetime import datetime, timedelta

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from alerts import send_alert
from risk import WINDOW_HOURS, calculate_risk, should_alert

app = Flask(__name__)
DB = "readings.db"


def query(sql, args=(), commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, args)
        rows = cur.fetchall()
        if commit:
            conn.commit()
        return rows
    finally:
        conn.close()


def init_db():
    query(
        """CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            time TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            rain_mm REAL NOT NULL
        )""",
        commit=True,
    )
    query(
        "CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
        commit=True,
    )


def get_state(key, default):
    rows = query("SELECT value FROM state WHERE key = ?", (key,))
    return rows[0]["value"] if rows else default


def set_state(key, value):
    query(
        "INSERT INTO state (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
        commit=True,
    )


def compute_risk():
    rows = query(
        "SELECT time, temperature, humidity, rain_mm FROM readings "
        "ORDER BY time DESC LIMIT 2000"
    )
    if not rows:
        return {"level": "No data", "hours_of_data": 0}

    df = pd.DataFrame([dict(r) for r in rows])
    df["time"] = pd.to_datetime(df["time"])
    df = df[df["time"] > df["time"].max() - timedelta(hours=WINDOW_HOURS)]

    # Readings arrive every few minutes; the risk model expects hourly rows.
    hourly = (
        df.set_index("time")
        .resample("h")
        .agg({"temperature": "mean", "humidity": "mean", "rain_mm": "sum"})
        .dropna(subset=["temperature"])
        .rename(columns={
            "temperature": "temperature_2m",
            "humidity": "relative_humidity_2m",
            "rain_mm": "precipitation",
        })
    )

    if len(hourly) < 24:
        return {"level": "Not enough data", "hours_of_data": len(hourly)}

    result = calculate_risk(hourly)
    result["hours_of_data"] = len(hourly)
    result["as_of"] = str(hourly.index.max())
    return result


def check_alert():
    """Send one alert when risk rises to High; stay quiet while it stays High."""
    result = compute_risk()
    level = result["level"]
    if level not in ("Low", "Medium", "High"):
        return
    previous = get_state("last_level", "Low")
    if should_alert(previous, level):
        send_alert(
            f"High Koleroga risk (as of {result['as_of']}). "
            f"Last 48 h: {result['rain_hrs']} hours of rain, "
            f"{result['hum95_hrs']} hours at 95%+ humidity, {result['rain_mm']} mm rain. "
            "Check your plantation and ask your local KVK about preventive measures."
        )
    set_state("last_level", level)


@app.get("/")
def home():
    return jsonify(
        name="Koleroga Early-Warning API",
        endpoints=["POST /readings", "GET /readings", "GET /risk"],
    )


@app.post("/readings")
def add_reading():
    data = request.get_json(silent=True) or {}
    try:
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        rain_mm = float(data["rain_mm"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="temperature, humidity and rain_mm must be numbers"), 400

    if not 0 <= humidity <= 100 or rain_mm < 0:
        return jsonify(error="humidity must be 0-100 and rain_mm must be >= 0"), 400

    time = data.get("time") or datetime.now().isoformat(timespec="seconds")
    try:
        datetime.fromisoformat(time)
    except ValueError:
        return jsonify(error="time must be ISO format, e.g. 2026-11-16T10:30:00"), 400

    device_id = str(data.get("device_id", "device-1"))
    query(
        "INSERT INTO readings (device_id, time, temperature, humidity, rain_mm) "
        "VALUES (?, ?, ?, ?, ?)",
        (device_id, time, temperature, humidity, rain_mm),
        commit=True,
    )

    try:
        check_alert()
    except Exception as e:  # an alert problem must never lose a reading
        print("Alert check failed:", e)

    return jsonify(status="saved"), 201


@app.get("/readings")
def list_readings():
    limit = min(request.args.get("limit", default=50, type=int), 1000)
    rows = query("SELECT * FROM readings ORDER BY time DESC LIMIT ?", (limit,))
    return jsonify([dict(r) for r in rows])


@app.get("/dashboard")
def dashboard():
    return send_from_directory("../dashboard", "index.html")


@app.get("/risk")
def current_risk():
    return jsonify(compute_risk())


init_db()

if __name__ == "__main__":
    app.run(debug=True)

