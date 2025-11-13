import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="🏨 Hotel Management System", layout="wide")

ROOMS_FILE = "rooms.csv"
RESERVATIONS_FILE = "reservations.csv"

# ===================== LOAD & SAVE =====================
def load_rooms():
    if os.path.exists(ROOMS_FILE):
        return pd.read_csv(ROOMS_FILE)
    else:
        rooms = [{"Room Number": i, "Status": "Available"} for i in range(1, 31)]
        df = pd.DataFrame(rooms)
        df.to_csv(ROOMS_FILE, index=False)
        return df

def load_reservations():
    if os.path.exists(RESERVATIONS_FILE):
        return pd.read_csv(RESERVATIONS_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Reservation ID", "Room Number", "Guest Name", "ID/Passport",
            "Address", "Job", "Nationality", "Nights",
            "Check-in Date", "Check-out Date", "Total Cost",
            "Paid", "Remaining", "Status"
        ])
        df.to_csv(RESERVATIONS_FILE, index=False)
        return df

def save_rooms(df):
    df.to_csv(ROOMS_FILE, index=False)

def save_reservations(df):
    df.to_csv(RESERVATIONS_FILE, index=False)

# ===================== INIT =====================
if "rooms" not in st.session_state:
    st.session_state.rooms = load_rooms()

if "reservations" not in st.session_state:
    st.session_state.reservations = load_reservations()

rooms_df = st.session_state.rooms
reservations_df = st.session_state.reservations

# ===================== MENU =====================
st.sidebar.title("🏨 Hotel Menu")
menu = st.sidebar.radio("Select Action", ["Dashboard", "Register Guest", "Check-Out", "Reservations", "Analytics"])

today = datetime.today().date()

# ===================== DASHBOARD =====================
if menu == "Dashboard":
    st.title("🏨 Hotel Dashboard")

    current_res = reservations_df.copy()
    current_res["Check-in Date"] = pd.to_datetime(current_res["Check-in Date"], errors='coerce')
    current_res["Check-out Date"] = pd.to_datetime(current_res["Check-out Date"], errors='coerce')

    occupied = current_res[
        (current_res["Check-in Date"] <= pd.Timestamp(today)) &
        (current_res["Check-out Date"] >= pd.Timestamp(today))
    ]
    future = current_res[current_res["Check-in Date"] > pd.Timestamp(today)]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rooms", len(rooms_df))
    col2.metric("Currently Occupied", len(occupied))
    col3.metric("Future Bookings", len(future))

    st.subheader("🟩 Rooms Overview")
    st.dataframe(rooms_df)

# ===================== REGISTER GUEST =====================
elif menu == "Register Guest":
    st.title("🧾 Register a New Guest")

    room_number = st.selectbox("Select Room Number", rooms_df["Room Number"].tolist())
    guest_name = st.text_input("Guest Name")
    guest_id = st.text_input("ID or Passport Number")
    address = st.text_input("Address")
    job = st.text_input("Job")
    nationality = st.text_input("Nationality")
    nights = st.number_input("Number of Nights", min_value=1, max_value=60, step=1)
    checkin_date = st.date_input("Check-in Date", today)
    checkout_date = checkin_date + timedelta(days=int(nights))
    st.info(f"Check-out Date: **{checkout_date.strftime('%Y-%m-%d')}**")

    total_cost = st.number_input("Total Cost (EGP)", min_value=0.0, step=100.0)
    paid = st.number_input("Paid (EGP)", min_value=0.0, step=100.0)
    remaining = total_cost - paid

    if st.button("Register Guest"):
        # Prevent overlapping reservations
        overlap = False
        for _, res in reservations_df[reservations_df["Room Number"] == room_number].iterrows():
            try:
                res_in = datetime.strptime(res["Check-in Date"], "%Y-%m-%d").date()
                res_out = datetime.strptime(res["Check-out Date"], "%Y-%m-%d").date()
                if (checkin_date < res_out) and (checkout_date > res_in):
                    overlap = True
                    break
            except:
                pass

        if overlap:
            st.error("⚠️ This room is already booked or occupied during that period!")
        else:
            new_id = int(reservations_df["Reservation ID"].max() + 1) if not reservations_df.empty else 1
            status = "Occupied" if checkin_date <= today <= checkout_date else "Booked"
            new_row = pd.DataFrame([{
                "Reservation ID": new_id,
                "Room Number": room_number,
                "Guest Name": guest_name,
                "ID/Passport": guest_id,
                "Address": address,
                "Job": job,
                "Nationality": nationality,
                "Nights": nights,
                "Check-in Date": checkin_date.strftime("%Y-%m-%d"),
                "Check-out Date": checkout_date.strftime("%Y-%m-%d"),
                "Total Cost": total_cost,
                "Paid": paid,
                "Remaining": remaining,
                "Status": status
            }])

            reservations_df = pd.concat([reservations_df, new_row], ignore_index=True)
            st.session_state.reservations = reservations_df
            save_reservations(reservations_df)

            st.success(f"✅ Registered guest {guest_name} for Room {room_number}")
            st.metric("Remaining", f"{remaining:.2f} EGP")

