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

# Initialize Firebase (Global)
@st.cache_resource
def init_db():
    firebase = pyrebase.initialize_app(config)
    return firebase.database()

db = init_db()

# 🎨 PAGE CONFIG
st.set_page_config(page_title="No Scuttle Shuttle", layout="centered")
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
if "votes" not in st.session_state:
    st.session_state.votes = {"green": 0, "yellow": 0, "red": 0}
if "user_voted" not in st.session_state:
    st.session_state.user_voted = False

# 🔄 SYNC FIREBASE
try:
    live_votes = db.child("votes").get().val()
    if live_votes:
        st.session_state.votes = live_votes
    live_index = db.child("bus_location").get().val()
    if live_index is not None:
        st.session_state.current_index = live_index
except:
    pass

# 🚐 BUS LOCATION
current_stop = ROUTE[st.session_state.current_index]
current_coord = STOPS[current_stop]

# 🗺️ MAP
m = folium.Map(location=[6.6735, -1.5670], zoom_start=15)
for stop, coord in STOPS.items():
    folium.Marker(coord, popup=stop).add_to(m)
folium.Marker(current_coord, icon=folium.DivIcon(html="<div style='font-size:30px;'>🚌</div>")).add_to(m)

st_folium(m, width=700, height=400)
st.info(f"📍 Bus is currently at: {current_stop}")

st.divider()

# 📱 INTERACTION
col1, col2 = st.columns(2)
with col1:
    st.subheader("📍 Update Location")
    new_loc = st.selectbox("I see it at:", ROUTE, index=st.session_state.current_index)
    if st.button("Confirm Location"):
        new_idx = ROUTE.index(new_loc)
        db.child("bus_location").set(new_idx)
        st.session_state.current_index = new_idx
        st.rerun()

with col2:
    st.subheader("📊 Crowd Status")
    v = st.session_state.votes
    status = "🟢 Free"
    if sum(v.values()) > 0:
        if v["red"] >= v["yellow"] and v["red"] >= v["green"]: status = "🔴 Full"
        elif v["yellow"] > v["green"]: status = "🟡 Tight"
    
    st.metric("Current Status", status)
    
    if not st.session_state.user_voted:
        c1, c2, c3 = st.columns(3)
        if c1.button("🟢"):
            v["green"] += 1
            db.child("votes").set(v)
            st.session_state.user_voted = True
            st.rerun()
        if c2.button("🟡"):
            v["yellow"] += 1
            db.child("votes").set(v)
            st.session_state.user_voted = True
            st.rerun()
        if c3.button("🔴"):
            v["red"] += 1
            db.child("votes").set(v)
            st.session_state.user_voted = True
            st.rerun()

st.divider()

# ⏱️ ETA
my_stop = st.selectbox("Where are you?", ROUTE)
dist = geodesic(current_coord, STOPS[my_stop]).km
eta = round((dist / 20) * 60, 1)
st.write(f"Wait time: *{eta} mins*" if my_stop != current_stop else "Bus is here!")