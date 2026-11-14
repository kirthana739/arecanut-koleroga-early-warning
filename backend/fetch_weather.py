import requests
import pandas as pd

LAT, LON = 12.56, 75.39  # Sullya, Karnataka

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": LAT,
    "longitude": LON,
    "hourly": "temperature_2m,relative_humidity_2m,precipitation",
    "past_days": 7,
    "forecast_days": 2,
    "timezone": "Asia/Kolkata",
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

df = pd.DataFrame(response.json()["hourly"])
df.to_csv("weather_sample.csv", index=False)

print(df.head())
print(f"Saved {len(df)} rows")