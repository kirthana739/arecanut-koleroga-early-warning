import pandas as pd

WINDOW_HOURS = 48

# Thresholds chosen from the 2026 monsoon data (about the 50th and 75th percentile).
# (1 point at the first value, 2 points at the second.)
# TODO: validate with a KVK officer or farmer.
RAIN_HRS = (27, 37)    # hours with rain >= 0.2 mm in the window
HUM95_HRS = (32, 36)   # hours with humidity >= 95%
RAIN_MM = (31, 52)     # total rain in the window (mm)

HIGH_SCORE = 5         # out of 6
MEDIUM_SCORE = 3


def _points(value, limits):
    low, high = limits
    if value >= high:
        return 2
    if value >= low:
        return 1
    return 0


def calculate_risk(window: pd.DataFrame) -> dict:
    """Score the last 48 hours of weather (0-6) and return a risk level."""
    rain_hrs = int((window["precipitation"] >= 0.2).sum())
    hum95_hrs = int((window["relative_humidity_2m"] >= 95).sum())
    rain_mm = float(window["precipitation"].sum())
    avg_temp = float(window["temperature_2m"].mean())

    score = (
        _points(rain_hrs, RAIN_HRS)
        + _points(hum95_hrs, HUM95_HRS)
        + _points(rain_mm, RAIN_MM)
    )

    if score >= HIGH_SCORE:
        level = "High"
    elif score >= MEDIUM_SCORE:
        level = "Medium"
    else:
        level = "Low"

    return {
        "level": level,
        "score": score,
        "rain_hrs": rain_hrs,
        "hum95_hrs": hum95_hrs,
        "rain_mm": round(rain_mm, 1),
        "avg_temp": round(avg_temp, 1),
    }


def should_alert(previous_level: str, level: str) -> bool:
    """Alert only when risk rises to High, not on every High day."""
    return level == "High" and previous_level != "High"


if __name__ == "__main__":
    df = pd.read_csv("weather_sample.csv", parse_dates=["time"])
    df = df[df["time"] <= pd.Timestamp.now()]   # ignore forecast hours
    print(calculate_risk(df.tail(WINDOW_HOURS)))