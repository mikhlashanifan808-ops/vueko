import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import pandas as pd

# ================================
# Konfigurasi dasar
# ================================
st.set_page_config(page_title="MQTT Dashboard", layout="wide")

# Session-state untuk data
if "connected" not in st.session_state:
    st.session_state.connected = False

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["time", "temperature", "humidity"])

if "log" not in st.session_state:
    st.session_state.log = []

# ================================
# MQTT Callback
# ================================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.connected = True
        st.session_state.log.append(f"[{datetime.now()}] MQTT Connected")
        client.subscribe(st.session_state.sub_topic)
    else:
        st.session_state.log.append(f"[{datetime.now()}] MQTT Failed: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        temp = payload.get("temperature") or payload.get("temp") or payload.get("t")
        hum = payload.get("humidity") or payload.get("hum") or payload.get("h")

        if temp is not None and hum is not None:
            st.session_state.df.loc[len(st.session_state.df)] = [
                datetime.now().strftime("%H:%M:%S"),
                float(temp),
                float(hum),
            ]

        st.session_state.log.append(
            f"[{datetime.now()}] Topic: {msg.topic} | {msg.payload.decode()}"
        )

    except Exception as e:
        st.session_state.log.append(f"[ERROR] {e}")

# ================================
# Sidebar: Pengaturan MQTT
# ================================
st.sidebar.header("MQTT Connection")

mqtt_host = st.sidebar.text_input("Broker Host", "broker.hivemq.com")
mqtt_port = st.sidebar.number_input("Port (WebSocket)", 1883)
mqtt_user = st.sidebar.text_input("Username", "")
mqtt_pass = st.sidebar.text_input("Password", "", type="password")

sub_topic = st.sidebar.text_input("Subscribe Topic", "sensor/dht22")
pub_topic = st.sidebar.text_input("Publish Topic", "device/led")

st.session_state.sub_topic = sub_topic

if st.sidebar.button("Connect MQTT"):
    client = mqtt.Client()

    if mqtt_user != "":
        client.username_pw_set(mqtt_user, mqtt_pass)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(mqtt_host, int(mqtt_port), 60)
        client.loop_start()
        st.success("Connecting...")
    except Exception as e:
        st.error(f"Gagal connect: {e}")

# ================================
# Layout Dashboard
# ================================
st.title("📡 Realtime MQTT Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Grafik Suhu (°C)")
    if len(st.session_state.df) > 0:
        st.line_chart(st.session_state.df[["temperature"]])
    else:
        st.info("Belum ada data.")

with col2:
    st.subheader("Grafik Kelembapan (%)")
    if len(st.session_state.df) > 0:
        st.line_chart(st.session_state.df[["humidity"]])
    else:
        st.info("Belum ada data.")

# ================================
# Kontrol Publish
# ================================
st.subheader("Kontrol Perangkat")

colA, colB, colC, colD = st.columns(4)

def publish_led(color):
    try:
        client.publish(pub_topic, json.dumps({"led": color}))
        st.session_state.log.append(
            f"[{datetime.now()}] Publish LED: {color}"
        )
    except:
        st.error("Belum terhubung ke MQTT")

with colA:
    if st.button("LED Merah"):
        publish_led("merah")

with colB:
    if st.button("LED Hijau"):
        publish_led("hijau")

with colC:
    if st.button("LED Kuning"):
        publish_led("kuning")

with colD:
    if st.button("LED Off"):
        publish_led("off")

# ================================
# Log Pesan
# ================================
st.subheader("Log MQTT")
st.text("\n".join(st.session_state.log[-25:]))
