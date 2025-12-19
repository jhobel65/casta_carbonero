# src/database.py
import streamlit as st
from sqlalchemy import text
from datetime import datetime

class LeadsManager:
    def __init__(self):
        # Uses st.connection which handles caching and reconnection automatically
        self.conn = st.connection("supabase", type="sql")

    def get_leads(self, status_filter=None):
        query = "SELECT * FROM leads"
        params = {}
        
        if status_filter and status_filter != "All":
            query += " WHERE status = :status"
            params["status"] = status_filter.lower()
            
        # Return as Pandas DataFrame for easy mapping
        return self.conn.query(query, params=params, ttl=0)

    def add_lead(self, lead_data: dict):
        """
        Updated to include 'source_keyword'
        """
        sql = text("""
            INSERT INTO leads (place_id, name, phone, address, rating, latitude, longitude, status, source_keyword)
            VALUES (:place_id, :name, :phone, :address, :rating, :lat, :lng, 'new', :keyword)
            ON CONFLICT (place_id) DO UPDATE 
            SET source_keyword = :keyword -- Update keyword if we find them again with a better search
        """)
        with self.conn.session as s:
            s.execute(sql, lead_data)
            s.commit()

    def update_lead_status(self, place_id: str, new_status: str, note: str = None):
        sql = text("""
            UPDATE leads 
            SET status = :status, 
                notes = COALESCE(:note, notes), 
                updated_at = NOW() 
            WHERE place_id = :id
        """)
        with self.conn.session as s:
            s.execute(sql, {"status": new_status, "note": note, "id": place_id})
            s.commit()