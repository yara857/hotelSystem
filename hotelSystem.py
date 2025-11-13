import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="🏨 Hotel Management System", layout="wide")

DATA_FILE = "hotel_data.csv"

# ================== LOAD OR INITIALIZE DATA ==================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
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
menu = st.sidebar.radio("Select Action", ["Dashboard", "Register Guest", "Check-Out", "Available Rooms", "All Guests"])

# ================== DASHBOARD ==================
if menu == "Dashboard":
    st.title("🏨 Hotel Management Dashboard")

    total_rooms = len(rooms_df)
    occupied = (rooms_df["Status"].isin(["Occupied", "Booked"])).sum()
    available = total_rooms - occupied

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rooms", total_rooms)
    col2.metric("Occupied/Booked", occupied)
    col3.metric("Available", available)

    st.dataframe(rooms_df)

# ================== REGISTER GUEST ==================
elif menu == "Register Guest":
    st.title("🧾 Register a New Guest")

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
        status = "Occupied" if checkin_date <= datetime.today().date() <= checkout_date else "Booked"

        rooms_df.loc[idx, :] = [
            room_number,
            status,
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

# ================== CHECK-OUT ==================
elif menu == "Check-Out":
    st.title("🚪 Guest Check-Out")

    occupied_rooms = rooms_df[rooms_df["Status"].isin(["Occupied", "Booked"])]["Room Number"].tolist()
    if not occupied_rooms:
        st.info("✅ No guests to check out right now.")
    else:
        room_number = st.selectbox("Select Room to Check Out", occupied_rooms)
        guest_data = rooms_df[rooms_df["Room Number"] == room_number].iloc[0]

        st.write(f"**Guest Name:** {guest_data['Guest Name']}")
        st.write(f"**Check-in:** {guest_data['Check-in Date']}")
        st.write(f"**Check-out:** {guest_data['Check-out Date']}")
        st.write(f"**Total Cost:** {guest_data['Total Cost']} EGP")
        st.write(f"**Paid:** {guest_data['Paid']} EGP")
        st.write(f"**Remaining:** {guest_data['Remaining']} EGP")

        add_payment = st.number_input("Add Payment (EGP)", min_value=0.0, step=100.0)

        if st.button("Confirm Check-Out"):
            idx = rooms_df.index[rooms_df["Room Number"] == room_number][0]
            new_paid = guest_data["Paid"] + add_payment
            new_remaining = guest_data["Total Cost"] - new_paid

            if new_remaining > 0:
                st.warning(f"⚠️ Guest still owes {new_remaining:.2f} EGP.")
            else:
                # clear room info
                rooms_df.loc[idx, :] = [
                    room_number, "Available", "", "", "", "", "", 0, "", "", 0.0, 0.0, 0.0
                ]
                save_data(rooms_df)
                st.session_state.rooms = rooms_df
                st.success(f"✅ Room {room_number} checked out successfully!")

# ================== AVAILABLE ROOMS ==================
elif menu == "Available Rooms":
    st.title("🟩 Available Rooms")

    today = pd.Timestamp(datetime.today().date())
    checkout_dates = pd.to_datetime(rooms_df["Check-out Date"], errors='coerce')
    available_now = rooms_df[
        (rooms_df["Status"] == "Available") |
        (checkout_dates < today)
    ]

    st.write(f"Currently available rooms: **{len(available_now)}**")
    st.dataframe(available_now[["Room Number", "Status", "Guest Name", "Check-out Date"]])

# ================== ALL GUESTS ==================
elif menu == "All Guests":
    st.title("👥 All Guests Records")
    st.dataframe(rooms_df)

