import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date, timedelta

def scrape_hotel_rate(hotel_name, booking_website_url, check_in_date, website_name):
    """
    Scrapes hotel room rate from various booking websites based on website name.

    Args:
        hotel_name (str): Name of the hotel (for identification).
        booking_website_url (str): URL of the hotel listing on the booking website.
        check_in_date (str): Check-in date in YYYY-MM-DD format.
        website_name (str): Name of the website (e.g., 'agoda', 'bookingcom', 'expedia').

    Returns:
        float or None: Room rate if found, None otherwise.
    """
    try:
        url = booking_website_url.format(date=check_in_date)
        headers = {'User-Agent': 'Your User Agent String'}  # Add a User-Agent
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        room_rate = None

        if website_name == 'agoda':
            # Agoda Price Extraction (Example - may need adjustments)
            price_element = soup.find('span', class_='PropertyPriceBreakdown__PriceValue')
            if price_element:
                price_text = price_element.text.strip().replace('S$', '').replace(',', '')
                room_rate = float(price_text)

        elif website_name == 'bookingcom':
            # Booking.com Price Extraction (Example - may need adjustments)
            price_element = soup.find('span', class_='fcab3ed991 bd73d13072') # Updated class - check website
            if price_element:
                price_text = price_element.text.strip().replace('S$', '').replace('SGD', '').replace(',', '').replace(' ', '')
                room_rate = float(price_text)

        elif website_name == 'expedia':
            # Expedia Price Extraction (Example - may need adjustments)
            price_element = soup.find('span', class_='price-summary-price-value') # Example class - check website
            if price_element:
                price_text = price_element.text.strip().replace('S$', '').replace(',', '')
                room_rate = float(price_text)
        # Add more website parsing logic here (Trip.com, Traveloka, MakeMyTrip etc.)
        else:
            print(f"Website '{website_name}' parsing not implemented yet.")
            return None


        if room_rate is not None:
            return room_rate
        else:
            print(f"Price element not found for {hotel_name} on {check_in_date} on {website_name}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL for {hotel_name} on {check_in_date} from {website_name}: {e}")
        return None
    except Exception as e:
        print(f"Error parsing data for {hotel_name} on {check_in_date} from {website_name}: {e}")
        return None


def create_competitor_rate_excel(competitor_hotels, start_date, num_days, excel_filename="competitor_rates.xlsx"):
    """
    Scrapes competitor hotel rates for a date range from multiple websites and saves to Excel.

    Args:
        competitor_hotels (dict): Dictionary of competitor hotels with names and booking website URLs (including website name).
        start_date (date): Start date for data collection.
        num_days (int): Number of days to collect data for.
        excel_filename (str): Filename for the output Excel file.
    """

    all_rates_data = []
    dates = [start_date + timedelta(days=i) for i in range(num_days)]

    for hotel_info in competitor_hotels:
        hotel_name = hotel_info['name']
        website_url_format = hotel_info['url_format']
        website_name = hotel_info['website']

        for current_date in dates:
            check_in_date_str = current_date.strftime('%Y-%m-%d')
            rate = scrape_hotel_rate(hotel_name, website_url_format, check_in_date_str, website_name)
            all_rates_data.append({
                'Hotel': hotel_name,
                'Website': website_name,
                'Date': check_in_date_str,
                'Room Rate': rate
            })

    df = pd.DataFrame(all_rates_data)
    df.to_excel(excel_filename, index=False)
    print(f"Competitor rates saved to {excel_filename}")


