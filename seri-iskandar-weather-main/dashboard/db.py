"""Seri Iskandar Weather Monitor dashboard. Owner: Member C."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(page_title="Seri Iskandar Weather Monitor", page_icon="🌦️", layout="wide")

MYT = "Asia/Kuala_Lumpur"
RAIN_MM = 0.1                       # an hour counts as rainy at 0.1 mm or more
VARS = {
    "temperature":   {"label": "Temperature", "unit": "°C",   "icon": "🌡️", "color": "#F28C28", "scale": "YlOrRd"},
    "humidity":      {"label": "Humidity",    "unit": "%",    "icon": "💧", "color": "#2A9DD8", "scale": "Blues"},
    "precipitation": {"label": "Rainfall",    "unit": "mm",   "icon": "🌧️", "color": "#3A5BA9", "scale": "Blues"},
    "wind_speed":    {"label": "Wind speed",  "unit": "km/h", "icon": "🍃", "color": "#3E9B5F", "scale": "Greens"},
}
INK, MUTED, GRID = "#13293D", "#5B7083", "#E3EBF2"
CHART_CFG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}
FORECAST = "#8E6CC9"

# ---------- Look and feel ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
html, body, .stApp, [class*="css"] {font-family: 'Plus Jakarta Sans', sans-serif;}
.stApp {background: linear-gradient(180deg, #E4F1FA 0%, #F6F9FC 360px);}
.block-container {padding-top: 1.4rem; max-width: 1320px;}
.hero {background: linear-gradient(120deg, #0E3B55 0%, #1C6E8C 55%, #45A9DA 100%);
  border-radius: 22px; padding: 26px 30px; color: #fff; position: relative; overflow: hidden;
  box-shadow: 0 14px 34px rgba(14,59,85,.28); margin-bottom: 18px;}
.hero h1 {color: #fff; font-weight: 800; font-size: 2.1rem; margin: 0 0 4px; padding: 0;}
.hero p {margin: 0; opacity: .9; font-size: .98rem;}
.hero .art {position: absolute; right: 26px; top: 6px; font-size: 6.5rem; opacity: .22;}
.pill {display: inline-block; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.35);
  border-radius: 999px; padding: 4px 12px; font-size: .8rem; margin: 14px 8px 0 0;}
.dot {display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #7CF29A;
  margin-right: 6px; box-shadow: 0 0 8px #7CF29A;}
.card {background: #fff; border-radius: 18px; padding: 16px 20px; border-top: 5px solid var(--c);
  box-shadow: 0 6px 18px rgba(19,41,61,.08); margin-bottom: 16px;}
.card .lbl {color: #5B7083; font-size: .85rem; font-weight: 700;}
.card .val {font-size: 2rem; font-weight: 800; color: #13293D; line-height: 1.25;}
.card .val span {font-size: 1rem; color: #5B7083; font-weight: 600;}
.card .delta {font-size: .8rem; color: #5B7083; margin-top: 2px;}
.card .delta b {color: var(--c);}
.alert {border-radius: 16px; padding: 14px 18px; font-weight: 600; margin: 18px 0 8px;}
.alert.rain {background: #E2ECFA; border-left: 6px solid #3A5BA9; color: #1B3A6B;}
.alert.dry {background: #FFF3E3; border-left: 6px solid #F28C28; color: #7A4A12;}
.section {font-weight: 800; font-size: 1.2rem; color: #13293D; margin: 14px 0 2px;}
.sub {color: #5B7083; font-size: .9rem; margin-bottom: 8px;}
.stat {background: #fff; border-radius: 14px; padding: 12px 16px; box-shadow: 0 4px 14px rgba(19,41,61,.06);
  margin-bottom: 16px;}
.stat .k {color: #5B7083; font-size: .8rem; font-weight: 700;}
.stat .v {color: #13293D; font-size: 1.35rem; font-weight: 800;}
div[data-testid="stTabs"] button[role="tab"] p {font-weight: 700; font-size: 1rem;}
div[data-testid="stPlotlyChart"] {background: #fff; border-radius: 18px; overflow: hidden;
  box-shadow: 0 6px 18px rgba(19,41,61,.06);}
section[data-testid="stSidebar"] {background: #EEF5FA;}
</style>
""", unsafe_allow_html=True)


