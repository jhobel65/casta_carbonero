import requests
import streamlit as st
import time
from src.database import LeadsManager

class GoogleHarvester:
    def __init__(self):
        self.api_key = st.secrets["google"]["api_key"]
        self.db = LeadsManager()
        self.base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/json"

    def get_phone_number(self, place_id):
        """
        Performs a second API call to get the specific contact details.
        """
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number",
            "key": self.api_key
        }
        try:
            resp = requests.get(self.details_url, params=params)
            data = resp.json()
            return data.get('result', {}).get('formatted_phone_number', None)
        except:
            return None

    def scan_location(self, lat, lng, radius, keyword):
        """
        Scans Google, handles pagination (up to 60 results), 
        fetches phones, and saves to DB.
        """
        all_results = []
        next_page_token = None
        
        # --- PAGINATION LOOP ---
        while True:
            params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "keyword": keyword,
                "key": self.api_key
            }
            
            # If we have a token from the previous loop, add it to params
            if next_page_token:
                params["pagetoken"] = next_page_token
                # CRITICAL: Google needs ~2 seconds to make the token valid
                time.sleep(2) 

            try:
                resp = requests.get(self.base_url, params=params)
                data = resp.json()
                
                # Add this batch of 20 to our master list
                results = data.get('results', [])
                all_results.extend(results)
                
                # Check if there is another page
                next_page_token = data.get("next_page_token")
                
                if not next_page_token:
                    break  # No more pages, stop looping
                    
            except Exception as e:
                st.error(f"API Error during scan: {e}")
                break

        # --- PROCESS ALL RESULTS ---
        count = 0
        status_bar = st.progress(0, text="Fetching details...")
        total = len(all_results)
        
        for index, place in enumerate(all_results):
            # Update progress bar
            status_bar.progress((index + 1) / total, text=f"Processing {index+1}/{total}: {place.get('name')}")
            
            loc = place.get('geometry', {}).get('location', {})
            pid = place.get('place_id')
            
            # Fetch Phone (Costs time/quota, but necessary for sales)
            phone_number = self.get_phone_number(pid)
            
            lead_data = {
                "place_id": pid,
                "name": place.get('name'),
                "phone": phone_number,
                "address": place.get('vicinity'),
                "rating": place.get('rating', 0.0),
                "lat": loc.get('lat'),
                "lng": loc.get('lng'),
                "keyword": keyword
            }
            
            self.db.add_lead(lead_data)
            count += 1
            
        status_bar.empty() # Remove bar when done
        return count