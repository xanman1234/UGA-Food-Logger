import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- Configuration ---
st.set_page_config(page_title="Macro Master Pro", layout="wide")
DB_NAME = "nutrition_vault.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS food_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, food_name TEXT, meal_type TEXT, 
                    calories REAL, protein REAL, carbs REAL, fat REAL, sugar REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS food_library (
                    food_name TEXT PRIMARY KEY, 
                    cal_per_100 REAL, prot_per_100 REAL, 
                    carb_per_100 REAL, fat_per_100 REAL, sugar_per_100 REAL)''')
    conn.commit()
    conn.close()

init_db()

st.title("🥑 Macro Tracker & CSV Library")
tab1, tab2 = st.tabs(["📝 Log Meals", "📖 Manage Food Library"])

# --- TAB 2: Food Library ---
with tab2:
    st.subheader("Bulk Import from CSV")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        if st.button("🚀 Process CSV"):
            try:
                df_import = pd.read_csv(uploaded_file, skiprows=1, header=None, usecols=[9, 22, 24, 34, 38, 40], encoding='cp1252')
                df_import.columns = ['name', 'calories', 'fat', 'carbs', 'sugar', 'protein']
                
                # FIX: Force columns to be numeric, turning errors into 0
                for col in ['calories', 'fat', 'carbs', 'sugar', 'protein']:
                    df_import[col] = pd.to_numeric(df_import[col], errors='coerce').fillna(0)
                
                conn = sqlite3.connect(DB_NAME)
                for _, row in df_import.iterrows():
                    if pd.isna(row['name']): continue
                    conn.execute('''INSERT OR REPLACE INTO food_library VALUES (?, ?, ?, ?, ?, ?)''', 
                                 (str(row['name']), row['calories'], row['protein'], row['carbs'], row['fat'], row['sugar']))
                conn.commit()
                conn.close()
                st.success("Import Successful!")
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 1: Daily Logger ---
with tab1:
    conn = sqlite3.connect(DB_NAME)
    library_df = pd.read_sql_query("SELECT * FROM food_library", conn)
    conn.close()

    st.subheader("Log a Meal")
    # Moved the toggle OUTSIDE the form to prevent the "Missing Submit Button" error
    use_custom = st.checkbox("Select from Library")
    
    with st.form("log_form", clear_on_submit=True):
        date_sel = st.date_input("Date", date.today())
        meal_sel = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snack"])
        
        if use_custom and not library_df.empty:
            food_list = sorted(library_df['food_name'].tolist())
            selected_food = st.selectbox("Select Food", food_list)
            grams = st.number_input("Amount (grams / units)", min_value=0.1, value=100.0)
            
            f_data = library_df[library_df['food_name'] == selected_food].iloc[0]
            mult = float(grams) / 100.0
            
            # Use column names instead of indices to be safer
            fname = selected_food
            fcal = float(f_data['cal_per_100']) * mult
            fprot = float(f_data['prot_per_100']) * mult
            fcarb = float(f_data['carb_per_100']) * mult
            ffat = float(f_data['fat_per_100']) * mult
            fsug = float(f_data['sugar_per_100']) * mult
            st.info(f"Calculated: {fcal:.1f} kcal | P: {fprot:.1f}g | C: {fcarb:.1f}g")
        else:
            fname = st.text_input("Food Name")
            c1, c2, c3, c4, c5 = st.columns(5)
            fcal = c1.number_input("Cals", 0.0)
            fprot = c2.number_input("Prot", 0.0)
            fcarb = c3.number_input("Carbs", 0.0)
            ffat = c4.number_input("Fat", 0.0)
            fsug = c5.number_input("Sugar", 0.0)

        # The Button MUST be at the bottom level of the 'with st.form' block
        submitted = st.form_submit_button("Log Entry")
        if submitted and fname:
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO food_log (date, food_name, meal_type, calories, protein, carbs, fat, sugar) VALUES (?,?,?,?,?,?,?,?)",
                       (date_sel.strftime("%Y-%m-%d"), fname, meal_sel, fcal, fprot, fcarb, ffat, fsug))
            conn.commit()
            conn.close()
            st.rerun()

    # --- Summary ---
    st.markdown("---")
    conn = sqlite3.connect(DB_NAME)
    log_df = pd.read_sql_query("SELECT * FROM food_log", conn)
    conn.close()

    if not log_df.empty:
        view_date = st.date_input("View Log for:", date.today())
        day_df = log_df[log_df['date'] == view_date.strftime("%Y-%m-%d")]
        if not day_df.empty:
            st.dataframe(day_df.drop(columns=['id']), use_container_width=True, hide_index=True)
            st.metric("Total Calories", f"{day_df['calories'].sum():.0f} kcal")