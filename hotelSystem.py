import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Hotel Management System", layout="wide")

# === Initialize Data ===
if "rooms" not in st.session_state:
    # Create 30 rooms initially all available
    st.session_state.rooms = pd.DataFrame({
        "Room Number": list(range(1, 31)),
        "Status": ["Available"] * 30,
        "Guest Name": [None] * 30,
        "ID/Passport": [None] * 30,
        "Address": [None] * 30,
        "Job": [None] * 30,
        "Nationality": [None] * 30,
        "Nights": [None] * 30,
        "Check-in": [None] * 30,
        "Check-out": [None] * 30,
        "Paid": [0.0] * 30,
        "Total": [0.0] * 30,
        "Remaining": [0.0] * 30,
    })

rooms_df = st.session_state.rooms

# === Sidebar ===
st.sidebar.header("🏨 Hotel System Menu")
menu = st.sidebar.radio("Choose an action:", ["View Available Rooms", "Register Guest", "Check-out Guest"])

# === View Available Rooms ===
if menu == "View Available Rooms":
    st.subheader("📋 Available Rooms Overview")

    available = rooms_df[rooms_df["Status"] == "Available"]
    occupied = rooms_df[rooms_df["Status"] == "Occupied"]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Available Rooms", len(available))
        st.dataframe(available[["Room Number"]], use_container_width=True)

    with col2:
        st.metric("Occupied Rooms", len(occupied))
        st.dataframe(
            occupied[["Room Number", "Guest Name", "Check-out"]],
            use_container_width=True
        )

# === Register Guest ===
elif menu == "Register Guest":
    st.subheader("🧾 Register a New Guest")

    available_rooms = rooms_df[rooms_df["Status"] == "Available"]["Room Number"].tolist()
    if not available_rooms:
        st.warning("❌ No rooms available.")
    else:
        with st.form("register_form"):
            col1, col2 = st.columns(2)

            with col1:
                room_number = st.selectbox("Select Room Number", available_rooms)
                guest_name = st.text_input("Guest Name")
                guest_id = st.text_input("ID or Passport Number")
                address = st.text_input("Address")
                job = st.text_input("Job")
                nationality = st.text_input("Nationality")
                nights = st.number_input("Number of Nights", min_value=1, max_value=30, step=1)
            
            with col2:
                checkin_date = st.date_input("Check-in Date", datetime.today())
                checkout_date = checkin_date + timedelta(days=nights)
                st.write("**Check-out Date:**", checkout_date)
                total_price = st.number_input("Total Cost (EGP)", min_value=0.0, step=100.0)
                paid = st.number_input("Paid Amount (EGP)", min_value=0.0, step=100.0)
                remaining = total_price - paid

            submitted = st.form_submit_button("Register Guest")

        if submitted:
            idx = rooms_df.index[rooms_df["Room Number"] == room_number][0]
            st.session_state.rooms.loc[idx, :] = [
                room_number,
                "Occupied",
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
            st.success(f"✅ Guest {guest_name} registered in Room {room_number}.")
            st.metric("Remaining to Pay", f"{remaining:.2f} EGP")

# === Check-out Guest ===
elif menu == "Check-out Guest":
    st.subheader("🚪 Check-out Guest")
    occupied_rooms = rooms_df[rooms_df["Status"] == "Occupied"]["Room Number"].tolist()

    if not occupied_rooms:
        st.info("No guests currently checked in.")
    else:
        room_number = st.selectbox("Select Room Number to Check-out", occupied_rooms)
        guest_info = rooms_df.loc[rooms_df["Room Number"] == room_number].iloc[0]

        st.write(f"**Guest:** {guest_info['Guest Name']}")
        st.write(f"**Remaining to Pay:** {guest_info['Remaining']} EGP")

        if st.button("Confirm Check-out"):
            idx = rooms_df.index[rooms_df["Room Number"] == room_number][0]
            st.session_state.rooms.loc[idx, :] = [
                room_number,
                "Available",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                0.0,
                0.0,
                0.0
            ]
            st.success(f"✅ Room {room_number} is now available again.")

# === Visualization (Summary Dashboard) ===
st.markdown("---")
st.subheader("📊 Room Occupancy Summary")

col1, col2 = st.columns(2)
with col1:
    st.bar_chart(rooms_df["Status"].value_counts())

with col2:
    st.dataframe(rooms_df, use_container_width=True)
