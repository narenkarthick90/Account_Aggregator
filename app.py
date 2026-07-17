import streamlit as st
import plotly.express as px
import pandas as pd

# 1. THIS MUST BE THE FIRST STREAMLIT COMMAND IN THE FILE
st.set_page_config(page_title="Family Wealth Aggregator", layout="wide")

# 2. NOW IMPORT YOUR CUSTOM DATABASE FUNCTIONS
from database import fetch_latest_financials, add_asset_entry

# --- Mock Session Authentication for Setup ---
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = True
    st.session_state.user_role = "Admin"  # Change to 'Editor' or 'Viewer' to test UI variance
    st.session_state.username = "Head Of Family"

# --- Title Header ---
st.title("🛡️ Family Wealth Control Center")
st.caption(f"Logged in as: **{st.session_state.username}** ({st.session_state.user_role} Mode)")
st.markdown("---")

# --- Fetch Data ---
assets_df, liab_df = fetch_latest_financials()

# --- Setup Views based on Role ---
if st.session_state.user_role in ["Admin", "Editor", "Viewer"]:
    tab_dashboard, tab_breakdown, tab_management = st.tabs(["📊 Main Dashboard", "🔎 Deep Dive Analysis", "✏️ Update Balances"])
    
    # ==========================================
    # TAB 1: MAIN DASHBOARD
    # ==========================================
    with tab_dashboard:
        col1, col2, col3 = st.columns(3)
        
        # Format metrics gracefully
        total_assets = assets_df['current_value'].sum() if not assets_df.empty else 0
        total_liab = liab_df['current_loan_amt'].sum() if not liab_df.empty else 0
        net_worth = total_assets - total_liab
        
        col1.metric("Total Consolidated Assets", f"₹{total_assets:,.2f}")
        col2.metric("Total Outstanding Liabilities", f"₹{total_liab:,.2f}")
        col3.metric("Net Family Equity", f"₹{net_worth:,.2f}")
        
        st.markdown("### Asset Allocation Mapping")
        if not assets_df.empty:
            # Flatten joined structural queries for mapping
            assets_df['Family Member'] = assets_df['family_members'].apply(lambda x: x['member_name'] if isinstance(x, dict) else 'Unknown')
            
            fig = px.pie(assets_df, values='current_value', names='asset_class', 
                         title="Asset Splits Across Portfolio Classifications", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
    # ==========================================
    # TAB 2: DEEP DIVE VIEW
    # ==========================================
    with tab_breakdown:
        st.subheader("Granular View per Family Member Profile")
        if not assets_df.empty:
            selected_member = st.selectbox("Filter by Family Identity Slot", assets_df['Family Member'].unique())
            filtered_df = assets_df[assets_df['Family Member'] == selected_member]
            st.dataframe(filtered_df[['asset_class', 'description', 'invested_amount', 'current_value', 'recorded_at']], use_container_width=True)

    # ==========================================
    # TAB 3: UPDATE PRIVILEGES (Write/Modify Guard)
    # ==========================================
    # ==========================================
    # TAB 3: UPDATE PRIVILEGES (Write/Modify Guard)
    # ==========================================
    with tab_management:
        if st.session_state.user_role in ["Admin", "Editor"]:
            st.subheader("Log a New Asset Entry/Snapshot Update")
            
            # 1. The Selectbox MUST sit outside the form to trigger an instant UI change
            chosen_class = st.selectbox(
                "Select Asset Class", 
                ["Mutual Fund", "Sovereign Gold Bond", "Fixed Deposit", "Insurance", "Savings Account"]
            )
            
            # 2. Now start the form
            with st.form("manual_entry_form", clear_on_submit=True):
                member_mapping = {"AK HUF": 1, "AK IND": 2, "KP HUF": 3, "KP IND": 4, "KV": 5, "ABI": 6, "PT": 7}
                chosen_member = st.selectbox("Account Holder Identity", list(member_mapping.keys()))
                
                st.markdown("---")
                
                # 3. Dynamically swap input boxes based on the external selection
                if chosen_class == "Mutual Fund":
                    desc = st.text_input("Fund Name (e.g., SBI Bluechip)")
                    val_invested = st.number_input("Total Invested Amount (INR)", min_value=0.0, step=1000.0)
                    val_current = st.number_input("Current NAV Value (INR)", min_value=0.0, step=1000.0)
                    units = None
                    
                elif chosen_class == "Sovereign Gold Bond":
                    desc = st.text_input("SGB Series / Nominee")
                    units = st.number_input("Units (Grams)", min_value=0.0, step=1.0)
                    val_invested = st.number_input("Total Purchase Rate (INR)", min_value=0.0, step=1000.0)
                    val_current = st.number_input("Current Appraised Amount (INR)", min_value=0.0, step=1000.0)
                    
                elif chosen_class == "Fixed Deposit":
                    desc = st.text_input("FDR No. & Bank Name")
                    val_invested = st.number_input("Principal Amount (INR)", min_value=0.0, step=1000.0)
                    val_current = st.number_input("Maturity Amount (INR)", min_value=0.0, step=1000.0)
                    units = None
                    
                elif chosen_class == "Insurance":
                    desc = st.text_input("Policy No. & Type (Term/Returnable)")
                    val_invested = st.number_input("Total Premium Paid (INR)", min_value=0.0, step=1000.0)
                    val_current = st.number_input("Current/Maturity Amount (INR)", min_value=0.0, step=1000.0)
                    units = None
                    
                else: # Default Fallback (Savings)
                    desc = st.text_input("Bank / Account Details")
                    val_invested = st.number_input("Baseline Balance (INR)", min_value=0.0, step=1000.0)
                    val_current = st.number_input("Current Balance (INR)", min_value=0.0, step=1000.0)
                    units = None

                st.markdown("---")
                submit_btn = st.form_submit_button("Commit Changes to Supabase")
                
                if submit_btn:
                    # Optional: append units to description if it's SGB
                    if units is not None:
                        desc = f"{desc} ({units}g)"
                        
                    add_asset_entry(member_mapping[chosen_member], chosen_class, desc, val_invested, val_current)
                    st.success(f"Successfully recorded update entry for {chosen_member} -> {chosen_class}!")
        else:
            st.warning("🔒 Access Denied. Your credential level ('Viewer') restricts write operations to this database.")