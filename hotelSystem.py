# hotel_system.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="🏨 Hotel Management System", layout="wide")

ROOMS_FILE = "rooms_data.csv"
RES_FILE = "reservations.csv"

def init_rooms_file():
    rooms = []
    for i in range(1, 31):
        rooms.append({
            "Room Number": i,
            "Status": "Available",   # Available or Occupied
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
    df.to_csv(ROOMS_FILE, index=False)
    return df

def init_res_file():
    df = pd.DataFrame(columns=[
        "Reservation ID", "Room Number", "Guest Name", "ID/Passport", "Address", "Job", "Nationality",
        "Nights", "Check-in Date", "Check-out Date", "Paid", "Total Cost", "Remaining"
    ])
    df.to_csv(RES_FILE, index=False)
    return df

def load_rooms():
    if not os.path.exists(ROOMS_FILE):
        return init_rooms_file()
    df = pd.read_csv(ROOMS_FILE, dtype={"Room Number": int})
    return df

def load_reservations():
    if not os.path.exists(RES_FILE):
        return init_res_file()
    df = pd.read_csv(RES_FILE)
    # Ensure Reservation ID exists (integer)
    if "Reservation ID" not in df.columns:
        df.insert(0, "Reservation ID", range(1, len(df) + 1))
    return df

def save_rooms(df):
    df.to_csv(ROOMS_FILE, index=False)

def save_reservations(df):
    df.to_csv(RES_FILE, index=False)

# Load data into session_state
if "rooms" not in st.session_state:
    st.session_state.rooms = load_rooms()
if "reservations" not in st.session_state:
    st.session_state.reservations = load_reservations()

rooms_df = st.session_state.rooms
res_df = st.session_state.reservations

# Helper functions
def parse_date(s):
    if pd.isna(s) or s == "":
        return None
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return None

def overlap_period(start_a, end_a, start_b, end_b):
    """Return True if [start_a, end_a) overlaps [start_b, end_b) using dates."""
    if start_a is None or end_a is None or start_b is None or end_b is None:
        return False
    return (start_a < end_b) and (end_a > start_b)

def next_reservation_for_room(room_number):
    """Return earliest reservation row for a room (as Series) or None."""
    df = st.session_state.reservations.copy()
    if df.empty:
        return None
    df_room = df[df["Room Number"] == int(room_number)].copy()
    if df_room.empty:
        return None
    df_room["Check-in Date"] = pd.to_datetime(df_room["Check-in Date"], errors='coerce')
    df_room = df_room.sort_values("Check-in Date")
    return df_room.iloc[0]

def remove_reservation_by_id(res_id):
    df = st.session_state.reservations
    st.session_state.reservations = df[df["Reservation ID"] != res_id].reset_index(drop=True)
    save_reservations(st.session_state.reservations)

# Sidebar menu
st.sidebar.title("🏨 Hotel Menu")
menu = st.sidebar.radio("Select Action", ["Dashboard", "Register Guest", "Check-Out", "Analytics", "Reservations"])

# Dashboard
if menu == "Dashboard":
    st.title("🏨 Hotel Dashboard")
    rooms_df = st.session_state.rooms
    total = len(rooms_df)
    occupied = (rooms_df["Status"] == "Occupied").sum()
    available = (rooms_df["Status"] == "Available").sum()
    res_count = len(st.session_state.reservations)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Rooms", total)
    c2.metric("Occupied Now", occupied)
    c3.metric("Future Reservations", res_count)

    st.markdown("#### Current Rooms Table")
    st.dataframe(rooms_df)

# Register Guest
elif menu == "Register Guest":
    st.title("🧾 Register / Reserve a Guest")

    rooms_df = st.session_state.rooms
    res_df = st.session_state.reservations

    room_number = st.selectbox("Select Room Number", rooms_df["Room Number"].tolist())

    guest_name = st.text_input("Guest Name")
    guest_id = st.text_input("ID or Passport Number")
    address = st.text_input("Address")
    job = st.text_input("Job")
    nationality = st.text_input("Nationality")

    nights = st.number_input("Number of Nights", min_value=1, max_value=365, value=1, step=1)
    checkin_date = st.date_input("Check-in Date", datetime.today())
    checkout_date = st.date_input("Check-out Date", checkin_date + timedelta(days=nights))
    # Keep checkout dynamic if user changes nights
    # (we show both but allow user to choose)
    st.info(f"Calculated checkout (checkin + nights): {(checkin_date + timedelta(days=nights)).strftime('%Y-%m-%d')}")

    total_price = st.number_input("Total Cost (EGP)", min_value=0.0, step=1.0)
    paid = st.number_input("Paid Amount (EGP)", min_value=0.0, step=1.0)
    remaining = total_price - paid

    if st.button("Save Booking"):
        if not guest_name.strip() or not guest_id.strip():
            st.error("Please enter Guest Name and ID/Passport.")
        else:
            # Check overlaps against current occupant (if any) and existing reservations for this room
            idx = rooms_df.index[rooms_df["Room Number"] == room_number][0]
            current_checkin = parse_date(rooms_df.loc[idx, "Check-in Date"])
            current_checkout = parse_date(rooms_df.loc[idx, "Check-out Date"])
            new_start = checkin_date
            new_end = checkout_date

            conflict = False
            conflict_msgs = []

            # 1) Check against current occupant (if room is Occupied)
            if rooms_df.loc[idx, "Status"] == "Occupied" and current_checkin and current_checkout:
                if overlap_period(new_start, new_end, current_checkin, current_checkout):
                    conflict = True
                    conflict_msgs.append(f"Conflicts with current occupant from {current_checkin} to {current_checkout}.")

            # 2) Check against existing reservations for the same room
            # Convert reservation dates to date and iterate
            for _, r in res_df[res_df["Room Number"] == int(room_number)].iterrows():
                r_start = parse_date(r["Check-in Date"])
                r_end = parse_date(r["Check-out Date"])
                if overlap_period(new_start, new_end, r_start, r_end):
                    conflict = True
                    conflict_msgs.append(f"Conflicts with existing reservation (ID {r['Reservation ID']}) from {r_start} to {r_end}.")

            if conflict:
                st.error("⚠️ Booking conflict detected. " + " ".join(conflict_msgs))
            else:
                today = datetime.today().date()
                # If checkin is today or earlier -> occupy now
                if new_start <= today:
                    # assign as current occupant (do NOT touch reservations)
                    status = "Occupied"
                    rooms_df.loc[idx, :] = [
                        room_number,
                        status,
                        guest_name,
                        guest_id,
                        address,
                        job,
                        nationality,
                        nights,
                        new_start.strftime("%Y-%m-%d"),
                        new_end.strftime("%Y-%m-%d"),
                        paid,
                        total_price,
                        remaining
                    ]
                    save_rooms(rooms_df)
                    st.session_state.rooms = rooms_df
                    st.success(f"✅ Guest '{guest_name}' checked in to room {room_number}.")
                else:
                    # Save as future reservation (append to reservations table)
                    res_df = st.session_state.reservations
                    new_id = 1
                    if not res_df.empty:
                        # ensure integer Reservation ID
                        existing_ids = pd.to_numeric(res_df["Reservation ID"], errors='coerce').dropna().astype(int)
                        if not existing_ids.empty:
                            new_id = int(existing_ids.max()) + 1
                    new_res = {
                        "Reservation ID": new_id,
                        "Room Number": int(room_number),
                        "Guest Name": guest_name,
                        "ID/Passport": guest_id,
                        "Address": address,
                        "Job": job,
                        "Nationality": nationality,
                        "Nights": int(nights),
                        "Check-in Date": new_start.strftime("%Y-%m-%d"),
                        "Check-out Date": new_end.strftime("%Y-%m-%d"),
                        "Paid": float(paid),
                        "Total Cost": float(total_price),
                        "Remaining": float(remaining)
                    }
                    st.session_state.reservations = pd.concat([res_df, pd.DataFrame([new_res])], ignore_index=True)
                    save_reservations(st.session_state.reservations)
                    st.success(f"📅 Reservation saved for room {room_number} from {new_start} to {new_end} (ID {new_id}).")

# Check-Out
elif menu == "Check-Out":
    st.title("🚪 Check-Out")

    rooms_df = st.session_state.rooms
    occ_rooms = rooms_df[rooms_df["Status"] == "Occupied"]["Room Number"].tolist()

    if not occ_rooms:
        st.info("No currently occupied rooms.")
    else:
        room_number = st.selectbox("Select occupied room to check out", occ_rooms)
        idx = rooms_df.index[rooms_df["Room Number"] == room_number][0]
        guest_row = rooms_df.loc[idx]

        st.write("**Guest**:", guest_row["Guest Name"])
        st.write("**Check-in**:", guest_row["Check-in Date"])
        st.write("**Check-out**:", guest_row["Check-out Date"])
        st.write("**Total**:", guest_row["Total Cost"])
        st.write("**Paid**:", guest_row["Paid"])
        st.write("**Remaining**:", guest_row["Remaining"])

        add_payment = st.number_input("Add payment (EGP)", min_value=0.0, step=1.0, value=0.0)

        if st.button("Confirm Check-Out"):
            new_paid = float(guest_row["Paid"]) + float(add_payment)
            new_remaining = float(guest_row["Total Cost"]) - new_paid
            if new_remaining > 0:
                st.warning(f"Guest still owes {new_remaining:.2f} EGP. Add full payment to clear and proceed.")
            else:
                # Clear current occupant
                rooms_df.loc[idx, :] = [
                    room_number, "Available", "", "", "", "", "", 0, "", "", 0.0, 0.0, 0.0
                ]
                save_rooms(rooms_df)
                st.session_state.rooms = rooms_df
                st.success(f"Room {room_number} checked out and set to Available.")

                # Promote next reservation (if any) whose check-in is <= today (or earliest)
                next_res = next_reservation_for_room(room_number)
                if next_res is not None:
                    res_id = next_res["Reservation ID"]
                    res_checkin = parse_date(next_res["Check-in Date"])
                    today = datetime.today().date()
                    if res_checkin <= today:
                        # move reservation to occupied
                        st.info(f"Promoting reservation ID {res_id} to current occupant (check-in {res_checkin}).")
                        rooms_df = st.session_state.rooms
                        idx2 = rooms_df.index[rooms_df["Room Number"] == room_number][0]
                        rooms_df.loc[idx2, :] = [
                            room_number,
                            "Occupied",
                            next_res["Guest Name"],
                            next_res["ID/Passport"],
                            next_res["Address"],
                            next_res["Job"],
                            next_res["Nationality"],
                            int(next_res["Nights"]),
                            next_res["Check-in Date"],
                            next_res["Check-out Date"],
                            float(next_res["Paid"]),
                            float(next_res["Total Cost"]),
                            float(next_res["Remaining"])
                        ]
                        save_rooms(rooms_df)
                        st.session_state.rooms = rooms_df
                        # remove reservation
                        remove_reservation_by_id(res_id)
                        st.success(f"Reservation {res_id} promoted to Occupied for room {room_number}.")

# Analytics
elif menu == "Analytics":
    st.title("📊 Room Analytics")
    rooms_df = st.session_state.rooms.copy()
    res_df = st.session_state.reservations.copy()

    # normalize dates
    rooms_df["Check-in Date"] = pd.to_datetime(rooms_df["Check-in Date"], errors='coerce')
    rooms_df["Check-out Date"] = pd.to_datetime(rooms_df["Check-out Date"], errors='coerce')
    res_df["Check-in Date"] = pd.to_datetime(res_df["Check-in Date"], errors='coerce')
    res_df["Check-out Date"] = pd.to_datetime(res_df["Check-out Date"], errors='coerce')

    today = pd.Timestamp(datetime.today().date())

    available_now = rooms_df[
        (rooms_df["Status"] == "Available") |
        (rooms_df["Check-out Date"] < today)
    ]

    occupied_now = rooms_df[
        (rooms_df["Status"] == "Occupied") &
        (rooms_df["Check-in Date"] <= today) &
        (rooms_df["Check-out Date"] >= today)
    ]

    future_reservations = res_df[res_df["Check-in Date"] > today]

    c1, c2, c3 = st.columns(3)
    c1.metric("Available Now", len(available_now))
    c2.metric("Occupied Now", len(occupied_now))
    c3.metric("Future Reservations", len(future_reservations))

    st.subheader("Available Rooms (Now)")
    st.dataframe(available_now[["Room Number", "Status", "Check-out Date"]])

    st.subheader("Currently Occupied Rooms")
    st.dataframe(occupied_now[["Room Number", "Guest Name", "Check-in Date", "Check-out Date", "Remaining"]])

    st.subheader("Future Reservations")
    st.dataframe(future_reservations[["Reservation ID", "Room Number", "Guest Name", "Check-in Date", "Check-out Date", "Remaining"]])

    st.divider()
    st.write("### Summary Chart")
    chart_df = pd.DataFrame({
        "State": ["Available", "Occupied", "Future Reservations"],
        "Count": [len(available_now), len(occupied_now), len(future_reservations)]
    }).set_index("State")
    st.bar_chart(chart_df)

# Reservations management (list + delete)
elif menu == "Reservations":
    st.title("📅 Manage Reservations")
    res_df = st.session_state.reservations.copy()
    if res_df.empty:
        st.info("No future reservations.")
    else:
        res_df["Check-in Date"] = pd.to_datetime(res_df["Check-in Date"], errors='coerce')
        res_df["Check-out Date"] = pd.to_datetime(res_df["Check-out Date"], errors='coerce')
        st.dataframe(res_df.sort_values("Check-in Date").reset_index(drop=True))

        st.markdown("#### Delete a reservation")
        delete_id = st.number_input("Reservation ID to delete", min_value=1, step=1, value=0)
        if st.button("Delete Reservation"):
            if delete_id <= 0:
                st.error("Enter a valid Reservation ID.")
            else:
                if delete_id in list(st.session_state.reservations["Reservation ID"].astype(int)):
                    remove_reservation_by_id(delete_id)
                    st.success(f"Reservation {delete_id} deleted.")
                else:
                    st.error("Reservation ID not found.")
