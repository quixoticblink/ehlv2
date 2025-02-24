import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Streamlit App Title
st.title("Singapore Hotel Dynamic Pricing")

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
            st.write("Available columns in API response:", df_hotels.columns.tolist())
        return df_hotels
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return pd.DataFrame()

hotel_df = get_hotel_data()
if not hotel_df.empty:
    st.subheader("Hotel Summary Data")
    display_cols = [col for col in ['name', 'address', 'leadInRoomRate', 'leadInRoomSize'] if col in hotel_df.columns]
    if display_cols:
        st.dataframe(hotel_df[display_cols])
    else:
        st.write("No matching columns found in the API response.")

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
    df['Promotion'] = df['Date'].apply(lambda d: "Family Package: Free breakfast + Kids stay free" if d.strftime('%Y-%m-%d') in event_dates["School Holidays"]
                                       else "Business Package: Free WiFi + Late checkout" if d.strftime('%Y-%m-%d') in event_dates["Sea Asia 2025"]
                                       else "Standard Discount: 10% off direct booking")

df['Reason'] = df['Date'].apply(lambda d: "High demand due to School Holidays" if d.strftime('%Y-%m-%d') in event_dates["School Holidays"]
                                  else "High demand due to Sea Asia 2025 event" if d.strftime('%Y-%m-%d') in event_dates["Sea Asia 2025"]
                                  else "Regular pricing period")

recommend_promotions()

st.subheader("Singapore Events in March 2025")
for event, dates in event_dates.items():
    st.write(f"**{event}:** {', '.join(dates)}")

# Display recommended pricing and promotions
st.subheader("Recommended Pricing & Promotions")
st.dataframe(df[['Date', 'Base_Price', 'Promotion', 'Reason']])

# Plot price trends
st.subheader("Pricing Trend")
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['Date'], df['Base_Price'], marker='o', linestyle='-', label='Recommended Price')
ax.set_xlabel("Date")
ax.set_ylabel("Price (SGD)")
ax.set_title("Recommended Hotel Pricing for March 2025")
ax.legend()
ax.grid()
st.pyplot(fig)

# Save the DataFrame to a CSV file for further analysis
df.to_csv("hotel_pricing_march_2025.csv", index=False)