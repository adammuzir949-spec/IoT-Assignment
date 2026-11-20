"""Daily health check: finds missing hours and saves a CSV backup. Owner: Member D."""
import csv
import os
import sys
from datetime import datetime, timedelta, timezone

from supabase import create_client

MYT = timezone(timedelta(hours=8))
db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def fetch_all(table):
    """Read a whole table, 1,000 rows at a time."""
    rows, start = [], 0
    while True:
        part = db.table(table).select("*").order("id").range(start, start + 999).execute().data
        rows += part
        if len(part) < 1000:
            return rows
        start += 1000


obs = fetch_all("observations")
fc = fetch_all("forecasts")
if not obs:
    sys.exit("No observations found")

# Find missing hours between the first and latest observation
times = {datetime.fromisoformat(r["obs_time"]) for r in obs}
first, last = min(times), max(times)
expected, t = set(), first
while t <= last:
    expected.add(t)
    t += timedelta(hours=1)
missing = sorted(expected - times)
stale = datetime.now(timezone.utc) - last > timedelta(hours=2)

# Save CSV backups
os.makedirs("backup", exist_ok=True)
for name, rows in [("observations", obs), ("forecasts", fc)]:
    if rows:
        with open(f"backup/{name}.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

# Write the report
lines = [
    f"- Hours collected: {len(obs)}",
    f"- Forecast rows: {len(fc)}",
    f"- First hour: {first.astimezone(MYT):%Y-%m-%d %H:%M} (Malaysia time)",
    f"- Latest hour: {last.astimezone(MYT):%Y-%m-%d %H:%M} (Malaysia time)",
    f"- Missing hours: {len(missing)}",
]
lines += [f"    - {m.astimezone(MYT):%Y-%m-%d %H:%M}" for m in missing]
if stale:
    lines.append("- WARNING: no new observation in the last 2 hours")
report = "\n".join(lines)
print(report)

summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_file:
    with open(summary_file, "a") as f:
        f.write("## Data health check\n\n" + report + "\n")

if missing or stale:
    sys.exit(1)   # marks the run as failed, so D gets an email
