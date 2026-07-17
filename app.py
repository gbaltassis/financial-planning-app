import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Συνάρτηση για μορφοποίηση στο Ελληνικό πρότυπο (π.χ. 1.500,53)
def format_gr(number):
    s = f"{number:,.2f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')

st.set_page_config(page_title="Financial Planning App", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #f9f9fb;}
    h1 {color: #1E3A8A;}
    .stButton>button {background-color: #1E3A8A; color: white;}
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Στρατηγικός Οικονομικός Σχεδιασμός")
st.markdown("Υπολογισμός Αποταμιευτικού και Επενδυτικού Πλάνου (v2.0)")

# --- SIDEBAR: ΕΙΣΑΓΩΓΗ ΔΕΔΟΜΕΝΩΝ ---
st.sidebar.header("Παράμετροι Πελάτη")

st.sidebar.subheader("1. Οικονομικό Περιβάλλον & Κεφάλαιο")
PV = st.sidebar.number_input("Αρχικό Κεφάλαιο Επένδυσης (€)", min_value=0.0, value=10000.0, step=1000.0)
n = st.sidebar.number_input("Έτη Συσσώρευσης (μέχρι την ανάγκη)", min_value=1, value=15, step=1)
r = st.sidebar.number_input("Εκτιμώμενη Ετήσια Απόδοση (%)", min_value=0.0, value=5.0, step=0.1) / 100
i = st.sidebar.number_input("Εκτιμώμενος Πληθωρισμός (%)", min_value=0.0, value=2.0, step=0.1) / 100

st.sidebar.subheader("2. Μελλοντικός Στόχος")
target_type = st.sidebar.radio("Πώς θα χρειαστεί το κεφάλαιο;", ("Εφάπαξ", "Μηνιαίες Δόσεις", "Μικτό (Εφάπαξ & Δόσεις)"))

if target_type == "Εφάπαξ":
    target_today = st.sidebar.number_input("Επιθυμητό Εφάπαξ (σε ΣΗΜΕΡΙΝΗ αξία €)", min_value=0.0, value=50000.0, step=5000.0)
    m = 0
elif target_type == "Μηνιαίες Δόσεις":
    monthly_income = st.sidebar.number_input("Επιθυμητό Μηνιαίο Εισόδημα (σε ΣΗΜΕΡΙΝΗ αξία €)", min_value=0.0, value=1000.0, step=100.0)
    m = st.sidebar.number_input("Για πόσα έτη θα λαμβάνει εισόδημα;", min_value=1, value=20, step=1)
else: # Μικτό
    initial_lump_sum = st.sidebar.number_input("Αρχικό Εφάπαξ στη Λήξη (€ Σήμερα)", min_value=0.0, value=15000.0, step=1000.0)
    annual_lump_sum = st.sidebar.number_input("Ετήσιο Εφάπαξ / π.χ. κάθε Σεπτέμβρη (€ Σήμερα)", min_value=0.0, value=0.0, step=1000.0)
    monthly_income = st.sidebar.number_input("Επιπλέον Μηνιαίο Εισόδημα (€ Σήμερα)", min_value=0.0, value=500.0, step=100.0)
    m = st.sidebar.number_input("Για πόσα έτη θα λαμβάνει τις δόσεις;", min_value=1, value=4, step=1)

st.sidebar.subheader("3. Ευελιξία & Τακτικές Καταβολές")
g = st.sidebar.number_input("Ετήσια Αύξηση Δόσης / Step-up (%)", min_value=0.0, value=0.0, step=0.5) / 100

# --- ΕΚΤΑΚΤΕΣ ΚΑΤΑΒΟΛΕΣ ---
st.subheader("💡 Έκτακτες Καταβολές (Προαιρετικό)")
st.write("Συμπληρώστε αν περιμένετε να έχετε κάποια έκτακτη εισροή χρημάτων σε συγκεκριμένα έτη (π.χ. bonus, πώληση ακινήτου, ακανόνιστα έσοδα).")

df_extra_init = pd.DataFrame({
    "Έτος": list(range(1, int(n) + 1)),
    "Έκτακτη Καταβολή (€)": [0.0] * int(n)
})

edited_df = st.data_editor(
    df_extra_init,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Έτος": st.column_config.NumberColumn("Έτος", disabled=True),
        "Έκτακτη Καταβολή (€)": st.column_config.NumberColumn("Έκτακτη Καταβολή (€)", min_value=0.0, format="€ %d")
    }
)

# --- ΑΝΑΛΟΓΙΣΤΙΚΗ ΜΗΧΑΝΗ (ΥΠΟΛΟΓΙΣΜΟΙ) ---
r_real = ((1 + r) / (1 + i)) - 1

if target_type == "Εφάπαξ":
    target_fv = target_today * ((1 + i) ** n)
elif target_type == "Μηνιαίες Δόσεις":
    annual_need_today = monthly_income * 12
    if r_real == 0:
        target_fv_real = annual_need_today * m
    else:
        target_fv_real = annual_need_today * ((1 - (1 + r_real)**(-m)) / r_real)
    target_fv = target_fv_real * ((1 + i) ** n)
else:
    fv_initial_lump = initial_lump_sum * ((1 + i) ** n)
    annual_need_today = annual_lump_sum + (monthly_income * 12)
    if r_real == 0:
        pv_annuity_real = annual_need_today * m
    else:
        pv_annuity_real = annual_need_today * ((1 - (1 + r_real)**(-m)) / r_real)
    fv_annuity = pv_annuity_real * ((1 + i) ** n)
    target_fv = fv_initial_lump + fv_annuity

fv_pv = PV * ((1 + r) ** n)

fv_extra = 0.0
for index, row in edited_df.iterrows():
    year = row["Έτος"]
    extra_amount = row["Έκτακτη Καταβολή (€)"]
    if extra_amount > 0:
        fv_extra += extra_amount * ((1 + r) ** (n - year))

shortfall = target_fv - fv_pv - fv_extra

if shortfall <= 0:
    pmt = 0.0
else:
    if r == g:
        pmt = shortfall / (n * ((1 + r)**(n-1)))
    else:
        pmt = shortfall / ((( (1 + r)**n ) - ( (1 + g)**n )) / (r - g))

years = list(range(1, int(n) + 1))
balance = [PV]
regular_contributions = []
extra_contributions = edited_df["Έκτακτη Καταβολή (€)"].tolist()

current_pmt = pmt
for year_idx in range(int(n)):
    reg_contrib = current_pmt if current_pmt > 0 else 0
    regular_contributions.append(reg_contrib)
    ext_contrib = extra_contributions[year_idx]
    
    new_balance = (balance[-1] + reg_contrib) * (1 + r) + ext_contrib
    balance.append(new_balance)
    
    current_pmt = current_pmt * (1 + g)

balance = balance[1:]

# --- ΕΜΦΑΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ---
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.info("🎯 Στόχος στη Λήξη (Αναπροσαρμοσμένος)")
    st.title(f"€ {format_gr(target_fv)}")

with col2:
    st.warning("📥 1η Τακτική Ετήσια Καταβολή")
    if shortfall <= 0:
        st.title("€ 0,00")
        st.write("Οι πόροι καλύπτουν τον στόχο!")
    else:
        st.title(f"€ {format_gr(pmt)}")
        st.write(f"(ή περίπου € {format_gr(pmt/12)} / μήνα)")

with col3:
    st.success("💰 Συνολικό Κεφάλαιο στη Λήξη")
    st.title(f"€ {format_gr(balance[-1])}")

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
    plot_bgcolor='rgba(0,0,0,0)'
)
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

st.plotly_chart(fig, use_container_width=True)
