import pandas as pd

# Placeholder thresholds. Verify them with a KVK officer or farmer later.
HUMIDITY_WET = 90        # % humidity counted as "wet"
WINDOW_HOURS = 48        # look back this many hours
TEMP_RANGE = (20, 26)    # C, cool weather favors the disease


def calculate_risk(window: pd.DataFrame) -> dict:
    """Score the last 48 hours of weather and return a risk level."""
    wet = (window["relative_humidity_2m"] >= HUMIDITY_WET) | (window["precipitation"] > 0)
    wet_hours = int(wet.sum())
    rain_mm = float(window["precipitation"].sum())
    avg_temp = float(window["temperature_2m"].mean())

    score = 0
    if wet_hours >= 36:
        score += 2
    elif wet_hours >= 24:
        score += 1

    if rain_mm >= 50:
        score += 2
    elif rain_mm >= 20:
        score += 1

    if TEMP_RANGE[0] <= avg_temp <= TEMP_RANGE[1]:
        score += 1

    if score >= 4:
        level = "High"
    elif score >= 2:
        level = "Medium"
    else:
        level = "Low"

    return {
        "level": level,
        "score": score,
        "wet_hours": wet_hours,
        "rain_mm": round(rain_mm, 1),
        "avg_temp": round(avg_temp, 1),
    }


if __name__ == "__main__":
    df = pd.read_csv("weather_sample.csv", parse_dates=["time"])
    df = df[df["time"] <= pd.Timestamp.now()]   # ignore forecast hours
    latest = df.tail(WINDOW_HOURS)
    print(calculate_risk(latest))