import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# Συνάρτηση για μορφοποίηση στο Ελληνικό πρότυπο
def format_gr(number):
    s = f"{number:,.2f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')

st.set_page_config(page_title="Strategic Financial Planning", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #f9f9fb;}
    h1 {color: #1E3A8A;}
    .stButton>button {background-color: #1E3A8A; color: white;}
    [data-testid="stSidebar"] img {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Φόρτωση Λογοτύπου
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)

# --- SIDEBAR: ΚΕΝΤΡΟ ΕΛΕΓΧΟΥ ---
st.sidebar.header("Κέντρο Ελέγχου Multi-Goal")
total_capital = st.sidebar.number_input("Συνολικό Διαθέσιμο Κεφάλαιο Σήμερα (€)", min_value=0.0, value=25000.0, step=1000.0)
num_goals = st.sidebar.number_input("Αριθμός Στόχων", min_value=1, max_value=5, value=2, step=1)

# --- MAIN PAGE ---
st.title("📈 Στρατηγικός Οικονομικός Σχεδιασμός")
st.markdown("Multi-Goal Wealth Management (v5.0)")
st.markdown("---")

# Δημιουργία δυναμικών καρτελών
tab_names = [f"Στόχος {i+1}" for i in range(num_goals)] + ["📊 Master Dashboard"]
tabs = st.tabs(tab_names)

all_results = []
total_allocated = 0.0
max_years = 0

# Επίλυση για κάθε Στόχο
for i in range(num_goals):
    with tabs[i]:
        st.header(f"Ρυθμίσεις Στόχου {i+1}")
        
        col_name, col_alloc = st.columns(2)
        goal_name = col_name.text_input("Ονομασία Στόχου", value=f"Στόχος {i+1}", key=f"name_{i}")
        allocated_pv = col_alloc.number_input("Δεσμευμένο Κεφάλαιο (από τα διαθέσιμα)", min_value=0.0, value=0.0, step=1000.0, key=f"pv_{i}")
        
        total_allocated += allocated_pv
        
        st.subheader("1. Οικονομικό Περιβάλλον")
        env1, env2, env3, env4 = st.columns(4)
        n = env1.number_input("Έτη Συσσώρευσης", 1, 60, 18 if i==0 else 30, key=f"n_{i}")
        r_acc = env2.number_input("Απόδοση Συσσώρευσης (%)", 0.0, 20.0, 5.0, key=f"r_acc_{i}") / 100
        r_ret = env3.number_input("Απόδοση Συνταξ/σης (%)", 0.0, 20.0, 0.0, key=f"r_ret_{i}") / 100
        inf = env4.number_input("Πληθωρισμός (%)", 0.0, 20.0, 3.0, key=f"inf_{i}") / 100
        
        if n > max_years:
            max_years = int(n)
            
        st.subheader("2. Μελλοντικός Στόχος")
        target_type = st.radio("Τύπος Στόχου", ("Εφάπαξ", "Μηνιαίες Δόσεις", "Μικτό (Εφάπαξ & Δόσεις)"), key=f"ttype_{i}")
        
        target_today = 0
        monthly_income = 0
        m = 0
        initial_lump_sum = 0
        annual_lump_sum = 0
        
        if target_type == "Εφάπαξ":
            target_today = st.number_input("Επιθυμητό Εφάπαξ (€ Σήμερα)", 0.0, 1000000.0, 50000.0, key=f"tt_{i}")
        elif target_type == "Μηνιαίες Δόσεις":
            col_t1, col_t2 = st.columns(2)
            monthly_income = col_t1.number_input("Μηνιαίο Εισόδημα (€ Σήμερα)", 0.0, 50000.0, 1500.0, key=f"mi_{i}")
            m = col_t2.number_input("Έτη Εισοδήματος", 1, 50, 20, key=f"m_{i}")
        else:
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            initial_lump_sum = col_t1.number_input("Αρχικό Εφάπαξ (€ Σήμερα)", 0.0, 500000.0, 15000.0, key=f"ils_{i}")
            annual_lump_sum = col_t2.number_input("Ετήσιο Εφάπαξ (€ Σήμερα)", 0.0, 100000.0, 5000.0, key=f"als_{i}")
            monthly_income = col_t3.number_input("Μηνιαίο Εισόδημα (€ Σήμερα)", 0.0, 50000.0, 500.0, key=f"mi2_{i}")
            m = col_t4.number_input("Έτη Δόσεων", 1, 50, 4, key=f"m2_{i}")
            
        st.subheader("3. Ευελιξία & Έκτακτες Καταβολές")
        flex1, flex2 = st.columns(2)
        g = flex1.number_input("Ετήσια Αύξηση Δόσης / Step-up (%)", 0.0, 20.0, 0.0, key=f"g_{i}") / 100
        
        df_extra_init = pd.DataFrame({"Έτος": list(range(1, int(n) + 1)), "Έκτακτη (€)": [0.0] * int(n)})
        edited_df = flex2.data_editor(df_extra_init, hide_index=True, use_container_width=True, key=f"df_{i}")
        
        # --- ΑΝΑΛΟΓΙΣΤΙΚΗ ΜΗΧΑΝΗ ---
        if target_type == "Εφάπαξ":
            target_fv = target_today * ((1 + inf) ** n)
        elif target_type == "Μηνιαίες Δόσεις":
            annual_need_today = monthly_income * 12
            C1 = annual_need_today * ((1 + inf) ** n)
            if r_ret == inf:
                target_fv = C1 * m
            else:
                target_fv = C1 * (1 - ((1 + inf) / (1 + r_ret)) ** m) / (r_ret - inf)
        else:
            fv_initial_lump = initial_lump_sum * ((1 + inf) ** n)
            annual_need_today = annual_lump_sum + (monthly_income * 12)
            C1 = annual_need_today * ((1 + inf) ** n)
            if r_ret == inf:
                fv_annuity = C1 * m
            else:
                fv_annuity = C1 * (1 - ((1 + inf) / (1 + r_ret)) ** m) / (r_ret - inf)
            target_fv = fv_initial_lump + fv_annuity
            
        fv_pv = allocated_pv * ((1 + r_acc) ** n)
        
        fv_extra = 0.0
        for index, row in edited_df.iterrows():
            y = row["Έτος"]
            ex = row["Έκτακτη (€)"]
            if ex > 0:
                fv_extra += ex * ((1 + r_acc) ** (n - y))
                
        shortfall = target_fv - fv_pv - fv_extra
        
        # Υπολογισμός Εφάπαξ Απαιτούμενου (Σημερινή Αξία Κενού)
        if shortfall <= 0:
            lump_sum_today = 0.0
            pmt = 0.0
        else:
            lump_sum_today = shortfall / ((1 + r_acc) ** n)
            
            if r_acc == g:
                pmt = shortfall / (n * ((1 + r_acc)**n))
            else:
                pmt = shortfall / ((((1 + r_acc)**n - (1 + g)**n) / (r_acc - g)) * (1 + r_acc))
                
        # Πίνακας Εξέλιξης
        years_list = list(range(1, int(n) + 1))
        balance = [allocated_pv]
        reg_contribs = []
        ext_contribs = edited_df["Έκτακτη (€)"].tolist()
        
        curr_pmt = pmt
        for y_idx in range(int(n)):
            rc = curr_pmt if curr_pmt > 0 else 0
            reg_contribs.append(rc)
            ec = ext_contribs[y_idx]
            
            new_bal = (balance[-1] + rc) * (1 + r_acc) + ec
            balance.append(new_bal)
            
            curr_pmt = curr_pmt * (1 + g)
            
        balance = balance[1:]
        
        all_results.append({
            "name": goal_name,
            "n": int(n),
            "reg": reg_contribs,
            "ext": ext_contribs,
            "lump_today": lump_sum_today
        })
        
        # --- ΕΜΦΑΝΙΣΗ ΚΑΡΤΩΝ (4 ΚΑΡΤΕΣ) ---
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            with st.container(border=True):
                st.caption("🎯 Στόχος στη Λήξη")
                st.subheader(f"€ {format_gr(target_fv)}")
        with c2:
            with st.container(border=True):
                st.caption("⚡ Απαιτούμενο Εφάπαξ Σήμερα")
                if shortfall <= 0:
                    st.subheader("€ 0,00")
                else:
                    st.subheader(f"€ {format_gr(lump_sum_today)}")
        with c3:
            with st.container(border=True):
                st.caption("📥 1η Τακτική Ετήσια Καταβολή")
                if shortfall <= 0:
                    st.subheader("€ 0,00")
                else:
                    st.subheader(f"€ {format_gr(pmt)}")
        with c4:
            with st.container(border=True):
                st.caption("💰 Συνολικό Κεφάλαιο στη Λήξη")
                st.subheader(f"€ {format_gr(balance[-1])}")
                st.write(f"*(Σημερινή Αξία: € {format_gr(balance[-1] / ((1 + inf)**n))})*")
                
        # --- ΓΡΑΦΗΜΑ ΣΤΟΧΟΥ ---
        fig = go.Figure()
        fig.add_trace(go.Bar(x=years_list, y=reg_contribs, name='Τακτική', marker_color='#FF9F1C'))
        fig.add_trace(go.Bar(x=years_list, y=ext_contribs, name='Έκτακτη', marker_color='#2A9D8F'))
        fig.add_trace(go.Scatter(x=years_list, y=balance, name='Κεφάλαιο', mode='lines+markers', marker_color='#1E3A8A'))
        fig.update_layout(title=f"Εξέλιξη Κεφαλαίου: {goal_name}", xaxis_title="Έτη", yaxis_title="Ποσό (€)", barmode='stack', hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig, use_container_width=True)

# --- MASTER DASHBOARD ---
with tabs[-1]:
    st.header("📊 Σύνοψη Χαρτοφυλακίου & Ταμειακών Ροών")
    
    unallocated = total_capital - total_allocated
    total_lump_required = sum([r["lump_today"] for r in all_results])
    
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        with st.container(border=True):
            st.caption("🏦 Διαθέσιμο Κεφάλαιο")
            st.subheader(f"€ {format_gr(total_capital)}")
    with mc2:
        with st.container(border=True):
            st.caption("⚖️ Αδιάθετο (Unallocated)")
            if unallocated < 0:
                st.error(f"€ {format_gr(unallocated)}")
            else:
                st.subheader(f"€ {format_gr(unallocated)}")
    with mc3:
        with st.container(border=True):
            st.caption("🚨 Συνολικό Εφάπαξ Κενό Σήμερα")
            st.subheader(f"€ {format_gr(total_lump_required)}")
            
    st.markdown("### 📈 Συγκεντρωτικές Ετήσιες Απαιτήσεις Ταμειακών Ροών")
    if max_years > 0:
        master_years = list(range(1, max_years + 1))
        master_reg = [0.0] * max_years
        master_ext = [0.0] * max_years
        
        for res in all_results:
            n_goal = res["n"]
            for y in range(n_goal):
                master_reg[y] += res["reg"][y]
                master_ext[y] += res["ext"][y]
                
        fig_master = go.Figure()
        fig_master.add_trace(go.Bar(x=master_years, y=master_reg, name='Σύνολο Τακτικών Καταβολών', marker_color='#FF9F1C'))
        fig_master.add_trace(go.Bar(x=master_years, y=master_ext, name='Σύνολο Έκτακτων Καταβολών', marker_color='#2A9D8F'))
        fig_master.update_layout(xaxis_title="Έτος Σχεδιασμού", yaxis_title="Συνολικό Απαιτούμενο Ποσό (€)", barmode='stack', hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_master, use_container_width=True)
