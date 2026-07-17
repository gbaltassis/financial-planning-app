import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# Συνάρτηση για μορφοποίηση στο Ελληνικό πρότυπο
def format_gr(number):
    s = f"{number:,.2f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')

st.set_page_config(page_title="Financial Planning App", page_icon="📈", layout="wide")

st.markdown("""
    <style>
[data-testid="stSidebar"] img {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 15px;
    border-radius: 10px;
}
    .main {background-color: #f9f9fb;}
    h1 {color: #1E3A8A;}
    .stButton>button {background-color: #1E3A8A; color: white;}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: ΕΙΣΑΓΩΓΗ ΔΕΔΟΜΕΝΩΝ ---

# Φόρτωση Λογοτύπου (αν υπάρχει στο GitHub)
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)

st.sidebar.header("ΠΑΡΑΜΕΤΡΟΙ ΠΕΛΑΤΗ")

st.sidebar.subheader("1. Οικονομικό Περιβάλλον & Κεφάλαιο")
PV = st.sidebar.number_input("Αρχικό Κεφάλαιο Επένδυσης (€)", min_value=0.0, value=10000.0, step=1000.0)
n = st.sidebar.number_input("Έτη Συσσώρευσης (μέχρι την ανάγκη)", min_value=1, value=35, step=1)
r_acc = st.sidebar.number_input("Απόδοση κατά τη Φάση Συσσώρευσης (%)", min_value=0.0, value=5.0, step=0.1) / 100
r_ret = st.sidebar.number_input("Απόδοση κατά τη Φάση Συνταξιοδότησης (%)", min_value=0.0, value=0.0, step=0.1) / 100
i = st.sidebar.number_input("Εκτιμώμενος Πληθωρισμός (%)", min_value=0.0, value=3.0, step=0.1) / 100

st.sidebar.subheader("2. Μελλοντικός Στόχος")
target_type = st.sidebar.radio("Πώς θα χρειαστεί το κεφάλαιο;", ("Εφάπαξ", "Μηνιαίες Δόσεις", "Μικτό (Εφάπαξ & Δόσεις)"))

if target_type == "Εφάπαξ":
    target_today = st.sidebar.number_input("Επιθυμητό Εφάπαξ (σε ΣΗΜΕΡΙΝΗ αξία €)", min_value=0.0, value=50000.0, step=5000.0)
    m = 0
elif target_type == "Μηνιαίες Δόσεις":
    monthly_income = st.sidebar.number_input("Επιθυμητό Μηνιαίο Εισόδημα (σε ΣΗΜΕΡΙΝΗ αξία €)", min_value=0.0, value=1500.0, step=100.0)
    m = st.sidebar.number_input("Για πόσα έτη θα λαμβάνει εισόδημα;", min_value=1, value=20, step=1)
else:
    initial_lump_sum = st.sidebar.number_input("Αρχικό Εφάπαξ στη Λήξη (σε ΣΗΜΕΡΙΝΗ αξία €)", min_value=0.0, value=15000.0, step=1000.0)
    annual_lump_sum = st.sidebar.number_input("Ετήσιο Εφάπαξ / π.χ. κάθε Σεπτέμβρη (σε ΣΗΜΕΡΙΝΗ αξία €)", min_value=0.0, value=0.0, step=1000.0)
    monthly_income = st.sidebar.number_input("Επιπλέον Μηνιαίο Εισόδημα (σε ΣΗΜΕΡΙΝΗ αξία €)", min_value=0.0, value=500.0, step=100.0)
    m = st.sidebar.number_input("Για πόσα έτη θα λαμβάνει τις δόσεις;", min_value=1, value=4, step=1)

st.sidebar.subheader("3. Ευελιξία & Τακτικές Καταβολές")
g = st.sidebar.number_input("Ετήσια Αύξηση Δόσης / Step-up (%)", min_value=0.0, value=0.0, step=0.5) / 100

st.sidebar.subheader("4. Έκτακτες Καταβολές (Προαιρετικό)")
st.sidebar.write("Εισαγωγή έκτακτων εισροών ανά έτος.")
df_extra_init = pd.DataFrame({
    "Έτος": list(range(1, int(n) + 1)),
    "Έκτακτη (€)": [0.0] * int(n)
})

edited_df = st.sidebar.data_editor(
    df_extra_init,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Έτος": st.column_config.NumberColumn("Έτος", disabled=True),
        "Έκτακτη (€)": st.column_config.NumberColumn("Έκτακτη (€)", min_value=0.0, format="€ %d")
    }
)

# --- ΑΝΑΛΟΓΙΣΤΙΚΗ ΜΗΧΑΝΗ (ΥΠΟΛΟΓΙΣΜΟΙ) ---
# Φάση Α: Στόχος
if target_type == "Εφάπαξ":
    target_fv = target_today * ((1 + i) ** n)
elif target_type == "Μηνιαίες Δόσεις":
    annual_need_today = monthly_income * 12
    C1 = annual_need_today * ((1 + i) ** n)
    if r_ret == i:
        target_fv = C1 * m
    else:
        target_fv = C1 * (1 - ((1 + i) / (1 + r_ret)) ** m) / (r_ret - i)
else:
    fv_initial_lump = initial_lump_sum * ((1 + i) ** n)
    annual_need_today = annual_lump_sum + (monthly_income * 12)
    C1 = annual_need_today * ((1 + i) ** n)
    if r_ret == i:
        fv_annuity = C1 * m
    else:
        fv_annuity = C1 * (1 - ((1 + i) / (1 + r_ret)) ** m) / (r_ret - i)
    target_fv = fv_initial_lump + fv_annuity

# Φάση Β: Συσσώρευση 
fv_pv = PV * ((1 + r_acc) ** n)

fv_extra = 0.0
for index, row in edited_df.iterrows():
    year = row["Έτος"]
    extra_amount = row["Έκτακτη (€)"]
    if extra_amount > 0:
        fv_extra += extra_amount * ((1 + r_acc) ** (n - year))

shortfall = target_fv - fv_pv - fv_extra

# Διόρθωση: Προκαταβλητέα Ράντα (πολλαπλασιασμός με 1+r_acc)
if shortfall <= 0:
    pmt = 0.0
else:
    if r_acc == g:
        pmt = shortfall / (n * ((1 + r_acc)**n))
    else:
        pmt = shortfall / ((((1 + r_acc)**n - (1 + g)**n) / (r_acc - g)) * (1 + r_acc))

# Πίνακας Εξέλιξης
years = list(range(1, int(n) + 1))
balance = [PV]
regular_contributions = []
extra_contributions = edited_df["Έκτακτη (€)"].tolist()

current_pmt = pmt
for year_idx in range(int(n)):
    reg_contrib = current_pmt if current_pmt > 0 else 0
    regular_contributions.append(reg_contrib)
    ext_contrib = extra_contributions[year_idx]
    
    # Η τακτική καταβολή μπαίνει στην αρχή του έτους, η έκτακτη στο τέλος
    new_balance = (balance[-1] + reg_contrib) * (1 + r_acc) + ext_contrib
    balance.append(new_balance)
    
    current_pmt = current_pmt * (1 + g)

balance = balance[1:] 

# --- MAIN PAGE: ΕΜΦΑΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ---
st.title("📈 Στρατηγικός Οικονομικός Σχεδιασμός")
st.markdown("Υπολογισμός Αποταμιευτικού και Επενδυτικού Πλάνου")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.info("🎯 Στόχος στη Λήξη (Αναπροσαρμοσμένος)")
        st.subheader(f"€ {format_gr(target_fv)}")

with col2:
    with st.container(border=True):
        st.warning("📥 1η Τακτική Ετήσια Καταβολή")
        if shortfall <= 0:
            st.subheader("€ 0,00")
            st.caption("Οι πόροι καλύπτουν τον στόχο!")
        else:
            st.subheader(f"€ {format_gr(pmt)}")
            st.caption(f"(ή περίπου € {format_gr(pmt/12)} / μήνα)")

with col3:
    with st.container(border=True):
        st.success("💰 Συνολικό Κεφάλαιο στη Λήξη")
        st.subheader(f"€ {format_gr(balance[-1])}")

st.markdown("### 📊 Εξέλιξη Επένδυσης")
fig = go.Figure()

fig.add_trace(go.Bar(
    x=years,
    y=regular_contributions,
    name='Τακτική Ετήσια Καταβολή',
    marker_color='#FF9F1C'
))

fig.add_trace(go.Bar(
    x=years,
    y=extra_contributions,
    name='Έκτακτη Καταβολή',
    marker_color='#2A9D8F'
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
    barmode='stack',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, t=30, b=0)
)
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

st.plotly_chart(fig, use_container_width=True)
