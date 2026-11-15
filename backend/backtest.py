import requests
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from risk import calculate_risk, WINDOW_HOURS

LAT, LON = 12.56, 75.39  # Sullya, Karnataka

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": LAT,
    "longitude": LON,
    "start_date": "2026-06-01",
    "end_date": "2026-09-30",
    "hourly": "temperature_2m,relative_humidity_2m,precipitation",
    "timezone": "Asia/Kolkata",
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()

df = pd.DataFrame(response.json()["hourly"])
df["time"] = pd.to_datetime(df["time"])
df.to_csv("weather_monsoon_2026.csv", index=False)

rows = []
for day in pd.date_range("2026-06-03", "2026-09-30"):
    end = day + pd.Timedelta(hours=23)
    start = end - pd.Timedelta(hours=WINDOW_HOURS)
    window = df[(df["time"] > start) & (df["time"] <= end)]
    result = calculate_risk(window)
    result["date"] = day
    rows.append(result)

res = pd.DataFrame(rows)
res["alert"] = (res["level"] == "High") & (res["level"].shift(1) != "High")
res.to_csv("risk_results_2026.csv", index=False)

print("Alerts sent:", int(res["alert"].sum()))
print(res["level"].value_counts())

colors = {"Low": "#97C459", "Medium": "#EF9F27", "High": "#E24B4A"}
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
ax1.bar(res["date"], res["rain_mm"], color="#378ADD")
ax1.set_ylabel("Rain in last 48 h (mm)")
ax2.bar(res["date"], res["score"], color=[colors[l] for l in res["level"]])
ax2.set_ylabel("Risk score (0-6)")
ax2.set_xlabel("Date (monsoon 2026)")
fig.suptitle("Koleroga risk score vs rainfall, Sullya, June-Sept 2026")
plt.tight_layout()
plt.savefig("../docs/risk_chart.png", dpi=150)
print("Saved ../docs/risk_chart.png")