import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- Configuration ---
st.set_page_config(page_title="Macro Master", layout="wide")

DB_NAME = "nutrition_vault.db"

# --- Database Management ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Table for daily logs
    c.execute('''CREATE TABLE IF NOT EXISTS food_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, food_name TEXT, meal_type TEXT, 
                    calories REAL, protein REAL, carbs REAL, fat REAL)''')
    # Table for custom food library (values stored per 100g)
    c.execute('''CREATE TABLE IF NOT EXISTS food_library (
                    food_name TEXT PRIMARY KEY, 
                    cal_per_100 REAL, prot_per_100 REAL, 
                    carb_per_100 REAL, fat_per_100 REAL)''')
    conn.commit()
    conn.close()

def add_to_library(name, c, p, carb, f):
    try:
        conn = sqlite3.connect(DB_NAME)
        c_db = conn.cursor()
        c_db.execute("INSERT OR REPLACE INTO food_library VALUES (?, ?, ?, ?, ?)", (name, c, p, carb, f))
        conn.commit()
        conn.close()
        return True
    except Exception: return False

init_db()

# --- App UI ---
st.title("Macro Tracker & Food Library")

tab1, tab2 = st.tabs(["Log Meals", "Manage Food Library"])

# --- TAB 2: Food Library (Create Custom Foods) ---
with tab2:
    st.subheader("Add Food to Library (Values per 100g)")
    with st.form("library_form"):
        lib_name = st.text_input("Food Name (e.g., Chicken Breast)")
        col1, col2, col3, col4 = st.columns(4)
        l_cal = col1.number_input("Cals / 100g", min_value=0.0)
        l_prot = col2.number_input("Protein / 100g", min_value=0.0)
        l_carb = col3.number_input("Carbs / 100g", min_value=0.0)
        l_fat = col4.number_input("Fat / 100g", min_value=0.0)
        
        if st.form_submit_button("Save to Library"):
            if lib_name:
                add_to_library(lib_name, l_cal, l_prot, l_carb, l_fat)
                st.success(f"Saved {lib_name} to your library!")
            else:
                st.error("Please enter a food name.")

# --- TAB 1: Daily Logger ---
with tab1:
    # Fetch library for the dropdown
    conn = sqlite3.connect(DB_NAME)
    library_df = pd.read_sql_query("SELECT * FROM food_library", conn)
    conn.close()

    st.subheader("Log a Meal")
    
    # 1. Choose from Library or Manual
    use_custom = st.checkbox("Use a food from my library")
    
    with st.form("log_form"):
        date_sel = st.date_input("Date", date.today())
        meal_sel = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snack"])
        
        if use_custom and not library_df.empty:
            selected_food = st.selectbox("Select Food", library_df['food_name'].tolist())
            grams = st.number_input("Amount (grams)", min_value=1.0, value=100.0)
            
            # Auto-calculation logic
            food_data = library_df[library_df['food_name'] == selected_food].iloc[0]
            multiplier = grams / 100.0
            
            final_name = selected_food
            final_cal = food_data['cal_per_100'] * multiplier
            final_prot = food_data['prot_per_100'] * multiplier
            final_carb = food_data['carb_per_100'] * multiplier
            final_fat = food_data['fat_per_100'] * multiplier
            
            st.info(f"Calculated: {final_cal:.1f} kcal | P: {final_prot:.1f}g | C: {final_carb:.1f}g | F: {final_fat:.1f}g")
        else:
            final_name = st.text_input("Food Name")
            c1, c2, c3, c4 = st.columns(4)
            final_cal = c1.number_input("Calories", 0.0)
            final_prot = c2.number_input("Protein", 0.0)
            final_carb = c3.number_input("Carbs", 0.0)
            final_fat = c4.number_input("Fat", 0.0)

        if st.form_submit_button("Log Entry"):
            conn = sqlite3.connect(DB_NAME)
            c_db = conn.cursor()
            c_db.execute("INSERT INTO food_log (date, food_name, meal_type, calories, protein, carbs, fat) VALUES (?,?,?,?,?,?,?)",
                       (date_sel.strftime("%Y-%m-%d"), final_name, meal_sel, final_cal, final_prot, final_carb, final_fat))
            conn.commit()
            conn.close()
            st.rerun()

    # --- Display Today's Summary ---
    st.markdown("---")
    conn = sqlite3.connect(DB_NAME)
    log_df = pd.read_sql_query("SELECT * FROM food_log", conn)
    conn.close()

    if not log_df.empty:
        today_str = date.today().strftime("%Y-%m-%d")
        day_df = log_df[log_df['date'] == today_str]
        
        st.subheader(f"Today's Totals ({today_str})")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Calories", f"{day_df['calories'].sum():.0f}")
        m2.metric("Protein", f"{day_df['protein'].sum():.1f}g")
        m3.metric("Carbs", f"{day_df['carbs'].sum():.1f}g")
        m4.metric("Fat", f"{day_df['fat'].sum():.1f}g")
        
        st.dataframe(day_df[['meal_type', 'food_name', 'calories', 'protein', 'carbs', 'fat']], use_container_width=True)