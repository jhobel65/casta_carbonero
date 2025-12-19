import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from src.database import LeadsManager
from src.google_services import GoogleHarvester
from src.utils import STATUS_COLORS

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Casta Carbonero CRM", 
    page_icon="assets/logo_black.png", 
    layout="wide"
)

# --- CONSTANTS ---
# The allowed categories for search and filtering
SEARCH_TYPES = [
    "RESTAURANTE", 
    "HAMBURGUESAS", 
    "TAQUERIA", 
    "FONDA", 
    "FOOD TRUCK", 
    "CAFETERIA", 
    "LONCHERIA"
]

# --- INITIALIZE MODULES ---
db = LeadsManager()
harvester = GoogleHarvester()

# --- SIDEBAR (CONTROLS) ---
with st.sidebar:
    # 1. COMPANY BRANDING
    try:
        st.image("assets/logo_full_white.png", use_column_width=True)
    except:
        st.warning("Tip: Upload 'logo.png' to assets/ folder")

    st.divider()
    
    # 2. HARVESTER CONTROLS
    st.header("🚜 Lead Harvester")
    
    # Dynamic Search Center
    st.subheader("📍 Search Center")
    # Defaulting to Tijuana coordinates
    search_lat = st.number_input("Latitude", value=32.52044, format="%.4f")
    search_lng = st.number_input("Longitude", value=-117.01972, format="%.4f")
    st.caption("Tip: Change these to move your search area.")
    
    # STRICT SEARCH INPUT
    # Users can only pick from your defined list
    search_kw = st.selectbox("Target Category", SEARCH_TYPES)
    
    radius = st.slider("Scan Radius (meters)", 500, 5000, 1000)
    
    # The Scan Button
    if st.button("Run Scan", type="primary"):
        with st.spinner(f"Scanning Google Maps for '{search_kw}'..."):
            count = harvester.scan_location(search_lat, search_lng, radius, search_kw)
        
        if count > 0:
            st.success(f"Found {count} new leads!")
            st.rerun()
        else:
            st.warning("No new leads found in this area.")

    st.divider()
    
    # 3. FILTERS
    st.write("📊 **View Filters**")
    
    # Status Filter
    status_filter = st.selectbox("Status:", ["All", "New", "Contacted", "Interested", "Closed", "Ignored"])
    
    # NEW: Type Filter
    # We add "All" to the list so you can see everything if you want
    type_filter = st.selectbox("Category:", ["All"] + SEARCH_TYPES)

# --- MAIN DASHBOARD ---
st.title("🗺️ Territory Map & Leads")

# 1. FETCH DATA (Based on Status)
df = db.get_leads(status_filter)

# 2. APPLY TYPE FILTER (Python Level)
if type_filter != "All":
    # Filter the dataframe to only show the selected category
    df = df[df['source_keyword'] == type_filter]

if not df.empty:
    # --- PROFESSIONAL MAP (FOLIUM) ---
    
    # Create map centered on the USER'S selected search location
    m = folium.Map(location=[search_lat, search_lng], zoom_start=14, tiles="cartodbpositron")

    # A. Add the Office/Search Center Marker
    try:
        icon = folium.CustomIcon(
            icon_image="assets/logo_black.png",
            icon_size=(50, 50),
            icon_anchor=(25, 50),
            popup_anchor=(0, -50)
        )
        folium.Marker(
            location=[search_lat, search_lng],
            icon=icon,
            popup="📍Casta Carbonero",
            tooltip="Current Search Center"
        ).add_to(m)
    except:
        # Fallback if image missing
        folium.Marker(
            location=[search_lat, search_lng],
            popup="📍 SEARCH CENTER",
            icon=folium.Icon(color="black", icon="home")
        ).add_to(m)

    # B. Add Leads to Map
    for index, row in df.iterrows():
        color = STATUS_COLORS.get(row['status'], "#00FF00")
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(f"<b>{row['name']}</b><br>{row['source_keyword']}", max_width=200),
            tooltip=f"{row['name']} ({row['status']})"
        ).add_to(m)

    # Render Map
    st_folium(m, use_container_width=True, height=500)
    
    # Legend
    st.caption("📍 Center | 🟢 New | 🔵 Contacted | 🟡 Interested | 🔴 Ignored | ⚪ Closed")
    st.divider()

    # 3. THE LEADS LIST (WORK QUEUE)
    st.subheader(f"📋 Work Queue ({len(df)} leads)")
    
    for index, row in df.iterrows():
        status_icon = "🟢" if row['status'] == 'new' else "🔵"
        keyword_tag = f"[{row['source_keyword']}]" if row['source_keyword'] else ""
        
        with st.expander(f"{status_icon} {row['name']} {keyword_tag}"):
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.markdown(f"**Address:** {row['address']}")
                if row['phone']:
                    st.markdown(f"📞 [{row['phone']}](tel:{row['phone']})")
                else:
                    st.caption("No phone on file")
                
                # Notes
                current_note = row['notes'] if row['notes'] else ""
                new_note = st.text_area("Sales Notes", current_note, key=f"note_{row['place_id']}")
                if st.button("Save Note", key=f"sv_{row['place_id']}"):
                    db.update_lead_status(row['place_id'], row['status'], new_note)
                    st.success("Saved")

            with c2:
                st.write("**Update Status:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Contacted", key=f"con_{row['place_id']}"):
                        db.update_lead_status(row['place_id'], "contacted")
                        st.rerun()
                    if st.button("Interested", key=f"int_{row['place_id']}"):
                        db.update_lead_status(row['place_id'], "interested")
                        st.rerun()
                with col_b:
                    if st.button("Win/Close", key=f"win_{row['place_id']}"):
                        db.update_lead_status(row['place_id'], "closed")
                        st.rerun()
                    if st.button("Ignore", key=f"ig_{row['place_id']}"):
                        db.update_lead_status(row['place_id'], "ignored")
                        st.rerun()
else:
    st.info("No leads found matching your filters.")