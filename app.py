import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Financial Planning App", page_icon="📈", layout="wide")

# CSS για Branding (Μπορείς να αλλάξεις χρώματα)
st.markdown("""
    <style>
    .main {background-color: #f9f9fb;}
    h1 {color: #1E3A8A;}
    .stButton>button {background-color: #1E3A8A; color: white;}
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Στρατηγικός Οικονομικός Σχεδιασμός")
st.markdown("Υπολογισμός Αποταμιευτικού και Επενδυτικού Πλάνου")

# --- SIDEBAR: ΕΙΣΑΓΩΓΗ ΔΕΔΟΜΕΝΩΝ ---
st.sidebar.header("Παράμετροι Πελάτη")

# 1. Βασικές Παράμετροι
st.sidebar.subheader("1. Οικονομικό Περιβάλλον & Κεφάλαιο")
PV = st.sidebar.number_input("Αρχικό Κεφάλαιο Επένδυσης (€)", min_value=0.0, value=10000.0, step=1000.0)
n = st.sidebar.number_input("Έτη Συσσώρευσης (μέχρι την ανάγκη)", min_value=1, value=15, step=1)
r = st.sidebar.slider("Εκτιμώμενη Ετήσια Απόδοση (%)", 0.0, 15.0, 5.0) / 100
i = st.sidebar.slider("Εκτιμώμενος Πληθωρισμός (%)", 0.0, 10.0, 2.0) / 100

# 2. Στόχος / Ανάγκη
st.sidebar.subheader("2. Μελλοντικός Στόχος")
target_type = st.sidebar.radio("Πώς θα χρειαστεί το κεφάλαιο;", ("Εφάπαξ", "Μηνιαίες Δόσεις (Εισόδημα)"))
if target_type == "Εφάπαξ":
    target_today = st.sidebar.number_input("Επιθυμητό Εφάπαξ (σε ΣΗΜΕΡΙΝΗ αξία €)", min_value=0.0, value=50000.0, step=5000.0)
    m = 0
else:
    monthly_income = st.sidebar.number_input("Επιθυμητό Μηνιαίο Εισόδημα (σε ΣΗΜΕΡΙΝΗ αξία €)", min_value=0.0, value=1000.0, step=100.0)
    target_today = monthly_income * 12
    m = st.sidebar.number_input("Για πόσα έτη θα λαμβάνει εισόδημα;", min_value=1, value=20, step=1)

# 3. Σχέδιο Καταβολών
st.sidebar.subheader("3. Ευελιξία & Καταβολές")
g = st.sidebar.slider("Ετήσια Αύξηση Δόσης / Step-up (%)", 0.0, 10.0, 0.0) / 100

st.sidebar.markdown("---")
st.sidebar.write("💡 *Συμπληρώστε τα πεδία για να δείτε τα αποτελέσματα δεξιά.*")

# --- ΑΝΑΛΟΓΙΣΤΙΚΗ ΜΗΧΑΝΗ (ΥΠΟΛΟΓΙΣΜΟΙ) ---
# Πραγματικό επιτόκιο
r_real = ((1 + r) / (1 + i)) - 1

# ΦΑΣΗ Α: Υπολογισμός Στόχου (FV) στο τέλος του έτους n
if target_type == "Εφάπαξ":
    target_fv = target_today * ((1 + i) ** n)
else:
    # Παρούσα αξία ράντας στην αρχή της περιόδου συνταξιοδότησης (έτος n), με το πραγματικό επιτόκιο
    if r_real == 0:
        target_fv_real = target_today * m
    else:
        target_fv_real = target_today * ((1 - (1 + r_real)**(-m)) / r_real)
    # Προσαρμογή στον πληθωρισμό της περιόδου συσσώρευσης
    target_fv = target_fv_real * ((1 + i) ** n)

# ΦΑΣΗ Β: Πορεία Αρχικού Κεφαλαίου
fv_pv = PV * ((1 + r) ** n)

# ΦΑΣΗ Γ: Επίλυση για την πρώτη ετήσια δόση (PMT)
shortfall = target_fv - fv_pv

if shortfall <= 0:
    pmt = 0.0
    st.success("Το αρχικό σας κεφάλαιο επαρκεί για να καλύψει τον στόχο! Δεν απαιτούνται περαιτέρω τακτικές καταβολές.")
else:
    if r == g:
        pmt = shortfall / (n * ((1 + r)**(n-1)))
    else:
        pmt = shortfall / ((( (1 + r)**n ) - ( (1 + g)**n )) / (r - g))

# Δημιουργία Πίνακα Χρεολυσίας / Εξέλιξης Κεφαλαίου
years = list(range(1, int(n) + 1))
balance = [PV]
contributions = []

current_pmt = pmt
for year in years:
    if current_pmt > 0:
        contributions.append(current_pmt)
    else:
        contributions.append(0)
    
    # Εξέλιξη: Προηγούμενο υπόλοιπο + απόδοση + νέα καταβολή
    new_balance = balance[-1] * (1 + r) + current_pmt * (1 + r) # Υποθέτουμε καταβολή στην αρχή του έτους
    balance.append(new_balance)
    
    current_pmt = current_pmt * (1 + g)

balance = balance[1:] # Αφαιρούμε το έτος 0 για το γράφημα

# --- ΕΜΦΑΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ---
col1, col2, col3 = st.columns(3)

with col1:
    st.info("🎯 Στόχος στη Λήξη (Αναπροσαρμοσμένος)")
    st.title(f"€ {target_fv:,.0f}")

with col2:
    st.warning("📥 1η Ετήσια Καταβολή")
    if pmt > 0:
        st.title(f"€ {pmt:,.0f}")
        st.write(f"(ή περίπου € {pmt/12:,.0f} / μήνα)")
    else:
        st.title("€ 0")

with col3:
    st.success("💰 Συνολικό Κεφάλαιο στη Λήξη")
    st.title(f"€ {balance[-1]:,.0f}")


# Γράφημα
st.markdown("### 📊 Εξέλιξη Επένδυσης")
fig = go.Figure()

fig.add_trace(go.Bar(
    x=years,
    y=contributions,
    name='Ετήσια Καταβολή',
    marker_color='#FF9F1C'
))

fig.add_trace(go.Scatter(
    x=years,
    y=balance,
    name='Συσσωρευμένο Κεφάλαιο',
    mode='lines+markers',
    marker_color='#1E3A8A',
    line=dict(width=3)
))

fig.update_layout(
    xaxis_title="Έτη Επένδυσης",
    yaxis_title="Ποσό (€)",
    hovermode="x unified",
    barmode='overlay',
    plot_bgcolor='rgba(0,0,0,0)'
)
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Developed for professional financial planning. All calculations are projections based on the provided inputs.")
