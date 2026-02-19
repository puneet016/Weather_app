# Real-Time Weather App

A beautiful Streamlit weather app using OpenWeatherMap API.

## Features
- Current weather for any city
- Temperature, humidity, sunrise, sunset
- 5-day forecast chart
- Dynamic weather icons
- Unit toggle (Celsius/Fahrenheit)
- Sample city queries in sidebar

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set API key:
   - PowerShell:
     ```powershell
     $env:OPENWEATHER_API_KEY="your_api_key_here"
     ```
   - Or create `.streamlit/secrets.toml` with:
     ```toml
     OPENWEATHER_API_KEY = "your_api_key_here"
     ```
3. Run:
   ```bash
   streamlit run app.py
   ```