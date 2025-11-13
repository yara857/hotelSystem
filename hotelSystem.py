import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Hotel Management System", layout="wide")

# === Initialize Current Rooms Data ===
if "rooms" not in st.session_state:
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

# === Initialize Reservations (future bookings) ===
if "reservations" not in st.session_state:
    st.session_state.reservations = pd.DataFrame(columns=[
        "Room Number", "Guest Name", "ID/Passport", "Address", "Job", "Nationality",
        "Check-in", "Check-out", "Nights", "Total", "Paid", "Remaining"
    ])

rooms_df = st.session_state.rooms
reservations_df = st.session_state.reservations

# === Sidebar Menu ===
st.sidebar.header("🏨 Hotel System Menu")
menu = st.sidebar.radio("Choose an action:", [
    "View Available Rooms",
    "Register / Reserve Guest",
    "Check-out Guest",
    "View Future Reservations"
])

# === View Available Rooms ===
if menu == "View Available Rooms":
    st.subheader("📋 Current Room Status")

    available = rooms_df[rooms_df["Status"] == "Available"]
    occupied = rooms_df[rooms_df["Status"] == "Occupied"]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Available Rooms", len(available))
        st.dataframe(available[["Room Number"]], use_container_width=True)
    with col2:
        st.metric("Occupied Rooms", len(occupied))
        st.dataframe(occupied[["Room Number", "Guest Name", "Check-out"]], use_container_width=True)

# === Register / Reserve Guest ===
elif menu == "Register / Reserve Guest":
    st.subheader("🧾 Register or Reserve a Room")

    all_rooms = rooms_df["Room Number"].tolist()
    room_number = st.selectbox("Select Room Number", all_rooms)
    guest_name = st.text_input("Guest Name")
    guest_id = st.text_input("ID or Passport Number")
    address = st.text_input("Address")
    job = st.text_input("Job")
    nationality = st.text_input("Nationality")
    nights = st.number_input("Number of Nights", min_value=1, max_value=30, step=1)
    checkin_date = st.date_input("Check-in Date", datetime.today())
    checkout_date = checkin_date + timedelta(days=int(nights))
    st.info(f"🗓️ Check-out Date: **{checkout_date.strftime('%Y-%m-%d')}**")

    total_price = st.number_input("Total Cost (EGP)", min_value=0.0, step=100.0)
    paid = st.number_input("Paid Amount (EGP)", min_value=0.0, step=100.0)
    remaining = total_price - paid

    if st.button("Save Booking"):
        if not guest_name or not guest_id:
            st.error("Please fill in all required fields (Name and ID/Passport).")
        else:
            current_room = rooms_df.loc[rooms_df["Room Number"] == room_number].iloc[0]

            # Check if room is available for the selected period
            room_available = True
            if current_room["Status"] == "Occupied" and current_room["Check-out"]:
                current_checkout = datetime.strptime(current_room["Check-out"], "%Y-%m-%d")
                if checkin_date <= current_checkout:
                    room_available = False

            if room_available:
                # If check-in is today or earlier -> occupy room now
                if checkin_date <= datetime.today().date():
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
                    st.success(f"✅ Guest {guest_name} checked into Room {room_number}.")
                else:
                    # Save as future reservation
                    new_res = {
                        "Room Number": room_number,
                        "Guest Name": guest_name,
                        "ID/Passport": guest_id,
                        "Address": address,
                        "Job": job,
                        "Nationality": nationality,
                        "Check-in": checkin_date.strftime("%Y-%m-%d"),
                        "Check-out": checkout_date.strftime("%Y-%m-%d"),
                        "Nights": nights,
                        "Total": total_price,
                        "Paid": paid,
                        "Remaining": remaining
                    }
                    st.session_state.reservations = pd.concat(
                        [st.session_state.reservations, pd.DataFrame([new_res])],
                        ignore_index=True
                    )
                    st.success(f"📅 Reservation saved for Room {room_number} ({guest_name}) on {checkin_date}.")
            else:
                st.error(f"❌ Room {room_number} is occupied until {current_room['Check-out']}.")

# === Check-out Guest ===
elif menu == "Check-out Guest":
    st.subheader("🚪 Check-out Guest")
    occupied_rooms = rooms_df[rooms_df["Status"] == "Occupied"]["Room Number"].tolist()

    if not occupied_rooms:
        st.info("No guests currently checked in.")
    else:
        room_number = st.selectbox("Select Room to Check-out", occupied_rooms)
        guest_info = rooms_df.loc[rooms_df["Room Number"] == room_number].iloc[0]

        st.write(f"**Guest Name:** {guest_info['Guest Name']}")
        st.write(f"**Check-in:** {guest_info['Check-in']}")
        st.write(f"**Check-out:** {guest_info['Check-out']}")
        st.write(f"**Remaining Balance:** {guest_info['Remaining']} EGP")

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

# === View Future Reservations ===
elif menu == "View Future Reservations":
    st.subheader("📅 Future Reservations")

    if len(reservations_df) == 0:
        st.info("No future reservations found.")
    else:
        st.dataframe(reservations_df, use_container_width=True)

# === Visualization (Summary Dashboard) ===
st.markdown("---")
st.subheader("📊 Room Summary Overview")

col1, col2 = st.columns(2)
with col1:
    st.bar_chart(rooms_df["Status"].value_counts())
with col2:
    st.metric("Total Future Reservations", len(reservations_df))
    st.dataframe(rooms_df, use_container_width=True)
