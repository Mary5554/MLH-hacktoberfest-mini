SNOWFLAKE_SAMPLE_DATA.TPCH_SF10# Dengue Early Warning: Streamlit in Snowflake
import pandas as pd
import altair as alt
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Dengue Early Warning", layout="wide")
session = get_active_session()


@st.cache_data(ttl=600)
def load():
    anom = session.table("OUTBREAK_DB.EARLY_WARNING.ANOMALY_RESULTS").to_pandas()
    fc = session.table("OUTBREAK_DB.EARLY_WARNING.FORECAST_RESULTS").to_pandas()
    loc = session.table("OUTBREAK_DB.EARLY_WARNING.CITY_LOCATIONS").to_pandas()
    anom["WEEK_START"] = pd.to_datetime(anom["WEEK_START"])
    fc["WEEK_START"] = pd.to_datetime(fc["WEEK_START"])
    return anom, fc, loc


anom, fc, loc = load()

st.title("🦟 Dengue Outbreak Early Warning")
st.caption("Snowflake ML anomaly detection + forecasting · replay mode")

# ---- Replay slider: pretend "today" is any week in the detection window ----
weeks = sorted(anom["WEEK_START"].dt.date.unique())
as_of = pd.Timestamp(
    st.select_slider("Simulated current week", options=weeks, value=weeks[len(weeks) // 2])
)
lookback = st.sidebar.slider("Alert lookback (weeks)", 1, 8, 4)
st.sidebar.markdown("Alert = week flagged as an anomaly **and** above the upper prediction bound.")

# ---- Alerts: upward anomalies within lookback window ----
win = anom[
    (anom["WEEK_START"] <= as_of)
    & (anom["WEEK_START"] > as_of - pd.Timedelta(weeks=lookback))
    & (anom["IS_ANOMALY"])
    & (anom["CASES"] > anom["UPPER_BOUND"])
].copy()
win["SEVERITY_X"] = (win["CASES"] / win["UPPER_BOUND"].clip(lower=1)).round(2)
win["LEVEL"] = win["SEVERITY_X"].apply(lambda r: "HIGH" if r >= 1.5 else "ELEVATED")

# Latest alert level per city
level = win.groupby("CITY")["LEVEL"].agg(lambda s: "HIGH" if "HIGH" in set(s) else "ELEVATED")
loc["STATUS"] = loc["CITY"].map(level).fillna("NORMAL")
colors = {"HIGH": [220, 38, 38, 200], "ELEVATED": [245, 158, 11, 200], "NORMAL": [34, 139, 34, 160]}
loc["COLOR"] = loc["STATUS"].map(colors)
loc["RADIUS"] = loc["STATUS"].map({"HIGH": 250000, "ELEVATED": 180000, "NORMAL": 100000})

left, right = st.columns([3, 2])

with left:
    st.subheader("Map")
    map_data = loc.rename(columns={"LAT": "latitude", "LON": "longitude"})
    st.map(map_data)

with right:
    st.subheader("Active alerts")
    if win.empty:
        st.success("No active alerts for this week.")
    else:
        show = win.sort_values("WEEK_START", ascending=False)[
            ["CITY", "WEEK_START", "CASES", "EXPECTED", "UPPER_BOUND", "SEVERITY_X", "LEVEL"]
        ].round(1)
        st.dataframe(show, use_container_width=True)

# ---- Trend + forecast per city ----
st.subheader("Cases vs. expected range")
city = st.selectbox("City", loc["CITY"].tolist(),
                    format_func=lambda c: loc.set_index("CITY").loc[c, "NAME"])

a = anom[(anom["CITY"] == city) & (anom["WEEK_START"] <= as_of)]
band = alt.Chart(a).mark_area(opacity=0.2).encode(
    x="WEEK_START:T", y="LOWER_BOUND:Q", y2="UPPER_BOUND:Q")
line = alt.Chart(a).mark_line().encode(x="WEEK_START:T", y=alt.Y("CASES:Q", title="Weekly cases"))
pts = alt.Chart(a[a["IS_ANOMALY"] & (a["CASES"] > a["UPPER_BOUND"])]).mark_circle(
    size=90, color="red").encode(x="WEEK_START:T", y="CASES:Q")
chart = band + line + pts

# Show the forecast only when the slider is at the final week
if as_of >= anom["WEEK_START"].max():
    f = fc[fc["CITY"] == city]
    fband = alt.Chart(f).mark_area(opacity=0.2, color="orange").encode(
        x="WEEK_START:T", y="LOWER_BOUND:Q", y2="UPPER_BOUND:Q")
    fline = alt.Chart(f).mark_line(color="orange", strokeDash=[4, 3]).encode(
        x="WEEK_START:T", y="FORECAST:Q")
    chart = chart + fband + fline
    st.caption("Orange dashed = 8-week forecast with 90% interval")

st.altair_chart(chart.interactive(), use_container_width=True)
