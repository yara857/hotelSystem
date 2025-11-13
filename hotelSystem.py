import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="🏨 Hotel Management System", layout="wide")

DATA_FILE = "hotel_data.csv"

# ================== INITIALIZE DATA ==================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        # create base structure for 30 rooms
        rooms = []
        for i in range(1, 31):
            rooms.append({
                "Room Number": i,
                "Status": "Available",
                "Guest Name": "",
                "ID/Passport": "",
                "Address": "",
                "Job": "",
                "Nationality": "",
                "Nights": 0,
                "Check-in Date": "",
                "Check-out Date": "",
                "Paid": 0.0,
                "Total Cost": 0.0,
                "Remaining": 0.0
            })
        df = pd.DataFrame(rooms)
        df.to_csv(DATA_FILE, index=False)
        return df


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


# Load or initialize data
if "rooms" not in st.session_state:
    st.session_state.rooms = load_data()

rooms_df = st.session_state.rooms

# ================== SIDEBAR MENU ==================
st.sidebar.title("🏨 Hotel Menu")
menu = st.sidebar.radio("Select Action", ["Dashboard", "Register Guest", "Available Rooms", "All Guests"])

# ================== DASHBOARD ==================
if menu == "Dashboard":
    st.title("🏨 Hotel Management Dashboard")

    total_rooms = len(rooms_df)
    occupied = (rooms_df["Status"] == "Occupied").sum()
    available = total_rooms - occupied

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rooms", total_rooms)
    col2.metric("Occupied Rooms", occupied)
    col3.metric("Available Rooms", available)

    st.dataframe(rooms_df)

# ================== REGISTER GUEST ==================
elif menu == "Register Guest":
    st.title("🧾 Register a New Guest")

    # show all rooms (even occupied), since user might book for future
    room_number = st.selectbox("Select Room Number", rooms_df["Room Number"].tolist())

    guest_name = st.text_input("Guest Name")
    guest_id = st.text_input("ID or Passport Number")
    address = st.text_input("Address")
    job = st.text_input("Job")
    nationality = st.text_input("Nationality")
    nights = st.number_input("Number of Nights", min_value=1, max_value=60, step=1)
    checkin_date = st.date_input("Check-in Date", datetime.today())
    checkout_date = checkin_date + timedelta(days=int(nights))
    st.info(f"🗓️ Check-out Date: **{checkout_date.strftime('%Y-%m-%d')}**")

    total_price = st.number_input("Total Cost (EGP)", min_value=0.0, step=100.0)
    paid = st.number_input("Paid Amount (EGP)", min_value=0.0, step=100.0)
    remaining = total_price - paid

    if st.button("Register Guest"):
        idx = rooms_df.index[rooms_df["Room Number"] == room_number][0]

        # update info (but allow booking for future even if room used)
        rooms_df.loc[idx, :] = [
            room_number,
            "Occupied" if checkin_date <= datetime.today().date() <= checkout_date else "Booked",
            guest_name,
            guest_id,
            address,
            job,
            nationality,
            nights,
            checkin_date.strftime("%Y-%m-%d"),
            checkout_date.strftime("%Y-%m-%d"),
            paid,
            total_price,
            remaining
        ]

        save_data(rooms_df)
        st.session_state.rooms = rooms_df

        st.success(f"✅ Guest {guest_name} registered for Room {room_number}.")
        st.metric("Remaining to Pay", f"{remaining:.2f} EGP")

# ================== AVAILABLE ROOMS ==================
elif menu == "Available Rooms":
    st.title("🟩 Available Rooms")

    today = datetime.today().date()
    available_now = rooms_df[
        (rooms_df["Status"] == "Available") |
        (pd.to_datetime(rooms_df["Check-out Date"], errors='coerce').dt.date < today)
    ]

    st.write(f"Currently available rooms: **{len(available_now)}**")
    st.dataframe(available_now[["Room Number", "Status", "Guest Name", "Check-out Date"]])

# ================== ALL GUESTS ==================
elif menu == "All Guests":
    st.title("👥 All Guests Records")
    st.dataframe(rooms_df)
