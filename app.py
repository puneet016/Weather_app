from datetime import datetime

import altair as alt
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Real-Time Weather App", page_icon="☁", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    :root {
        --bg-base: #020617;
        --card-bg: rgba(30, 41, 59, 0.4);
        --card-border: rgba(148, 163, 184, 0.15);
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --accent: #38bdf8;
    }

    .stApp {
        font-family: 'Inter', sans-serif;
        background: var(--bg-base);
        background-image: 
            radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(30, 58, 138, 0.2) 0px, transparent 50%);
        color: var(--text-primary);
    }

    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #e2e8f0, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        font-weight: 300;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(12px);
        transition: transform 0.2s;
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(148, 163, 184, 0.3);
    }

    .metric-title {
        color: var(--text-secondary);
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .forecast-block {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 1.2rem;
        text-align: center;
        height: 100%;
        backdrop-filter: blur(12px);
    }

    .tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.2);
        color: var(--accent);
        font-size: 0.8rem;
        margin: 4px;
    }

    @keyframes rise {
        from { transform: translateY(8px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def geocode_city(city: str):
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if "results" not in data:
        return None
    return data["results"][0]


def fetch_weather_data(lat: float, lon: float, units: str):
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,is_day",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset",
            "timezone": "auto",
            "temperature_unit": "fahrenheit" if units == "imperial" else "celsius",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_weather_desc(code: int, is_day: int = 1):
    if code == 0:
        return "Clear sky", "01d" if is_day else "01n"
    if code in [1, 2, 3]:
        return "Partly cloudy", "02d" if is_day else "02n"
    if code in [45, 48]:
        return "Fog", "50d"
    if code in [51, 53, 55]:
        return "Drizzle", "09d"
    if code in [61, 63, 65]:
        return "Rain", "10d"
    if code in [71, 73, 75]:
        return "Snow", "13d"
    if code >= 95:
        return "Thunderstorm", "11d"
    return "Cloudy", "03d"


def weather_icon_url(icon_code: str) -> str:
    return f"https://openweathermap.org/img/wn/{icon_code}@2x.png"


def build_daily_forecast(daily_data: dict) -> pd.DataFrame:
    dates = daily_data.get("time", [])
    max_temps = daily_data.get("temperature_2m_max", [])
    codes = daily_data.get("weather_code", [])

    rows = []
    for i, date_str in enumerate(dates):
        desc, icon = get_weather_desc(codes[i])
        rows.append(
            {
                "date": datetime.strptime(date_str, "%Y-%m-%d").date(),
                "temp": max_temps[i],
                "description": desc,
                "icon": icon,
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["day"] = pd.to_datetime(df["date"]).dt.strftime("%a")
    df["label"] = pd.to_datetime(df["date"]).dt.strftime("%b %d")
    return df.head(5)


def main():
    st.markdown('<div class="main-title">Real-Time Weather App</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Beautiful weather visualizations for cities worldwide.</p>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Settings")
        unit_label = st.radio("Temperature Unit", ["Celsius (°C)", "Fahrenheit (°F)"], horizontal=False)
        units = "metric" if "Celsius" in unit_label else "imperial"
        temp_symbol = "°C" if units == "metric" else "°F"

        st.markdown("### Sample Queries")
        samples = ["New York", "London", "Tokyo", "Delhi", "Sydney"]
        for city in samples:
            st.markdown(f'<span class="tag">{city}</span>', unsafe_allow_html=True)

    city = st.text_input("Enter city name", placeholder="e.g., San Francisco")

    if not city:
        st.info("Type a city name to view weather details.")
        return

    try:
        location = geocode_city(city)
        if not location:
            st.warning("City not found. Try a different name with country code, e.g., Paris,FR")
            return

        lat, lon = location["latitude"], location["longitude"]
        weather_data = fetch_weather_data(lat, lon, units)
    except requests.HTTPError as e:
        st.error(f"API error: {e}")
        return
    except requests.RequestException:
        st.error("Network error while contacting Weather Service.")
        return

    current = weather_data["current"]
    daily_raw = weather_data["daily"]
    city_name = location.get("name", city.title())
    country = location.get("country", "")
    description, icon = get_weather_desc(current["weather_code"], current["is_day"])

    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.markdown(f"## {city_name}, {country}")
        st.caption(description)
    with header_col2:
        st.image(weather_icon_url(icon), width=96)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            '<div class="metric-card"><div class="metric-title">Temperature</div>'
            f'<div class="metric-value">{current["temperature_2m"]:.1f}{temp_symbol}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="metric-card"><div class="metric-title">Humidity</div>'
            f'<div class="metric-value">{current["relative_humidity_2m"]:.0f}%</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        sunrise = datetime.fromisoformat(daily_raw["sunrise"][0]).strftime("%I:%M %p")
        st.markdown(
            '<div class="metric-card"><div class="metric-title">Sunrise</div>'
            f'<div class="metric-value">{sunrise}</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        sunset = datetime.fromisoformat(daily_raw["sunset"][0]).strftime("%I:%M %p")
        st.markdown(
            '<div class="metric-card"><div class="metric-title">Sunset</div>'
            f'<div class="metric-value">{sunset}</div></div>',
            unsafe_allow_html=True,
        )

    daily = build_daily_forecast(daily_raw)
    if daily.empty:
        st.warning("No forecast data available.")
        return

    st.markdown("### 5-Day Forecast")

    chart = (
        alt.Chart(daily)
        .mark_area(
            line={'color':'#38bdf8'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#38bdf8', offset=0),
                       alt.GradientStop(color='rgba(56, 189, 248, 0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        )
        .encode(
            x=alt.X("label:N", title=None, axis=alt.Axis(labelColor="#94a3b8", tickSize=0, domain=False)),
            y=alt.Y("temp:Q", title=None, axis=None, scale=alt.Scale(zero=False)),
            tooltip=["label", alt.Tooltip("temp:Q", format=".1f")],
        )
        .configure_view(strokeWidth=0)
        .configure_axis(grid=False)
        .properties(height=290)
    )
    st.altair_chart(chart, use_container_width=True)

    day_cols = st.columns(5)
    for idx, (_, row) in enumerate(daily.iterrows()):
        with day_cols[idx]:
            st.markdown('<div class="forecast-block">', unsafe_allow_html=True)
            st.markdown(f"**{row['day']}**")
            st.caption(row["label"])
            if isinstance(row.get("icon"), str):
                st.image(weather_icon_url(row["icon"]), width=62)
            st.write(f"{row['temp']:.1f}{temp_symbol}")
            if isinstance(row.get("description"), str):
                st.caption(row["description"])
            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()