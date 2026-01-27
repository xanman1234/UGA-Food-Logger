import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- Configuration ---
st.set_page_config(page_title="Macro Master Pro", layout="wide")

DB_NAME = "nutrition_vault.db"

# --- Database Management ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Ensure tables include Sugar (AM column in CSV)
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

# --- App UI ---
st.title("🥑 Macro Tracker & CSV Library")

tab1, tab2 = st.tabs(["📝 Log Meals", "📖 Manage Food Library"])

# --- TAB 2: Food Library & CSV Import ---
with tab2:
    st.subheader("Bulk Import from CSV")
    st.info("Upload a CSV where: J=Name, W=Cals, Y=Fat, AI=Carbs, AM=Sugar, AO=Protein. (Skips header row)")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        if st.button("🚀 Process and Save CSV to Library"):
            try:
                # Column indices (0-based): J=9, W=22, Y=24, AI=34, AM=38, AO=40
                # Using encoding='cp1252' to handle special characters from Excel exports
                df_import = pd.read_csv(
                    uploaded_file, 
                    skiprows=1, 
                    header=None, 
                    usecols=[9, 22, 24, 34, 38, 40],
                    encoding='cp1252'
                )
                df_import.columns = ['name', 'calories', 'fat', 'carbs', 'sugar', 'protein']
                
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                for _, row in df_import.iterrows():
                    if pd.isna(row['name']): continue
                    c.execute('''INSERT OR REPLACE INTO food_library 
                                 (food_name, cal_per_100, prot_per_100, carb_per_100, fat_per_100, sugar_per_100) 
                                 VALUES (?, ?, ?, ?, ?, ?)''', 
                              (str(row['name']), row['calories'], row['protein'], row['carbs'], row['fat'], row['sugar']))
                conn.commit()
                conn.close()
                st.success(f"Successfully imported {len(df_import)} items!")
            except Exception as e:
                st.error(f"Error processing CSV: {e}")

    st.markdown("---")
    
    # Library Search/View section
    st.subheader("Your Food Library")
    conn = sqlite3.connect(DB_NAME)
    full_lib = pd.read_sql_query("SELECT * FROM food_library", conn)
    conn.close()
    
    if not full_lib.empty:
        search_query = st.text_input("🔍 Search Library", placeholder="Search for a food name...")
        if search_query:
            filtered_lib = full_lib[full_lib['food_name'].str.contains(search_query, case=False, na=False)]
            st.dataframe(filtered_lib, use_container_width=True, hide_index=True)
        else:
            st.dataframe(full_lib.head(10), use_container_width=True, hide_index=True)
            st.caption("Showing first 10 items. Use the search bar above to find specific foods.")

# --- TAB 1: Daily Logger ---
with tab1:
    conn = sqlite3.connect(DB_NAME)
    library_df = pd.read_sql_query("SELECT * FROM food_library", conn)
    conn.close()

    st.subheader("Log a Meal")
    use_custom = st.checkbox("Select from Library")
    
    with st.form("log_form"):
        date_sel = st.date_input("Date", date.today())
        meal_sel = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snack"])
        
        if use_custom and not library_df.empty:
            # Sort library for easier selection
            food_list = sorted(library_df['food_name'].tolist())
            selected_food = st.selectbox("Select Food", food_list)
            grams = st.number_input("Amount (grams / units)", min_value=1.0, value=100.0)
            
            f_data = library_df[library_df['food_name'] == selected_food].iloc[0]
            mult = grams / 100.0
            
            # Mapping indices: name=0, cal=1, prot=2, carb=3, fat=4, sugar=5
            fname, fcal, fprot, fcarb, ffat, fsug = selected_food, f_data[1]*mult, f_data[2]*mult, f_data[3]*mult, f_data[4]*mult, f_data[5]*mult
            st.info(f"Calculated: {fcal:.1f} kcal | P: {fprot:.1f}g | C: {fcarb:.1f}g | F: {ffat:.1f}g | S: {fsug:.1f}g")
        else:
            fname = st.text_input("Food Name")
            c1, c2, c3, c4, c5 = st.columns(5)
            fcal = c1.number_input("Cals", 0.0)
            fprot = c2.number_input("Prot", 0.0)
            fcarb = c3.number_input("Carbs", 0.0)
            ffat = c4.number_input("Fat", 0.0)
            fsug = c5.number_input("Sugar", 0.0)

        if st.form_submit_button("Log Entry"):
            if fname:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO food_log (date, food_name, meal_type, calories, protein, carbs, fat, sugar) VALUES (?,?,?,?,?,?,?,?)",
                           (date_sel.strftime("%Y-%m-%d"), fname, meal_sel, fcal, fprot, fcarb, ffat, fsug))
                conn.commit()
                conn.close()
                st.rerun()

    # --- Daily Summary Section ---
    st.markdown("---")
    conn = sqlite3.connect(DB_NAME)
    log_df = pd.read_sql_query("SELECT * FROM food_log", conn)
    conn.close()

    if not log_df.empty:
        view_date = st.date_input("View Log for:", date.today())
        view_date_str = view_date.strftime("%Y-%m-%d")
        day_df = log_df[log_df['date'] == view_date_str]
        
        if not day_df.empty:
            cols = st.columns(5)
            cols[0].metric("Calories", f"{day_df['calories'].sum():.0f}")
            cols[1].metric("Protein", f"{day_df['protein'].sum():.1f}g")
            cols[2].metric("Carbs", f"{day_df['carbs'].sum():.1f}g")
            cols[3].metric("Fat", f"{day_df['fat'].sum():.1f}g")
            cols[4].metric("Sugar", f"{day_df['sugar'].sum():.1f}g")
            
            st.dataframe(day_df.drop(columns=['id']), use_container_width=True, hide_index=True)
            
            st.markdown("### 🛠️ Danger Zone")
            if st.checkbox("Enable Deletion"):
                if st.button(f"🔥 Clear All Entries for {view_date_str}"):
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("DELETE FROM food_log WHERE date=?", (view_date_str,))
                    conn.commit()
                    conn.close()
                    st.rerun()
        else:
            st.info(f"No entries found for {view_date_str}.")
    else:
        st.info("Start logging your food to see your daily totals!")