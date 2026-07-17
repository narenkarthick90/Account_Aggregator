import os
from supabase import create_client, Client
import streamlit as st
import pandas as pd

# Initialize client using Streamlit secrets
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

def fetch_latest_financials():
    """Fetches the absolute latest entry point per asset/liability for calculations."""
    # Assets Query
    asset_res = supabase.table("asset_ledger").select(
        "id, asset_class, description, invested_amount, current_value, recorded_at, family_members(member_name)"
    ).order("recorded_at", desc=True).execute()
    
    # Liabilities Query
    liab_res = supabase.table("liability_ledger").select(
        "id, liability_class, bank_name, current_loan_amt, recorded_at, family_members(member_name)"
    ).order("recorded_at", desc=True).execute()
    
    return pd.DataFrame(asset_res.data), pd.DataFrame(liab_res.data)

def add_asset_entry(member_id, asset_class, description, invested, current):
    data = {
        "member_id": member_id,
        "asset_class": asset_class,
        "description": description,
        "invested_amount": invested,
        "current_value": current
    }
    return supabase.table("asset_ledger").insert(data).execute()