import os
import numpy as np
import pandas as pd
from supabase import create_client

db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])


def load(table):
    """Read a whole table, 1,000 rows at a time."""
    rows, start = [], 0
    while True:
        part = db.table(table).select("*").order("id").range(start, start + 999).execute().data
        rows += part
        if len(part) < 1000:
            return pd.DataFrame(rows)
        start += 1000


obs = load("observations")
fc = load("forecasts")
print(f"{len(obs)} observations, {len(fc)} forecasts")

# Match each forecast to the actual weather for the same hour
obs["obs_time"] = pd.to_datetime(obs["obs_time"], utc=True).dt.floor("h")
fc["target_time"] = pd.to_datetime(fc["target_time"], utc=True).dt.floor("h")
pairs = fc.merge(obs, left_on="target_time", right_on="obs_time", suffixes=("_fc", "_obs"))
pairs["horizon_band"] = pd.cut(pairs["horizon_hours"], bins=[0, 24, 48, 72],
                               labels=["0-24h", "24-48h", "48-72h"])
print(f"{len(pairs)} forecast-actual pairs")

# MAE, RMSE and bias for each variable and horizon band
rows = []
for band, g in pairs.groupby("horizon_band", observed=True):
    for v in ["temperature", "humidity", "wind_speed", "precipitation"]:
        err = g[f"{v}_fc"] - g[f"{v}_obs"]
        rows.append({"horizon": band, "variable": v, "pairs": err.count(),
                     "MAE": err.abs().mean(), "RMSE": np.sqrt((err ** 2).mean()),
                     "bias": err.mean()})
metrics = pd.DataFrame(rows).round(2)
print(metrics)

# Rain yes/no: an hour counts as rainy at 0.1 mm or more
RAIN = 0.1
rain_rows = []
for band, g in pairs.groupby("horizon_band", observed=True):
    f = g["precipitation_fc"] >= RAIN
    o = g["precipitation_obs"] >= RAIN
    hits, misses = int((f & o).sum()), int((~f & o).sum())
    false_alarms, correct_dry = int((f & ~o).sum()), int((~f & ~o).sum())
    rain_rows.append({
        "horizon": band, "hits": hits, "misses": misses,
        "false_alarms": false_alarms, "correct_dry": correct_dry,
        "hit_rate": hits / (hits + misses) if hits + misses else np.nan,
        "false_alarm_ratio": false_alarms / (hits + false_alarms) if hits + false_alarms else np.nan,
        "accuracy": (hits + correct_dry) / len(g),
    })
rain = pd.DataFrame(rain_rows).round(2)
print(rain)

metrics.to_csv("metrics.csv", index=False)
rain.to_csv("rain_metrics.csv", index=False)