# ===================== CHECK-OUT =====================
elif menu == "Check-Out":
    st.title("🚪 Guest Check-Out")

    active_guests = reservations_df[
        (pd.to_datetime(reservations_df["Check-in Date"], errors='coerce') <= pd.Timestamp(today)) &
        (pd.to_datetime(reservations_df["Check-out Date"], errors='coerce') >= pd.Timestamp(today))
    ]

    if active_guests.empty:
        st.info("No guests currently checked in.")
    else:
        room_number = st.selectbox("Select Room", active_guests["Room Number"].unique())
        guest = active_guests[active_guests["Room Number"] == room_number].iloc[0]

        st.write(f"**Guest Name:** {guest['Guest Name']}")
        st.write(f"**Check-in:** {guest['Check-in Date']}")
        st.write(f"**Check-out:** {guest['Check-out Date']}")
        st.write(f"**Total Cost:** {guest['Total Cost']} EGP")
        st.write(f"**Paid:** {guest['Paid']} EGP")
        st.write(f"**Remaining:** {guest['Remaining']} EGP")

        add_payment = st.number_input("Add Payment (EGP)", min_value=0.0, step=100.0)

        if st.button("Confirm Check-Out"):
            idx = reservations_df.index[
                (reservations_df["Room Number"] == room_number) &
                (reservations_df["Check-in Date"] == guest["Check-in Date"])
            ][0]
            new_paid = guest["Paid"] + add_payment
            new_remaining = guest["Total Cost"] - new_paid

            if new_remaining > 0:
                st.warning(f"⚠️ Guest still owes {new_remaining:.2f} EGP.")
            else:
                reservations_df.at[idx, "Status"] = "Checked Out"
                save_reservations(reservations_df)
                st.session_state.reservations = reservations_df
                st.success(f"✅ Room {room_number} checked out successfully!")

# ===================== RESERVATIONS =====================
elif menu == "Reservations":
    st.title("📅 Manage Reservations")

    if reservations_df.empty:
        st.info("No reservations yet.")
    else:
        reservations_df["Check-in Date"] = pd.to_datetime(reservations_df["Check-in Date"], errors='coerce')
        reservations_df["Check-out Date"] = pd.to_datetime(reservations_df["Check-out Date"], errors='coerce')
        st.dataframe(reservations_df.sort_values("Check-in Date"))

        st.markdown("#### 🗑️ Delete a Reservation")
        valid_ids = reservations_df["Reservation ID"].astype(int).tolist()
        delete_id = st.selectbox("Select Reservation ID to delete", options=valid_ids)

        if st.button("Delete Reservation"):
            reservations_df = reservations_df[reservations_df["Reservation ID"] != delete_id].reset_index(drop=True)
            st.session_state.reservations = reservations_df
            save_reservations(reservations_df)
            st.success(f"Reservation {delete_id} deleted.")

# ===================== ANALYTICS =====================
elif menu == "Analytics":
    st.title("📊 Hotel Analytics")

    df = reservations_df.copy()
    if df.empty:
        st.info("No data to analyze yet.")
    else:
        df["Check-in Date"] = pd.to_datetime(df["Check-in Date"], errors='coerce')
        df["Check-out Date"] = pd.to_datetime(df["Check-out Date"], errors='coerce')

        current = df[
            (df["Check-in Date"] <= pd.Timestamp(today)) &
            (df["Check-out Date"] >= pd.Timestamp(today))
        ]
        future = df[df["Check-in Date"] > pd.Timestamp(today)]
        checked_out = df[df["Status"] == "Checked Out"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Currently Occupied", len(current))
        col2.metric("Future Bookings", len(future))
        col3.metric("Checked Out", len(checked_out))

        st.bar_chart(pd.DataFrame({
            "Category": ["Occupied", "Future", "Checked Out"],
            "Count": [len(current), len(future), len(checked_out)]
        }).set_index("Category"))

        st.subheader("💰 Revenue Analysis")
        total_revenue = df["Paid"].sum()
        pending = df["Remaining"].sum()
        st.metric("Total Collected", f"{total_revenue:.2f} EGP")
        st.metric("Pending Payments", f"{pending:.2f} EGP")
