# NO SCUTTLE SHUTTLE - FINAL STABLE VERSION

import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import time
import pyrebase

# 🔑 FIREBASE CONFIG
config = {
    "apiKey": "AIzaSyCJDXDpji9mwxef8__PqEYLo3DnSds9wuk",
    "authDomain": "no-scuttle-shuttle.firebaseapp.com",
    "databaseURL": "https://no-scuttle-shuttle-default-rtdb.firebaseio.com",
    "projectId": "no-scuttle-shuttle",
    "storageBucket": "no-scuttle-shuttle.firebasestorage.app",
    "messagingSenderId": "1072916906361",
    "appId": "1:1072916906361:web:8ae088fa2b48b53a45afa8"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

# 🎨 PAGE CONFIG
st.set_page_config(page_title="No Scuttle Shuttle", layout="wide")
st.title("🚌 NO SCUTTLE SHUTTLE")
st.caption("🚀 Stop the Scuttle. Know the Shuttle.")

# 📍 STOPS DATA
STOPS = {
    "Brunei Bus Stop": (6.6704, -1.5741),
    "Prempeh II Library": (6.6752, -1.5730),
    "Pharmacy Bus Stop": (6.6745, -1.5675),
    "KSB Bus Stop": (6.6694, -1.5672),
    "Casely Hayford Bus Stop": (6.6752, -1.5678),
    "Hall 7 A": (6.6792, -1.5728),
    "Hall 7 B": (6.6796, -1.5729),
    "Commercial Area": (6.6827, -1.5769),
    "GAZA": (6.6878, -1.5569),
    "Medical Village": (6.6819, -1.5496),
    "Agric": (6.6747, -1.5665),
}

ROUTE = list(STOPS.keys())

# 🧠 SESSION STATE
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "selected_stop" not in st.session_state:
    st.session_state.selected_stop = ROUTE[0]
if "votes" not in st.session_state:
    st.session_state.votes = {"green": 0, "yellow": 0, "red": 0}
if "user_votes" not in st.session_state:
    st.session_state.user_votes = 0

# Load votes from Firebase
try:
    data = db.child("votes").get().val()
    if data:
        st.session_state.votes = data
except:
    st.warning("⚠ Firebase not connected")

# ⚙ FUNCTIONS
def calculate_eta(start, end):
    distance = geodesic(start, end).km
    speed = 25  # km/h
    return round((distance / speed) * 60, 2)  # minutes

def get_status(v):
    if v["red"] > v["green"] and v["red"] > v["yellow"]:
        return "🔴 Full"
    elif v["yellow"] > v["green"]:
        return "🟡 Tight"
    else:
        return "🟢 Free Seats"

# 🚐 CURRENT SHUTTLE POSITION
current_stop = ROUTE[st.session_state.current_index]
current_coord = STOPS[current_stop]

# 📐 LAYOUT
left, right = st.columns([2, 1])

# 🗺 MAP (NO BLINK)
with left:
    m = folium.Map(location=[6.6735, -1.5670], zoom_start=15)

    for stop, coord in STOPS.items():
        color = "green" if stop == st.session_state.selected_stop else "blue"
        folium.Marker(
            coord,
            popup=stop,
            icon=folium.Icon(color=color)
        ).add_to(m)

    # 🚌 Shuttle Bus Icon
    folium.Marker(
        current_coord,
        popup="🚌 Shuttle",
        icon=folium.DivIcon(html="<div style='font-size:26px;'>🚌</div>")
    ).add_to(m)

    st.subheader(f"📍 Shuttle currently at: {current_stop}")
    st_folium(m, width=700, height=500)

# 📊 RIGHT PANEL
with right:
    # USER LOCATION
    st.subheader("📍 Where are you?")
    selected = st.selectbox("Select your stop", ROUTE)
    st.session_state.selected_stop = selected

    # ETA
    eta = calculate_eta(current_coord, STOPS[selected])
    st.info(f"⏱ Shuttle arrives in: {eta} mins")
    if eta < 2:
        st.success("🚌 Shuttle is approaching!")

    # 🚐 MANUAL MOVEMENT
    st.subheader("🛰 Live Movement")
    if st.button("➡ Move Shuttle"):
        st.session_state.current_index = (st.session_state.current_index + 1) % len(ROUTE)
    st.caption("Tap to simulate shuttle movement")

    # 📊 VOTING (LIMITED)
    st.subheader("📊 Crowd Level")
    st.write(f"Votes used: {st.session_state.user_votes}/3")
    if st.session_state.user_votes < 3:
        if st.button("🟢 Free"):
            st.session_state.votes["green"] += 1
            st.session_state.user_votes += 1
            db.child("votes").set(st.session_state.votes)
        if st.button("🟡 Tight"):
            st.session_state.votes["yellow"] += 1
            st.session_state.user_votes += 1
            db.child("votes").set(st.session_state.votes)
        if st.button("🔴 Full"):
            st.session_state.votes["red"] += 1
            st.session_state.user_votes += 1
            db.child("votes").set(st.session_state.votes)
    else:
        st.warning("Max votes reached!")

    st.success(get_status(st.session_state.votes))

    # ⚠ REPORT ISSUE
    st.subheader("⚠ Report Issue")
    issue = st.text_input("e.g. flat tyre, traffic jam")
    if st.button("Submit Report"):
        db.child("reports").push({
            "stop": selected,
            "issue": issue,
            "time": time.time()
        })
        st.success("Report submitted!")

    # 📢 SHOW REPORTS
    st.subheader("📢 Recent Reports")
    try:
        reports = db.child("reports").get().val()
        if reports:
            for r in list(reports.values())[-5:]:
                st.warning(f"{r['stop']}: {r['issue']}")
    except:
        st.write("No reports yet")