def style(fig, height=380, title=None):
    """Apply one consistent look to every chart."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color=INK, size=13),
        margin=dict(l=18, r=18, t=64 if title else 30, b=14),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    if title:
        fig.update_layout(title=dict(text=f"<b>{title}</b>", x=0.01, font=dict(size=16)))
    fig.update_xaxes(showgrid=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def stat(label, value):
    return f'<div class="stat"><div class="k">{label}</div><div class="v">{value}</div></div>'


# ---------- Load data ----------
@st.cache_data(ttl=600)   # reload from the database at most every 10 minutes
def load_table(table):
    from supabase import create_client
    db = create_client(st.secrets[https://xggfdiegywgvljsbwycx.supabase.co], st.secrets[sb_publishable_-kGIHGMRTVGb_c_dCq_qLA_EoZg_U0V])
    rows, start = [], 0
    while True:
        part = db.table(table).select("*").order("id").range(start, start + 999).execute().data
        rows += part
        if len(part) < 1000:
            return pd.DataFrame(rows)
        start += 1000


def sample_data():
    """Made-up data so the dashboard works before the database is connected."""
    rng = np.random.default_rng(1)
    now = pd.Timestamp.now(tz=MYT).floor("h")
    hours = pd.date_range(end=now, periods=120, freq="h")
    temp = 27 + 4 * np.sin((hours.hour - 9) / 24 * 2 * np.pi)
    obs = pd.DataFrame({"obs_time": hours, "temperature": temp + rng.normal(0, 0.5, len(hours)),
                        "humidity": 85 - (temp - 27) * 4,
                        "precipitation": rng.choice([0, 0, 0, 0.5, 3.0], len(hours)),
                        "wind_speed": rng.uniform(2, 10, len(hours))})
    fc = []
    for _, o in obs.iterrows():
        for h in [1, 3, 6, 12, 24, 48, 72]:
            fc.append({"issued_at": o.obs_time - pd.Timedelta(hours=h), "target_time": o.obs_time,
                       "horizon_hours": h,
                       "temperature": o.temperature + rng.normal(0, 0.3 + h / 40),
                       "humidity": o.humidity + rng.normal(0, 2 + h / 20),
                       "precipitation": max(0.0, o.precipitation + rng.normal(0, 0.5)),
                       "precip_probability": rng.uniform(0, 100),
                       "wind_speed": o.wind_speed + rng.normal(0, 1)})
    for h in range(1, 73):
        t = now + pd.Timedelta(hours=h)
        fc.append({"issued_at": now, "target_time": t, "horizon_hours": h,
                   "temperature": 27 + 4 * np.sin((t.hour - 9) / 24 * 2 * np.pi),
                   "humidity": 80.0, "precipitation": float(rng.choice([0, 0, 1.0])),
                   "precip_probability": float(rng.uniform(0, 100)), "wind_speed": 5.0})
    return obs, pd.DataFrame(fc)


try:
    obs, fc = load_table("observations"), load_table("forecasts")
    live = True
except Exception:
    obs, fc = sample_data()
    live = False

if obs.empty:
    st.warning("No data yet. Check the database connection and read-only rules.")
    st.stop()

obs["obs_time"] = pd.to_datetime(obs["obs_time"], utc=True).dt.tz_convert(MYT)
fc["target_time"] = pd.to_datetime(fc["target_time"], utc=True).dt.tz_convert(MYT)
fc["issued_at"] = pd.to_datetime(fc["issued_at"], utc=True).dt.tz_convert(MYT)
fc["precip_probability"] = fc["precip_probability"].fillna(0)
obs = obs.sort_values("obs_time").reset_index(drop=True)
latest = obs.iloc[-1]

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 🎛️ Filters")
    first_day, last_day = obs.obs_time.min().date(), obs.obs_time.max().date()
    dates = st.date_input("Date range", (first_day, last_day),
                          min_value=first_day, max_value=last_day)
    variable = st.selectbox("Variable", list(VARS),
                            format_func=lambda k: f'{VARS[k]["icon"]} {VARS[k]["label"]} ({VARS[k]["unit"]})')
    horizon = st.select_slider("Forecast made how many hours ahead?",
                               options=[1, 3, 6, 12, 24, 48, 72], value=24)
    st.markdown("---")
    st.markdown("**About this dashboard**  \n"
                "An automated collector fetches Open-Meteo data for Seri Iskandar, Perak "
                "and stores every observation and 72-hour forecast in a cloud database. "
                "This page compares what was forecast with what actually happened.  \n\n"
                "TFB2093 Internet-of-Things project")

obs_f = obs
if isinstance(dates, tuple) and len(dates) == 2:
    obs_f = obs[(obs.obs_time.dt.date >= dates[0]) & (obs.obs_time.dt.date <= dates[1])]

matched = (obs_f.merge(fc[fc.horizon_hours == horizon], left_on="obs_time",
                       right_on="target_time", suffixes=("_obs", "_fc"))
           .sort_values("obs_time"))
pairs = fc.merge(obs_f, left_on="target_time", right_on="obs_time", suffixes=("_fc", "_obs"))
meta = VARS[variable]

# ---------- Hero banner ----------
status = '<span class="dot"></span>Live data' if live else "⚠️ Sample data (database not connected)"
st.markdown(
    '<div class="hero"><div class="art">🌦️</div>'
    '<h1>Seri Iskandar Weather Monitor</h1>'
    '<p>Hourly observations, 72-hour forecasts and forecast accuracy for Seri Iskandar, Perak, Malaysia</p>'
    f'<span class="pill">{status}</span>'
    f'<span class="pill">📅 Collecting since {obs.obs_time.min():%d %b %Y}</span>'
    f'<span class="pill">⏱️ {len(obs):,} hours recorded</span>'
    f'<span class="pill">📦 {len(fc):,} forecasts stored</span>'
    f'<span class="pill">🔄 Latest: {latest.obs_time:%d %b, %H:%M} MYT</span>'
    '</div>', unsafe_allow_html=True)

# ---------- Current conditions ----------
prev = obs[obs.obs_time == latest.obs_time - pd.Timedelta(hours=24)]
for col, (key, m) in zip(st.columns(4), VARS.items()):
    fmt = ".0f" if key == "humidity" else ".1f"
    delta = ""
    if len(prev):
        d = latest[key] - prev.iloc[0][key]
        arrow = "▲" if d > 0.05 else "▼" if d < -0.05 else "●"
        delta = f'<div class="delta"><b>{arrow} {d:+.1f} {m["unit"]}</b> vs same hour yesterday</div>'
    col.markdown(
        f'<div class="card" style="--c:{m["color"]}"><div class="lbl">{m["icon"]} {m["label"]}</div>'
        f'<div class="val">{latest[key]:{fmt}} <span>{m["unit"]}</span></div>{delta}</div>',
        unsafe_allow_html=True)

# ---------- Next 24 hours outlook ----------
nxt = fc[(fc.issued_at == fc.issued_at.max()) & (fc.horizon_hours <= 24)].sort_values("target_time")
if not nxt.empty:
    soon = nxt[nxt.horizon_hours <= 6]
    peak = soon.precip_probability.max() if len(soon) else 0
    if peak >= 60:
        when = soon.loc[soon.precip_probability.idxmax(), "target_time"]
        st.markdown(f'<div class="alert rain">☔ Rain likely soon: {peak:.0f}% chance around '
                    f'{when:%H:%M}. Bring an umbrella!</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert dry">🌤️ Low rain risk in the next 6 hours '
                    f'(highest chance {peak:.0f}%).</div>', unsafe_allow_html=True)

    probs = nxt.precip_probability.clip(0, 100) / 100
    bar_colors = px.colors.sample_colorscale("Blues", [0.2 + 0.8 * p for p in probs])
    out = make_subplots(specs=[[{"secondary_y": True}]])
    out.add_bar(x=nxt.target_time, y=nxt.precip_probability, name="Chance of rain (%)",
                marker_color=bar_colors, opacity=0.85, secondary_y=False)
    out.add_scatter(x=nxt.target_time, y=nxt.temperature, name="Temperature (°C)",
                    mode="lines+markers", line=dict(color=VARS["temperature"]["color"], width=3, shape="spline"),
                    marker=dict(size=6, color="white", line=dict(color=VARS["temperature"]["color"], width=2)),
                    secondary_y=True)
    out.update_yaxes(title_text="Chance of rain (%)", range=[0, 100], tickvals=[0, 25, 50, 75, 100],
                     secondary_y=False)
    t_lo = int(np.floor(nxt.temperature.min())) - 1
    t_hi = int(np.ceil(nxt.temperature.max())) + 1
    out.update_yaxes(title_text="Temperature (°C)", showgrid=False, range=[t_lo, t_hi],
                     dtick=2 if t_hi - t_lo > 6 else 1, tickformat="d", secondary_y=True)
    style(out, 330, "🔮 Next 24 hours: temperature and chance of rain")
    st.plotly_chart(out, use_container_width=True, config=CHART_CFG)

tab1, tab2, tab3, tab4 = st.tabs(["📈 Forecast vs actual", "🎯 Forecast accuracy",
                                  "🗓️ Weather patterns", "📋 Data"])

# ---------- Tab 1: forecast vs actual ----------
with tab1:
    fig = go.Figure()
    if not matched.empty:
        # Put forecasts on an hourly grid so hours without a forecast show as gaps
        grid = (matched.drop_duplicates("obs_time").set_index("obs_time")
                [[f"{variable}_obs", f"{variable}_fc"]]
                .reindex(pd.date_range(matched.obs_time.min(), matched.obs_time.max(), freq="h")))
        has_fc = grid[f"{variable}_fc"].notna()
        # Shade the error only over runs of consecutive forecast hours (one polygon per run)
        run_id = (has_fc != has_fc.shift()).cumsum()
        sx, sy = [], []
        for _, run in grid[has_fc].groupby(run_id[has_fc]):
            if len(run) < 2:
                continue
            sx += list(run.index) + list(run.index[::-1]) + [None]
            sy += list(run[f"{variable}_obs"]) + list(run[f"{variable}_fc"][::-1]) + [None]
        if sx:
            fig.add_scatter(x=sx, y=sy, fill="toself", fillcolor="rgba(142,108,201,0.18)",
                            mode="lines", line=dict(width=0), hoverinfo="skip",
                            name="Forecast error")
        # Markers keep single isolated forecasts visible; lines join consecutive hours only
        fig.add_scatter(x=grid.index, y=grid[f"{variable}_fc"], connectgaps=False,
                        name=f"Forecast ({horizon} h ahead)", mode="lines+markers",
                        line=dict(color=FORECAST, width=2, dash="dash"),
                        marker=dict(color=FORECAST, size=7, line=dict(color="white", width=1)))
    fig.add_scatter(x=obs_f.obs_time, y=obs_f[variable], name="Actual", mode="lines",
                    line=dict(color=meta["color"], width=2.5))
    fig.update_yaxes(title_text=f'{meta["label"]} ({meta["unit"]})')
    # Open on the 7-day window with the most complete forecasts (latest one if tied)
    last_t = obs_f.obs_time.max()
    first_t = max(obs_f.obs_time.min(), last_t - pd.Timedelta(days=7))
    if not matched.empty:
        hrs = pd.Series(1, index=matched.obs_time.drop_duplicates())
        daily_n = hrs.groupby(hrs.index.floor("D")).sum()
        daily_n = daily_n.reindex(pd.date_range(obs_f.obs_time.min().floor("D"),
                                                obs_f.obs_time.max().floor("D"), freq="D"), fill_value=0)
        week = daily_n.rolling(7, min_periods=1).sum()
        best_end = week[week == week.max()].index[-1]
        last_t = min(obs_f.obs_time.max(), best_end + pd.Timedelta(hours=23))
        first_t = max(obs_f.obs_time.min(), last_t - pd.Timedelta(days=7))
    fig.update_xaxes(range=[first_t, last_t], rangeslider=dict(visible=True, thickness=0.07))
    style(fig, 500, f'{meta["icon"]} {meta["label"]}: forecast vs actual (shaded = forecast error)')
    st.plotly_chart(fig, use_container_width=True, config=CHART_CFG)
    if not matched.empty:
        cover = matched.obs_time.nunique() / max(1, len(obs_f))
        st.caption(f"{cover:.0%} of hours in the selected range have a saved {horizon}-hour-ahead forecast. "
                   "Gaps (mostly after 9 Nov) are hours when GitHub skipped the scheduled collector, so no "
                   "forecast was recorded. Observations were back-filled, so the actual line is complete. "
                   "Drag the slider below the chart to move through the period.")

    rainy = obs_f[obs_f.precipitation >= RAIN_MM]
    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(stat("🌧️ Total rainfall", f"{obs_f.precipitation.sum():.1f} mm"), unsafe_allow_html=True)
    s2.markdown(stat("⏱️ Rainy hours", f"{len(rainy)} of {len(obs_f)}"), unsafe_allow_html=True)
    if len(rainy):
        wet = obs_f.loc[obs_f.precipitation.idxmax()]
        s3.markdown(stat("💦 Wettest hour", f"{wet.precipitation:.1f} mm · {wet.obs_time:%d %b %H:%M}"),
                    unsafe_allow_html=True)
    s4.markdown(stat("🌡️ Temperature range",
                     f"{obs_f.temperature.min():.1f} – {obs_f.temperature.max():.1f} °C"),
                unsafe_allow_html=True)

    daily = (obs_f.assign(day=obs_f.obs_time.dt.floor("D"))
             .groupby("day").precipitation.sum().reset_index())
    daily["label"] = daily.day.dt.strftime("%d %b")
    rain = go.Figure(go.Bar(x=daily.label, y=daily.precipitation, name="Daily rainfall",
                            marker=dict(color=daily.precipitation, colorscale="Blues", cmin=-5,
                                        cmax=max(20.0, daily.precipitation.max())),
                            text=[f"{v:.0f}" if v >= 1 else "" for v in daily.precipitation],
                            textposition="outside",
                            cliponaxis=False,
                            hovertemplate="%{x}: %{y:.1f} mm<extra></extra>"))
    rain.update_yaxes(title_text="Rainfall (mm per day)")
    n_days = len(daily)
    pad = max(0, (7 - n_days) / 2)            # keep bars narrow when only a few days are shown
    rain.update_xaxes(type="category", range=[-0.5 - pad, n_days - 0.5 + pad])
    rain.update_yaxes(range=[0, max(5.0, daily.precipitation.max()) * 1.18])
    style(rain, 320, "🌧️ Daily rainfall")
    rain.update_layout(hovermode="closest")
    st.plotly_chart(rain, use_container_width=True, config=CHART_CFG)

# ---------- Tab 2: forecast accuracy ----------
with tab2:
    st.markdown(f'<div class="section">How accurate were forecasts made {horizon} hours ahead?</div>'
                '<div class="sub">MAE = average size of the error · Bias = whether forecasts '
                'ran too high (+) or too low (−)</div>', unsafe_allow_html=True)
    if matched.empty:
        st.info("No forecast-actual pairs for this horizon and date range yet.")
    else:
        for col, (key, m) in zip(st.columns(4), VARS.items()):
            e = matched[f"{key}_fc"] - matched[f"{key}_obs"]
            col.markdown(
                f'<div class="card" style="--c:{m["color"]}"><div class="lbl">{m["icon"]} {m["label"]} MAE</div>'
                f'<div class="val">{e.abs().mean():.2f} <span>{m["unit"]}</span></div>'
                f'<div class="delta">RMSE <b>{np.sqrt((e ** 2).mean()):.2f}</b> · Bias <b>{e.mean():+.2f}</b> '
                f'· {e.count():,} pairs</div></div>', unsafe_allow_html=True)

        left, right = st.columns([3, 2])
        with left:
            err = pairs.assign(e=pairs[f"{variable}_fc"] - pairs[f"{variable}_obs"])
            by_h = err.groupby("horizon_hours").agg(MAE=("e", lambda x: x.abs().mean()),
                                                    RMSE=("e", lambda x: np.sqrt((x ** 2).mean())))
            by_h = by_h.reset_index()
            g = go.Figure()
            g.add_scatter(x=by_h.horizon_hours, y=by_h.RMSE, name="RMSE", mode="lines",
                          line=dict(color=FORECAST, width=2, dash="dot"))
            g.add_scatter(x=by_h.horizon_hours, y=by_h.MAE, name="MAE", mode="lines",
                          line=dict(color=meta["color"], width=3), fill="tozeroy",
                          fillcolor="rgba(91,112,131,0.10)")
            g.update_xaxes(title_text="Hours ahead the forecast was made", dtick=12)
            g.update_yaxes(title_text=f'Error ({meta["unit"]})')
            style(g, 380, f'{meta["icon"]} Forecast error by how far ahead it was made')
            st.plotly_chart(g, use_container_width=True, config=CHART_CFG)
        with right:
            lo = min(matched[f"{variable}_obs"].min(), matched[f"{variable}_fc"].min())
            hi = max(matched[f"{variable}_obs"].max(), matched[f"{variable}_fc"].max())
            sc = go.Figure()
            sc.add_scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="Perfect forecast",
                           line=dict(color=MUTED, dash="dash"))
            sc.add_scatter(x=matched[f"{variable}_obs"], y=matched[f"{variable}_fc"], mode="markers",
                           name="Each hour", marker=dict(color=meta["color"], size=7, opacity=0.55,
                                                          line=dict(color="white", width=0.5)))
            sc.update_xaxes(title_text=f'Actual ({meta["unit"]})')
            sc.update_yaxes(title_text=f'Forecast ({meta["unit"]})')
            style(sc, 380, "Forecast vs actual, hour by hour")
            sc.update_layout(hovermode="closest")
            st.plotly_chart(sc, use_container_width=True, config=CHART_CFG)

        st.markdown(f'<div class="section">☔ Did it rain when forecast? ({horizon} h ahead)</div>'
                    f'<div class="sub">An hour counts as rainy at {RAIN_MM} mm or more</div>',
                    unsafe_allow_html=True)
        f = matched.precipitation_fc >= RAIN_MM
        o = matched.precipitation_obs >= RAIN_MM
        hits, misses = int((f & o).sum()), int((~f & o).sum())
        false_alarms, dry = int((f & ~o).sum()), int((~f & ~o).sum())
        donut_col, stats_col = st.columns([2, 3])
        with donut_col:
            dn = go.Figure(go.Pie(labels=["Rain caught", "Rain missed", "False alarm", "Dry, correct"],
                                  values=[hits, misses, false_alarms, dry], hole=0.62, sort=False,
                                  marker=dict(colors=["#3A5BA9", "#E4572E", "#F2B134", "#BFD7EA"])))
            dn.update_traces(textinfo="percent")
            style(dn, 340)
            dn.update_layout(hovermode="closest", margin=dict(t=20, b=60),
                             legend=dict(orientation="h", y=-0.08, yanchor="top", x=0.5, xanchor="center"),
                             annotations=[dict(text=f"<b>{len(matched):,}</b><br>hours", x=0.5, y=0.5,
                                               showarrow=False, font=dict(size=16, color=INK))])
            st.plotly_chart(dn, use_container_width=True, config={"displayModeBar": False})
        with stats_col:
            hit_rate = hits / (hits + misses) if hits + misses else float("nan")
            far = false_alarms / (hits + false_alarms) if hits + false_alarms else float("nan")
            acc = (hits + dry) / len(matched)
            a, b, c = st.columns(3)
            a.markdown(stat("🎯 Hit rate", f"{hit_rate:.0%}" if hit_rate == hit_rate else "–"),
                       unsafe_allow_html=True)
            b.markdown(stat("🚨 False alarm ratio", f"{far:.0%}" if far == far else "–"),
                       unsafe_allow_html=True)
            c.markdown(stat("✅ Overall accuracy", f"{acc:.0%}"), unsafe_allow_html=True)
            st.markdown('<div class="sub" style="margin-top:14px">Hit rate: share of rainy hours that '
                        'were forecast. False alarm ratio: share of forecast rain that never came.</div>',
                        unsafe_allow_html=True)

        cols = [f"{k}_err" for k in VARS]
        allv = pairs.assign(**{f"{k}_err": (pairs[f"{k}_fc"] - pairs[f"{k}_obs"]).abs() for k in VARS})
        multi = allv.groupby("horizon_hours")[cols].mean().reset_index()
        sm = make_subplots(rows=1, cols=4, subplot_titles=[
            f'{m["icon"]} {m["label"]} ({m["unit"]})' for m in VARS.values()])
        for i, (k, m) in enumerate(VARS.items(), start=1):
            sm.add_scatter(x=multi.horizon_hours, y=multi[f"{k}_err"], mode="lines", name=m["label"],
                           line=dict(color=m["color"], width=2.5), fill="tozeroy", showlegend=False,
                           row=1, col=i)
            sm.update_xaxes(dtick=24, title_text="Hours ahead", row=1, col=i)
        style(sm, 300, "Mean absolute error by forecast horizon, all variables")
        st.plotly_chart(sm, use_container_width=True, config=CHART_CFG)

# ---------- Tab 3: weather patterns ----------
with tab3:
    hm = (obs_f.assign(date=obs_f.obs_time.dt.strftime("%d %b"), day=obs_f.obs_time.dt.date,
                       hour=obs_f.obs_time.dt.hour)
          .pivot_table(index=["day", "date"], columns="hour", values=variable, aggfunc="mean")
          .reset_index())
    hours = [h for h in range(24) if h in hm.columns]
    heat = go.Figure(go.Heatmap(z=hm[hours].values, x=[f"{h:02d}:00" for h in hours], y=hm["date"],
                                colorscale=meta["scale"],
                                colorbar=dict(title=meta["unit"]),
                                hovertemplate="%{y} %{x}<br>%{z:.1f} " + meta["unit"] + "<extra></extra>"))
    heat.update_yaxes(autorange="reversed")
    style(heat, max(320, 22 * len(hm) + 120), f'{meta["icon"]} {meta["label"]} by hour of day')
    heat.update_layout(hovermode="closest")
    st.plotly_chart(heat, use_container_width=True, config=CHART_CFG)

    left, right = st.columns(2)
    by_hour = obs_f.assign(hour=obs_f.obs_time.dt.hour).groupby("hour")
    with left:
        d = by_hour[variable].agg(["mean", "min", "max"]).reset_index()
        dc = go.Figure()
        dc.add_scatter(x=d.hour, y=d["max"], mode="lines", line=dict(width=0), showlegend=False,
                       hoverinfo="skip")
        dc.add_scatter(x=d.hour, y=d["min"], mode="lines", line=dict(width=0), fill="tonexty",
                       fillcolor="rgba(91,112,131,0.15)", name="Range")
        dc.add_scatter(x=d.hour, y=d["mean"], mode="lines+markers", name="Average",
                       line=dict(color=meta["color"], width=3, shape="spline"))
        dc.update_xaxes(title_text="Hour of day", dtick=3)
        dc.update_yaxes(title_text=meta["unit"])
        style(dc, 340, f'Typical daily cycle: {meta["label"].lower()}')
        st.plotly_chart(dc, use_container_width=True, config=CHART_CFG)
    with right:
        r = (by_hour["precipitation"].apply(lambda x: (x >= RAIN_MM).mean() * 100)
             .reset_index(name="share"))
        rb = go.Figure(go.Bar(x=r.hour, y=r.share,
                              marker=dict(color=r.share, colorscale="Blues", cmin=0)))
        rb.update_xaxes(title_text="Hour of day", dtick=3)
        rb.update_yaxes(title_text="% of days with rain")
        style(rb, 340, "☔ When does it rain? Chance of rain by hour")
        st.plotly_chart(rb, use_container_width=True, config=CHART_CFG)

# ---------- Tab 4: raw data ----------
with tab4:
    table = obs_f[["obs_time", *VARS]].sort_values("obs_time", ascending=False)
    st.dataframe(
        table, hide_index=True, use_container_width=True, height=460,
        column_config={
            "obs_time": st.column_config.DatetimeColumn("Time (MYT)", format="DD MMM YYYY, HH:mm"),
            "temperature": st.column_config.NumberColumn("🌡️ Temperature (°C)", format="%.1f"),
            "humidity": st.column_config.ProgressColumn("💧 Humidity (%)", min_value=0, max_value=100,
                                                        format="%.0f"),
            "precipitation": st.column_config.NumberColumn("🌧️ Rainfall (mm)", format="%.1f"),
            "wind_speed": st.column_config.NumberColumn("🍃 Wind (km/h)", format="%.1f"),
        })
    st.download_button("⬇️ Download observations (CSV)", table.to_csv(index=False),
                       file_name="seri_iskandar_observations.csv", mime="text/csv")

st.caption("Weather data by Open-Meteo.com (CC BY 4.0) · Built with Streamlit, Plotly and Supabase · "
           "TFB2093 Internet-of-Things")
