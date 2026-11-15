"""Virtual ESP32: replays real monsoon weather to the API, one reading per simulated hour."""
import argparse
import time

import pandas as pd
import requests

API = "http://127.0.0.1:5000"

parser = argparse.ArgumentParser()
parser.add_argument("--end", required=True, help="last day to replay, e.g. 2026-07-15")
parser.add_argument("--hours", type=int, default=72, help="hours of data to send")
parser.add_argument("--delay", type=float, default=0.2, help="seconds between readings")
args = parser.parse_args()

df = pd.read_csv("weather_monsoon_2026.csv", parse_dates=["time"])
end = pd.Timestamp(args.end) + pd.Timedelta(hours=23)
window = df[df["time"] <= end].tail(args.hours)

print(f"Replaying {len(window)} hours ending {end}")

try:
    for row in window.itertuples():
        payload = {
            "device_id": "virtual-esp32-1",
            "time": row.time.isoformat(),
            "temperature": row.temperature_2m,
            "humidity": row.relative_humidity_2m,
            "rain_mm": row.precipitation,
        }
        r = requests.post(f"{API}/readings", json=payload, timeout=10)
        r.raise_for_status()
        print(f"{payload['time']}  {row.temperature_2m} C  {row.relative_humidity_2m}%  {row.precipitation} mm")
        time.sleep(args.delay)

    print("\nCurrent risk from the API:")
    print(requests.get(f"{API}/risk", timeout=10).json())

except requests.exceptions.ConnectionError:
    print("Could not reach the API. Is `python app.py` running in the other terminal?")