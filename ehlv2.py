import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.express as px

# Streamlit App Configuration
st.set_page_config(page_title="Singapore Hotel Dynamic Pricing", layout="wide")

# Add Background and Text Color Styling
st.markdown("""
    <style>
        .main {background-color: #eef2f7; color: black;}
        .stDataFrame {border-radius: 10px;}
        h1, h2, h3, h4, h5, h6 {color: black;}
    </style>
""", unsafe_allow_html=True)

st.title("🏨 Singapore Hotel Dynamic Pricing Dashboard")

# Define March 2025 Dates
dates = pd.date_range(start="2025-03-01", end="2025-03-31")
df = pd.DataFrame(dates, columns=['Date'])

# API Configuration
API_KEY = "8gg0OdkaBdNXHeqsx1f6PvrG8doHA9mH"
BASE_URL = "https://api.stb.gov.sg/content/accommodation/v2/search"
HEADERS = {
    "Content-Type": "application/json",
    "X-Content-Language": "en",
    "X-API-KEY": API_KEY
}
PARAMS = {
    "searchType": "keyword",
    "searchValues": "hotel",
    "min_star_rating": 3,
    "max_star_rating": 3
}

def get_hotel_data():
    """Fetches hotel data from STB API."""
    response = requests.get(BASE_URL, headers=HEADERS, params=PARAMS)
    if response.status_code == 200:
        data = response.json()
        hotels = data.get('data', [])
        df_hotels = pd.DataFrame(hotels)
        if not df_hotels.empty:
            available_columns = df_hotels.columns.tolist()
            required_columns = [col for col in ['name', 'address', 'postalCode', 'leadInRoomRate'] if col in available_columns]
            df_hotels = df_hotels[required_columns]
        return df_hotels
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return pd.DataFrame()

hotel_df = get_hotel_data()
if not hotel_df.empty:
    st.subheader("🏢 Hotel Summary Data")
    st.dataframe(hotel_df.style.set_properties(**{'background-color': '#f8f9fa', 'border-color': 'black', 'color': 'black'}))

# Event-based price adjustments
event_dates = {
    "Geylang Serai Bazaar": ["2025-03-01", "2025-03-31"],
    "Hari Raya Puasa": ["2025-03-31"],
    "School Holidays": ["2025-03-15", "2025-03-23"],
    "Sea Asia 2025": ["2025-03-25", "2025-03-27"]
}

def adjust_prices_for_events():
    """Adjusts prices based on upcoming events and expected demand."""
    df['Base_Price'] = df['Base_Price'].astype(float)
    for event, dates in event_dates.items():
        for date in dates:
            df.loc[df['Date'] == date, 'Base_Price'] *= 1.2  # Ensure type consistency

# Generate base prices
if 'leadInRoomRate' in hotel_df.columns:
    df['Base_Price'] = float(hotel_df['leadInRoomRate'].mean())
else:
    df['Base_Price'] = np.random.randint(100, 200, size=len(dates)).astype(float)  # Fallback to random values

adjust_prices_for_events()

def recommend_promotions():
    df['Promotion'] = df['Date'].apply(lambda d: "🎉 Family Package: Free breakfast + Kids stay free" if d.strftime('%Y-%m-%d') in event_dates["School Holidays"]
                                       else "💼 Business Package: Free WiFi + Late checkout" if d.strftime('%Y-%m-%d') in event_dates["Sea Asia 2025"]
                                       else "💰 Standard Discount: 10% off direct booking")

df['Reason'] = df['Date'].apply(lambda d: "📈 High demand due to School Holidays" if d.strftime('%Y-%m-%d') in event_dates["School Holidays"]
                                  else "📊 High demand due to Sea Asia 2025 event" if d.strftime('%Y-%m-%d') in event_dates["Sea Asia 2025"]
                                  else "🔹 Regular pricing period")

recommend_promotions()

st.subheader("📅 Singapore Events in March 2025")
for event, dates in event_dates.items():
    st.write(f"**{event}:** {', '.join(dates)}")

# Display recommended pricing and promotions
st.subheader("💰 Recommended Pricing & Promotions")
st.dataframe(df[['Date', 'Base_Price', 'Promotion', 'Reason']].style.set_properties(**{'background-color': '#f8f9fa', 'border-color': 'black', 'color': 'black'}))

# Plot price trends with better visuals
st.subheader("📊 Pricing Trend")
fig = px.line(df, x='Date', y='Base_Price', title="Recommended Hotel Pricing for March 2025",
              labels={"Base_Price": "Price (SGD)"}, markers=True, line_shape="spline")
st.plotly_chart(fig)

# Save the DataFrame to a CSV file for further analysis
df.to_csv("hotel_pricing_march_2025.csv", index=False)
