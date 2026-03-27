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

# Initialize Firebase
try:
    firebase = pyrebase.initialize_app(config)
    db = firebase.database()
except Exception as e:
    st.error("Firebase Connection Error. Check your config.")

# 🎨 PAGE CONFIG - Optimized for Mobile
st.set_page_config(page_title="No Scuttle Shuttle", layout="centered") 
st.title("🚌 NO SCUTTLE SHUTTLE")
st.caption("🚀 Stop the Scuttle. Know the Shuttle.")

# 📍 STOPS DATA (Latitudes & Longitudes preserved exactly)
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
if "votes" not in st.session_state:
    st.session_state.votes = {"green": 0, "yellow": 0, "red": 0}
if "user_voted" not in st.session_state:
    st.session_state.user_voted = False

# Sync with Firebase
try:
    live_votes = db.child("votes").get().val()
    if live_votes:
        st.session_state.votes = live_votes
    
    # Get current bus index from Firebase (so everyone sees the same bus)
    live_index = db.child("bus_location").get().val()
    if live_index is not None:
        st.session_state.current_index = live_index
except:
    pass

# ⚙️ HELPER FUNCTIONS
def calculate_eta(start, end):
    distance = geodesic(start, end).km
    speed = 20  # Average KNUST shuttle speed km/h
    return round((distance / speed) * 60, 1)

def get_crowd_status(v):
    total = sum(v.values())
    if total == 0: return "⚪ No Data Yet"
    if v["red"] >= v["yellow"] and v["red"] >= v["green"]: return "🔴 Full - Don't Bother"
    if v["yellow"] > v["green"]: return "🟡 Tight - Standing Room"
    return "🟢 Plenty Seats"

# 🚐 BUS LOCATION LOGIC
current_stop = ROUTE[st.session_state.current_index]
current_coord = STOPS[current_stop]

# 🗺️ VISUAL SECTION (MAP)
m = folium.Map(location=[6.6735, -1.5670], zoom_start=15)
for stop, coord in STOPS.items():
    folium.Marker(coord, popup=stop, icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)

# Bus Icon
folium.Marker(
    current_coord, 
    popup="LIVE BUS", 
    icon=folium.DivIcon(html="<div style='font-size:30px;'>🚌</div>")
).add_to(m)

st_folium(m, width=700, height=400)
st.info(f"📍 *Bus is currently at:* {current_stop}")

st.divider()

# 📱 STUDENT INTERACTION PANEL
col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Update Bus Location")
    new_loc = st.selectbox("I see the bus at:", ROUTE, index=st.session_state.current_index)
    if st.button("Confirm Bus is Here"):
        new_index = ROUTE.index(new_loc)
        db.child("bus_location").set(new_index)
        st.session_state.current_index = new_index
        st.success("Location Updated!")
        time.sleep(1)
        st.rerun()

with col2:
    st.subheader("📊 Vibe Check (Crowd)")
    if not st.session_state.user_voted:
        v_col1, v_col2, v_col3 = st.columns(3)
        if v_col1.button("🟢"):
            st.session_state.votes["green"] += 1
            db.child("votes").set(st.session_state.votes)
            st.session_state.user_voted = True
            st.rerun()
        if v_col2.button("🟡"):
            st.session_state.votes["yellow"] += 1
            db.child("votes").set(st.session_state.votes)
            st.session_state.user_voted = True
            st.rerun()
        if v_col3.button("🔴"):
            st.session_state.votes["red"] += 1
            db.child("votes").set(st.session_state.votes)
            st.session_state.user_voted = True
            st.rerun()
    else:
        st.write("Thanks for voting!")
    
    st.metric("Current Status", get_crowd_status(st.session_state.votes))

st.divider()

# ⏱️ PERSONAL ETA SECTION
st.subheader("⏱️ Personal Arrival Estimate")
my_stop = st.selectbox("Where are you waiting?", ROUTE)
eta_val = calculate_eta(current_coord, STOPS[my_stop])

if my_stop == current_stop:
    st.balloons()
    st.success("The bus is right in front of you!")
else:
    st.write(f"Estimated Wait: *{eta_val} minutes*")

# 📢 REPORT SECTION
with st.expander("⚠ Report a Traffic/Bus Issue"):
    issue = st.text_input("Describe the issue...")
    if st.button("Submit Report"):
        db.child("reports").push({"issue": issue, "time": time.ctime(), "stop": current_stop})
        st.toast("Report sent to fellow students!")