def suggest_daily_rates(competitor_rates_excel, base_rate_weekday, base_rate_weekend, cbd_events):
    """
    Suggests daily room rates based on competitor data, day of week, and CBD events.

    Args:
        competitor_rates_excel (str): Filename of the Excel file with competitor rates.
        base_rate_weekday (float): Base room rate for weekdays in SGD.
        base_rate_weekend (float): Base room rate for weekends in SGD.
        cbd_events (dict): Dictionary of events near CBD with date ranges and impact level (e.g., {'NATAS': {'start': '2025-02-27', 'end': '2025-03-01', 'impact': 1.15}}).

    Returns:
        pandas.DataFrame: DataFrame with suggested daily rates.
    """
    df_rates = pd.read_excel(competitor_rates_excel)
    df_rates['Date'] = pd.to_datetime(df_rates['Date'])

    suggested_rates_data = []

    for current_date in df_rates['Date'].unique():
        date_str = current_date.strftime('%Y-%m-%d')
        weekday = current_date.weekday() # Monday is 0 and Sunday is 6
        is_weekend = weekday >= 4 # Friday (4) to Sunday (6) are weekends

        # Base Rate
        base_rate = base_rate_weekend if is_weekend else base_rate_weekday
        suggested_rate = base_rate

        # Competitor Adjustment (Simple Average)
        relevant_competitor_rates = df_rates[df_rates['Date'] == current_date]['Room Rate'].dropna()
        if not relevant_competitor_rates.empty:
            avg_competitor_rate = relevant_competitor_rates.mean()
            suggested_rate = max(suggested_rate, avg_competitor_rate * 0.9) # Be slightly competitive

        # Event Adjustment
        for event, event_details in cbd_events.items():
            event_start = pd.to_datetime(event_details['start'])
            event_end = pd.to_datetime(event_details['end'])
            if event_start <= current_date <= event_end:
                suggested_rate *= event_details['impact'] # Apply event-based multiplier
                print(f"  Applying event multiplier ({event}) for {date_str}")
                break # Apply only one event multiplier if dates overlap


        suggested_rates_data.append({
            'Date': date_str,
            'Day of Week': current_date.strftime('%A'),
            'Base Rate': base_rate,
            'Suggested Rate': suggested_rate
        })

    return pd.DataFrame(suggested_rates_data)


# --- Example Usage (Adapt these variables) ---

# 1. Define Competitor Hotels and their Booking Website URLs and Website Names
# **IMPORTANT**: You need to find URLs for specific hotels and VERIFY the URL date format and CSS selectors.
# Inspect website HTML to find correct price CSS classes (update scrape_hotel_rate function).

competitor_hotels_near_cbd = [
    {
        "name": "V Hotel Bencoolen",
        "url_format": "https://www.agoda.com/v-hotel-bencoolen_3/hotel/singapore-sg.html?checkInDay={date_day}&checkInMonth={date_month}&checkInYear={date_year}", # Example - Agoda URL format (may not be accurate)
        "website": "agoda"
    },
    {
        "name": "Hotel Boss",
        "url_format": "https://www.booking.com/hotel/sg/boss.en-gb.html?checkin={date}", # Example - Booking.com URL format (may not be accurate)
        "website": "bookingcom"
    },
    {
        "name": "Holiday Inn Express Singapore Clarke Quay", # Example - Expedia - you need to find actual URL
        "url_format": "https://www.expedia.com.sg/Singapore-Hotel-deals-Holiday-Inn-Express-Singapore-Clarke-Quay.h4878587.Hotel-Information?adults=2&children=0&startDate={date}", # Example - Expedia URL format (likely needs adjustment)
        "website": "expedia"
    },
    # Add more competitor hotels and their URL formats and website names here, for Trip.com, Traveloka, MakeMyTrip etc.
]

# 2. Define Date Range for Data Collection
start_date = date(2025, 3, 1) # Collect data from March 1, 2025
num_days = 30 # For 30 days

# 3. Run the scraper and create Excel
# **To make this executable, uncomment the line below AFTER you have:**
# **    a) Installed required libraries (pip install requests beautifulsoup4 pandas openpyxl)**
# **    b) VERIFIED and UPDATED CSS selectors in scrape_hotel_rate function for each website**
# **    c) VERIFIED and UPDATED URL formats in competitor_hotels_near_cbd**
# create_competitor_rate_excel(competitor_hotels_near_cbd, start_date, num_days)
print ("Note: Web scraping part is currently commented out. Uncomment create_competitor_rate_excel() to run it AFTER setup.")


# 4. Define Base Rates and CBD Events (You need to adjust these)
base_weekday_rate_sgd = 150.0  # Example base rate for weekdays
base_weekend_rate_sgd = 180.0  # Example base rate for weekends

# Example CBD events (adjust dates and impact based on your knowledge)
cbd_area_events = {
    "NATAS Travel Fair": {'start': '2025-02-27', 'end': '2025-03-01', 'impact': 1.20}, # 20% price increase during fair
    "Jason Derulo Concert": {'start': '2025-03-19', 'end': '2025-03-19', 'impact': 1.10}, # 10% increase for concert night
    # Add more CBD area events here
}


# 5. Suggest Daily Rates based on Competitor Data and Events
# **Assuming you have run the scraper and have "competitor_rates.xlsx" (or after you uncommented and ran it)**
suggested_rates_df = suggest_daily_rates("competitor_rates.xlsx", base_weekday_rate_sgd, base_weekend_rate_sgd, cbd_area_events)

print("\nSuggested Daily Room Rates:")
print(suggested_rates_df)

# Optional: Export suggested rates to a new Excel sheet
# suggested_rates_df.to_excel("suggested_daily_rates.xlsx", index=False)