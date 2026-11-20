"""
Collector: fetches Seri Iskandar weather from Open-Meteo and saves it to Supabase.
Owner: Member A. Runs twice an hour via GitHub Actions.
Every run also refills any missing hour since collection began (Day 0),
because GitHub sometimes delays or skips scheduled runs for hours.
"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from supabase import create_client

LAT, LON = 4.36, 100.97                 # Seri Iskandar, Perak
TZ = ZoneInfo("Asia/Kuala_Lumpur")
MAX_HORIZON = 72                        # save forecasts up to 72 hours ahead
START = datetime(2026, 10, 25, 16, 0, tzinfo=TZ)   # Day 0: first hour of collection
PAST_DAYS = 35                          # how far back to look for missing hours
VARIABLES = ["temperature_2m", "relative_humidity_2m", "precipitation",
             "precipitation_probability", "wind_speed_10m"]


def fetch_weather():
    """Ask Open-Meteo for recent past hours and the next 4 days, hour by hour."""
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ",".join(VARIABLES),
        "timezone": "Asia/Kuala_Lumpur",
        "past_days": PAST_DAYS,
        "forecast_days": 4,
    }
    response = requests.get("https://api.open-meteo.com/v1/forecast",
                            params=params, timeout=60)
    response.raise_for_status()          # stop with an error if the request failed
    return response.json()["hourly"]


def main():
    hourly = fetch_weather()
    issued_at = datetime.now(TZ).replace(minute=0, second=0, microsecond=0)

    observations = []
    forecasts = []

    for i, time_text in enumerate(hourly["time"]):
        target_time = datetime.fromisoformat(time_text).replace(tzinfo=TZ)
        values = {
            "temperature": hourly["temperature_2m"][i],
            "humidity": hourly["relative_humidity_2m"][i],
            "precipitation": hourly["precipitation"][i],
            "wind_speed": hourly["wind_speed_10m"][i],
        }

        # Every hour from Day 0 up to now is an observation
        if START <= target_time <= issued_at:
            observations.append({"obs_time": target_time.isoformat(), **values})

        # Future hours (1 to 72 hours ahead) are forecasts
        horizon = int((target_time - issued_at).total_seconds() // 3600)
        if 1 <= horizon <= MAX_HORIZON:
            forecasts.append({
                "issued_at": issued_at.isoformat(),
                "target_time": target_time.isoformat(),
                "horizon_hours": horizon,
                "precip_probability": hourly["precipitation_probability"][i],
                **values,
            })

    if not any(o["obs_time"] == issued_at.isoformat() for o in observations):
        raise RuntimeError(f"No observation found for {issued_at}")

    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

    # ignore_duplicates: hours already saved stay as they are; only missing hours are added
    db.table("observations").upsert(observations, on_conflict="obs_time",
                                    ignore_duplicates=True).execute()
    db.table("forecasts").upsert(forecasts, on_conflict="issued_at,target_time").execute()

    print(f"Checked {len(observations)} hours since Day 0 and saved {len(forecasts)} forecasts "
          f"for {issued_at:%Y-%m-%d %H:%M} (Malaysia time)")


if __name__ == "__main__":
    main()
