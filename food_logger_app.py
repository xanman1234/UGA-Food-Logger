import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- Configuration ---
st.set_page_config(
    page_title="Macronutrient & Food Logger",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Database Management ---

DB_NAME = "food_log.db"

def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            food_name TEXT,
            meal_type TEXT,
            calories INTEGER,
            protein INTEGER,
            carbs INTEGER,
            fat INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def add_food_entry(entry_date, food_name, meal_type, calories, protein, carbs, fat):
    """Inserts a new food record into the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO food_log (date, food_name, meal_type, calories, protein, carbs, fat)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (entry_date, food_name, meal_type, calories, protein, carbs, fat))
    conn.commit()
    conn.close()
    st.success(f"Added **{food_name}** to your log!")

def get_log_dataframe():
    """Fetches all data from the database and returns it as a Pandas DataFrame."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM food_log", conn)
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# Initialize the DB when the app starts
init_db()

# --- Streamlit UI ---

st.title("Macro & Food Tracker")
st.markdown("Log your meals, track your macros, and keep your data saved.")

# --- 1. Food Logging Form ---
with st.form(key='food_entry_form'):
    st.subheader("Add New Entry")

    # Row 1: Basic Info
    col1, col2 = st.columns(2)
    with col1:
        input_date = st.date_input("Date", value=date.today())
    with col2:
        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])

    food_name = st.text_input("Food Name", placeholder="e.g., Grilled Chicken Breast")

    st.markdown("**Nutritional Info:**")
    
    # Row 2: Macros (The requested boxes)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        calories = st.number_input("Calories (kcal)", min_value=0, step=10, value=0)
    with c2:
        protein = st.number_input("Protein (g)", min_value=0, step=1, value=0)
    with c3:
        carbs = st.number_input("Carbs (g)", min_value=0, step=1, value=0)
    with c4:
        fat = st.number_input("Fat (g)", min_value=0, step=1, value=0)

    # Submission
    submit_button = st.form_submit_button("Save Entry")

    if submit_button:
        if food_name:
            add_food_entry(
                input_date.strftime("%Y-%m-%d"), 
                food_name, 
                meal_type, 
                calories, 
                protein, 
                carbs, 
                fat
            )
        else:
            st.error("Please enter a food name.")

st.markdown("---")

# --- 2. View History & Statistics ---

st.subheader("Daily Summary")

# Load data
df = get_log_dataframe()

if not df.empty:
    # Get unique dates for the filter dropdown
    unique_dates = sorted(df['date'].dt.date.unique(), reverse=True)
    
    selected_date = st.selectbox(
        "Select Date to View:", 
        options=unique_dates,
        format_func=lambda x: x.strftime("%A, %B %d, %Y")
    )

    # Filter data for selected date
    daily_df = df[df['date'].dt.date == selected_date]

    if not daily_df.empty:
        # 2A. Scorecard Metrics
        total_cals = daily_df['calories'].sum()
        total_prot = daily_df['protein'].sum()
        total_carbs = daily_df['carbs'].sum()
        total_fat = daily_df['fat'].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Calories", f"{total_cals}")
        m2.metric("Protein", f"{total_prot}g")
        m3.metric("Carbs", f"{total_carbs}g")
        m4.metric("Fat", f"{total_fat}g")

        # 2B. Detailed Table
        st.caption(f"Log for {selected_date.strftime('%B %d, %Y')}")
        st.dataframe(
            daily_df[['meal_type', 'food_name', 'calories', 'protein', 'carbs', 'fat']],
            use_container_width=True,
            hide_index=True
        )
        
        # 2C. Delete Option (Optional helper)
        with st.expander("Manage Records"):
            entry_to_delete = st.selectbox("Select entry to delete:", daily_df['food_name'])
            if st.button("Delete Selected Entry"):
                # Ideally you'd delete by ID, but for simplicity we show the concept
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                # Find the specific ID for this day/food to be safe
                row_id = daily_df[daily_df['food_name'] == entry_to_delete].iloc[0]['id']
                c.execute("DELETE FROM food_log WHERE id=?", (int(row_id),))
                conn.commit()
                conn.close()
                st.rerun() # Refresh the app

    else:
        st.info("No entries found for this date.")
else:
    st.info("No data logged yet. Start by adding a meal above!")