import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import base64

# Συνάρτηση για μορφοποίηση στο Ελληνικό πρότυπο
def format_gr(number):
    if number is None: return "0,00"
    s = f"{number:,.2f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')

# Συνάρτηση για μετατροπή εικόνας σε base64
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# Συνάρτηση δημιουργίας κειμένου ταμειακών ροών (Run-Length Encoding)
def get_cashflow_text(reg_list, ext_list, years):
    if not reg_list or years == 0:
        return []
    grouped_text = []
    current_val = reg_list[0] + ext_list[0]
    start_y = 1
    for y in range(1, years):
        val = reg_list[y] + ext_list[y]
        if round(val, 2) != round(current_val, 2):
            end_y = y
            if start_y == end_y:
                grouped_text.append(f"<b>Έτος {start_y}:</b> {format_gr(current_val)} €")
            else:
                grouped_text.append(f"<b>Από το έτος {start_y} έως {end_y}:</b> {format_gr(current_val)} € / έτος")
            start_y = y + 1
            current_val = val
    
    end_y = years
    if start_y == end_y:
        grouped_text.append(f"<b>Έτος {start_y}:</b> {format_gr(current_val)} €")
    else:
        grouped_text.append(f"<b>Από το έτος {start_y} έως {end_y}:</b> {format_gr(current_val)} € / έτος")
    return grouped_text

# Συνάρτηση δημιουργίας κειμένου μεταβλητών αποδόσεων (Glide Path RLE)
def get_rates_text(rates_list, years):
    if not rates_list or years == 0: return "0,00%"
    grouped = []
    curr = rates_list[0]
    start_y = 1
    for y in range(1, years):
        val = rates_list[y]
        if round(val, 2) != round(curr, 2):
            end_y = y
            if start_y == end_y:
                grouped.append(f"Έτος {start_y}: {format_gr(curr)}%")
            else:
                grouped.append(f"Έτη {start_y}-{end_y}: {format_gr(curr)}%")
            start_y = y + 1
            curr = val
    end_y = years
    if start_y == end_y:
        grouped.append(f"Έτος {start_y}: {format_gr(curr)}%")
    else:
        grouped.append(f"Έτη {start_y}-{end_y}: {format_gr(curr)}%")
    return ", ".join(grouped)

st.set_page_config(page_title="Strategic Financial Planning", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #f9f9fb;}
    h1 {color: #1E3A8A; margin-top: 0px; padding-top: 0px;}
    .stButton>button {background-color: #1E3A8A; color: white; width: 100%;}
    [data-testid="stSidebar"] img {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Φόρτωση Λογοτύπου
logo_b64 = ""
logo_file = None
if os.path.exists("logo.png"):
    logo_file = "logo.png"
    st.sidebar.image(logo_file, use_container_width=True)
    logo_b64 = get_base64_image(logo_file)
elif os.path.exists("logo.jpg"):
    logo_file = "logo.jpg"
    st.sidebar.image(logo_file, use_container_width=True)
    logo_b64 = get_base64_image(logo_file)

logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 110px; max-width: 100%;">' if logo_b64 else '<h2 style="margin:0; color:#1E3A8A;">Strategic Financial Planning</h2>'

# --- SIDEBAR: ΚΕΝΤΡΟ ΕΛΕΓΧΟΥ ---
st.sidebar.header("Κέντρο Ελέγχου Multi-Goal")

client_name = st.sidebar.text_input("Ονοματεπώνυμο Πελάτη", value="", placeholder=f"π.χ. Γιώργος Παπαδόπουλος")
total_capital = st.sidebar.number_input("Συνολικό Διαθέσιμο Κεφάλαιο Σήμερα (€)", min_value=0.0, value=None, step=1000.0)
tc_val = total_capital if total_capital is not None else 0.0

num_goals = st.sidebar.number_input("Αριθμός Στόχων", min_value=1, max_value=10, value=1, step=1)
ng_val = int(num_goals) if num_goals is not None else 2

safe_name = f"_{client_name.replace(' ', '_')}" if client_name.strip() else ""
display_name = client_name if client_name.strip() else "Μη Καθορισμένος"

# --- MAIN PAGE HEADER ---
col_main_title, col_main_logo = st.columns([4, 1])
with col_main_title:
    st.title("📈 Στρατηγικός Οικονομικός Σχεδιασμός")
    st.markdown("Multi-Goal Financial Planning Management")
with col_main_logo:
    if logo_b64:
        st.markdown(f"""
            <div style="text-align: right; margin-top: 15px;">
                <img src="data:image/png;base64,{logo_b64}" 
                     style="background-color: rgba(255, 255, 255, 0.9); padding: 15px; border-radius: 10px; max-height: 100px; border: 1px solid #e6e6f1; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            </div>
        """, unsafe_allow_html=True)
st.markdown("---")

tab_names = [f"Στόχος {i+1}" for i in range(ng_val)] + ["📊 Master Dashboard"]
tabs = st.tabs(tab_names)

all_results = []
total_allocated = 0.0
max_years = 0

allocated_list = []
for i in range(ng_val):
    alloc = st.session_state.get(f"pv_{i}", None)
    alloc_val = alloc if alloc is not None else 0.0
    allocated_list.append(alloc_val)
    
temp_total_allocated = sum(allocated_list)
remaining_global = tc_val - temp_total_allocated

if temp_total_allocated > tc_val and tc_val > 0:
    excess = temp_total_allocated - tc_val
    st.sidebar.error(f"🚨 **Υπέρβαση Κεφαλαίου κατά {format_gr(excess)} €!**\n\nΜειώστε τις δεσμεύσεις σας στους Στόχους.")

for i in range(ng_val):
    with tabs[i]:
        st.header(f"Ρυθμίσεις Στόχου {i+1}")
        
        col_name, col_alloc = st.columns(2)
        goal_name = col_name.text_input("Ονομασία Στόχου", value="", placeholder=f"π.χ. Στόχος {i+1}", key=f"name_{i}")
        goal_name_val = goal_name if goal_name.strip() else f"Στόχος {i+1}"
        
        allocated_pv = col_alloc.number_input("Κεφάλαιο που θέλω να δεσμεύσω από τα διαθέσιμα γι'αυτόν τον στόχο", min_value=0.0, value=None, step=1000.0, key=f"pv_{i}")
        alloc_val = allocated_pv if allocated_pv is not None else 0.0
        
        if remaining_global >= 0:
            col_alloc.caption(f"💡 Υπολειπόμενο διαθέσιμο προς κατανομή: **{format_gr(remaining_global)} €**")
        else:
            col_alloc.markdown(f"<span style='color:red; font-size:0.85em;'>🚨 Υπέρβαση κεφαλαίου! Αφαιρέστε {format_gr(abs(remaining_global))} €</span>", unsafe_allow_html=True)
            
        total_allocated += alloc_val
        
        st.subheader("1. Οικονομικό Περιβάλλον & Κύκλοι Αποδόσεων")
        env1, env2, env3, env4 = st.columns(4)
        n = env1.number_input("Συνολικά Έτη Συσσώρευσης", min_value=1, max_value=60, value=None, key=f"n_{i}")
        n_val = int(n) if n is not None else 0
        
        num_cycles = env2.number_input("Αριθμός Κύκλων Απόδοσης", min_value=1, max_value=10, value=1, key=f"num_cycles_{i}")
        
        r_ret = env3.number_input("Απόδοση Διατήρησης (%)", min_value=0.0, max_value=20.0, value=None, key=f"r_ret_{i}")
        r_ret_val = (r_ret if r_ret is not None else 0.0) / 100
        
        inf = env4.number_input("Πληθωρισμός (%)", min_value=0.0, max_value=20.0, value=None, key=f"inf_{i}")
        inf_val = (inf if inf is not None else 0.0) / 100
        
        if n_val > max_years:
            max_years = n_val

        rates_percent = []
        if n_val > 0:
            st.markdown("<span style='font-size:15px; font-weight:bold; color:#1E3A8A;'>Καθορισμός Αποδόσεων ανά Κύκλο (Glide Path)</span>", unsafe_allow_html=True)
            cols = st.columns(num_cycles)
            total_cycle_years = 0
            cycle_rates = []
            cycle_durations = []
            
            for c in range(num_cycles):
                with cols[c]:
                    with st.container(border=True):
                        st.caption(f"🔄 Κύκλος {c+1}")
                        c_rate = st.number_input(f"Απόδοση (%)", min_value=0.0, max_value=50.0, value=None, key=f"c_rate_{i}_{c}")
                        
                        if num_cycles == 1:
                            c_dur_val = n_val
                            st.write(f"Διάρκεια: **{c_dur_val} έτη**")
                        else:
                            c_dur = st.number_input(f"Διάρκεια (Έτη)", min_value=0, max_value=60, value=None, key=f"c_dur_{i}_{c}")
                            c_dur_val = int(c_dur) if c_dur is not None else 0
                            
                        c_rate_val = c_rate if c_rate is not None else 0.0
                        cycle_rates.append(c_rate_val)
                        cycle_durations.append(c_dur_val)
                        total_cycle_years += c_dur_val
            
            if num_cycles > 1:
                if total_cycle_years < n_val:
                    st.warning(f"⚠️ Έχετε ορίσει αποδόσεις για {total_cycle_years} από τα {n_val} έτη. Τα υπόλοιπα {n_val - total_cycle_years} έτη θα υπολογιστούν με 0%.")
                elif total_cycle_years > n_val:
                    st.error(f"🚨 Έχετε υπερβεί τα συνολικά έτη! Παρακαλώ προσαρμόστε τη διάρκεια των κύκλων. (Άθροισμα: {total_cycle_years} / Σύνολο: {n_val})")

            for rate, dur in zip(cycle_rates, cycle_durations):
                rates_percent.extend([rate] * dur)
            
            if len(rates_percent) < n_val:
                rates_percent.extend([0.0] * (n_val - len(rates_percent)))
            rates_percent = rates_percent[:n_val]
            
        st.subheader("2. Μελλοντικός Στόχος")
        target_type = st.radio("Τύπος Στόχου", ("Εφάπαξ", "Μηνιαίες Δόσεις", "Μικτό (Εφάπαξ & Δόσεις)"), key=f"ttype_{i}")
        
        target_today_val = 0.0
        monthly_income_val = 0.0
        m_val = 0
        initial_lump_sum_val = 0.0
        annual_lump_sum_val = 0.0
        
        if target_type == "Εφάπαξ":
            tt = st.number_input("Επιθυμητό Εφάπαξ στη Λήξη (Σε Σημερινή Αξία €)", min_value=0.0, max_value=10000000.0, value=None, key=f"tt_{i}")
            target_today_val = tt if tt is not None else 0.0
        elif target_type == "Μηνιαίες Δόσεις":
            col_t1, col_t2 = st.columns(2)
            mi = col_t1.number_input("Επιθυμητό Μηνιαίο Εισόδημα (Σε Σημερινή Αξία €)", min_value=0.0, max_value=50000.0, value=None, key=f"mi_{i}")
            monthly_income_val = mi if mi is not None else 0.0
            m = col_t2.number_input("Έτη Εισοδήματος", min_value=1, max_value=50, value=None, key=f"m_{i}")
            m_val = int(m) if m is not None else 0
        else:
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            ils = col_t1.number_input("Επιθυμητό Αρχικό Εφάπαξ (Σε Σημερινή Αξία €)", min_value=0.0, max_value=5000000.0, value=None, key=f"ils_{i}")
            initial_lump_sum_val = ils if ils is not None else 0.0
            als = col_t2.number_input("Επαναλαμβανόμενο/Ετήσιο Εφάπαξ (Σε Σημερινή Αξία €)", min_value=0.0, max_value=1000000.0, value=None, key=f"als_{i}")
            annual_lump_sum_val = als if als is not None else 0.0
            mi2 = col_t3.number_input("Επιθυμητό Μηνιαίο Εισόδημα (Σε Σημερινή Αξία €)", min_value=0.0, max_value=50000.0, value=None, key=f"mi2_{i}")
            monthly_income_val = mi2 if mi2 is not None else 0.0
            m2 = col_t4.number_input("Έτη Δόσεων", min_value=1, max_value=50, value=None, key=f"m2_{i}")
            m_val = int(m2) if m2 is not None else 0
            
        st.subheader("3. Ευελιξία & Έκτακτες Καταβολές (Βασικό Σενάριο)")
        flex1, flex2 = st.columns(2)
        g = flex1.number_input("Ετήσια Αύξηση Δόσης / Step-up (%)", min_value=0.0, max_value=20.0, value=None, key=f"g_{i}")
        g_val = (g if g is not None else 0.0) / 100
        
        rows_for_df = n_val if n_val > 0 else 1
        df_extra_init = pd.DataFrame({
            "Έτος": list(range(1, rows_for_df + 1)),
            "Απόδοση (%)": rates_percent if n_val > 0 else [0.0],
            "Έκτακτη (€)": [0.0] * rows_for_df
        })
        
        flex2.markdown("<span style='font-size:14px; font-weight:bold; color:#555;'>Έκτακτες Καταβολές (Η απόδοση ενημερώνεται αυτόματα)</span>", unsafe_allow_html=True)
        edited_df = flex2.data_editor(df_extra_init, hide_index=True, use_container_width=True, disabled=["Έτος", "Απόδοση (%)"], key=f"df_{i}")
        
        if n_val > 0:
            rates = [r / 100.0 for r in rates_percent]
            ext_contribs = edited_df["Έκτακτη (€)"].tolist()[:n_val]
            
            if target_type == "Εφάπαξ":
                target_fv = target_today_val * ((1 + inf_val) ** n_val)
            elif target_type == "Μηνιαίες Δόσεις":
                annual_need_today = monthly_income_val * 12
                C1 = annual_need_today * ((1 + inf_val) ** n_val)
                if r_ret_val == inf_val:
                    target_fv = C1 * m_val
                else:
                    target_fv = C1 * (1 - ((1 + inf_val) / (1 + r_ret_val)) ** m_val) / (r_ret_val - inf_val)
            else:
                fv_initial_lump = initial_lump_sum_val * ((1 + inf_val) ** n_val)
                annual_need_today = annual_lump_sum_val + (monthly_income_val * 12)
                C1 = annual_need_today * ((1 + inf_val) ** n_val)
                if r_ret_val == inf_val:
                    fv_annuity = C1 * m_val
                else:
                    fv_annuity = C1 * (1 - ((1 + inf_val) / (1 + r_ret_val)) ** m_val) / (r_ret_val - inf_val)
                target_fv = fv_initial_lump + fv_annuity
                
            fv_pv = alloc_val
            for r in rates:
                fv_pv *= (1 + r)
            
            fv_extra = 0.0
            for y_idx in range(n_val):
                val = ext_contribs[y_idx]
                for j in range(y_idx + 1, n_val):
                    val *= (1 + rates[j])
                fv_extra += val
                    
            shortfall = target_fv - fv_pv - fv_extra
            
            if shortfall <= 0:
                lump_sum_today = 0.0
                pmt = 0.0
            else:
                discount_factor = 1.0
                for r in rates:
                    discount_factor *= (1 + r)
                lump_sum_today = shortfall / discount_factor if discount_factor > 0 else shortfall
                
                fv_annuity_factor = 0.0
                for y_idx in range(n_val):
                    val = (1 + g_val)**y_idx
                    for j in range(y_idx, n_val):
                        val *= (1 + rates[j])
                    fv_annuity_factor += val
                    
                pmt = shortfall / fv_annuity_factor if fv_annuity_factor > 0 else 0.0
                    
            years_list = list(range(1, n_val + 1))
            balance = [alloc_val]
            reg_contribs = []
            
            curr_pmt = pmt
            for y_idx in range(n_val):
                rc = curr_pmt if curr_pmt > 0 else 0
                reg_contribs.append(rc)
                ec = ext_contribs[y_idx]
                
                new_bal = (balance[-1] + rc) * (1 + rates[y_idx]) + ec
                balance.append(new_bal)
                
                curr_pmt = curr_pmt * (1 + g_val)
                
            balance = balance[1:]
        else:
            target_fv = 0.0
            shortfall = 0.0
            lump_sum_today = 0.0
            pmt = 0.0
            years_list = []
            balance = [alloc_val]
            reg_contribs = []
            ext_contribs = []
            rates_percent = []
        
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            with st.container(border=True):
                st.caption("🎯 Στόχος στη Λήξη")
                st.subheader(f"€ {format_gr(target_fv)}")
        with c2:
            with st.container(border=True):
                st.caption("⚡ Απαιτούμενο Εφάπαξ Σήμερα (πέραν του δεσμευμένου)")
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
                final_bal = balance[-1] if len(balance) > 0 else 0.0
                st.subheader(f"€ {format_gr(final_bal)}")
                present_val = final_bal / ((1 + inf_val)**n_val) if n_val > 0 else final_bal
                st.write(f"*(Σημερινή Αξία: € {format_gr(present_val)})*")
                
        goal_cf_text = get_cashflow_text(reg_contribs, ext_contribs, n_val)
        st.markdown("### 📋 Απαιτούμενες Ταμειακές Ροές Στόχου")
        with st.container(border=True):
            if not goal_cf_text:
                st.write("Συμπληρώστε τα Έτη Συσσώρευσης και τις Αποδόσεις (Βήμα 1) για να υπολογιστούν οι ροές.")
            for text in goal_cf_text:
                st.write(f"🔹 {text.replace('<b>', '**').replace('</b>', '**')}")

        st.markdown("### 📈 Εξέλιξη Κεφαλαίου")
        if n_val > 0:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=years_list, y=reg_contribs, name='Τακτική', marker_color='#FF9F1C'))
            fig.add_trace(go.Bar(x=years_list, y=ext_contribs, name='Έκτακτη', marker_color='#2A9D8F'))
            fig.add_trace(go.Scatter(x=years_list, y=balance, name='Κεφάλαιο', mode='lines+markers', marker_color='#1E3A8A'))
            fig.update_layout(xaxis_title="Έτη", yaxis_title="Ποσό (€)", barmode='stack', hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Εισάγετε δεδομένα για να δείτε το γράφημα.")
            
        # --- WHAT-IF ΑΝΑΛΥΣΗ ---
        st.markdown("---")
        wi_fv = 0.0
        coverage_pct = 0.0
        wi_sales_text = ""
        wi_ext_contribs = []
        
        with st.expander("🔄 Εναλλακτικό Σενάριο (Αντίστροφη Αναζήτηση Εφικτότητας)"):
            st.markdown("Ελέγξτε τι ποσοστό του στόχου μπορείτε να καλύψετε με τα **διαθέσιμα χρήματα σήμερα** και μια **προκαθορισμένη τακτική ή/και έκτακτη αποταμίευση**.")
            
            col_wi1, col_wi2, col_wi3, col_wi4 = st.columns(4)
            wi_lump = col_wi1.number_input("Διαθέσιμο Εφάπαξ Σήμερα (€)", min_value=0.0, value=float(alloc_val), step=1000.0, key=f"wi_lump_{i}")
            wi_freq = col_wi2.selectbox("Συχνότητα Τακτικών Καταβολών", ["Μηνιαία", "Τριμηνιαία", "Εξαμηνιαία", "Ετήσια"], index=0, key=f"wi_freq_{i}")
            wi_pmt_freq = col_wi3.number_input(f"Ποσό (ανά {wi_freq.replace('ία', 'ίο')})", min_value=0.0, value=0.0, step=50.0, key=f"wi_pmt_{i}")
            wi_g = col_wi4.number_input("Ετήσια Αύξηση Δόσης (%)", min_value=0.0, max_value=20.0, value=0.0, step=0.5, key=f"wi_g_{i}")
            wi_g_val = wi_g / 100.0
            
            st.markdown("<span style='font-size:14px; font-weight:bold; color:#555;'>Έκτακτες Καταβολές Εναλλακτικού Σεναρίου (π.χ. Πώληση Ακινήτου, Μπόνους)</span>", unsafe_allow_html=True)
            
            col_wi_table, col_wi_empty = st.columns([1, 1])
            with col_wi_table:
                wi_df_extra_init = pd.DataFrame({
                    "Έτος": list(range(1, rows_for_df + 1)),
                    "Έκτακτη Εναλλακτικού (€)": [0.0] * rows_for_df
                })
                wi_edited_df = st.data_editor(wi_df_extra_init, hide_index=True, use_container_width=True, disabled=["Έτος"], key=f"wi_df_extra_{i}")
            
            if n_val > 0:
                wi_ext_contribs = wi_edited_df["Έκτακτη Εναλλακτικού (€)"].tolist()[:n_val]
                freq_multiplier = {"Μηνιαία": 12, "Τριμηνιαία": 4, "Εξαμηνιαία": 2, "Ετήσια": 1}
                wi_pmt_annual = wi_pmt_freq * freq_multiplier[wi_freq]
                
                wi_fv = wi_lump
                wi_curr_pmt = wi_pmt_annual
                
                for y_idx in range(n_val):
                    wi_fv = (wi_fv + wi_curr_pmt) * (1 + rates[y_idx]) + wi_ext_contribs[y_idx]
                    wi_curr_pmt = wi_curr_pmt * (1 + wi_g_val)
                    
                coverage_pct = (wi_fv / target_fv) * 100 if target_fv > 0 else 100.0
                coverage_ratio = coverage_pct / 100.0
                
                if target_fv > 0:
                    if target_type == "Εφάπαξ":
                        sec_lump = target_today_val * coverage_ratio
                        wi_sales_text = f"Πρακτικά, με αυτό το ρεαλιστικό σενάριο εξασφαλίζετε <b>{format_gr(sec_lump)} €</b> (σε σημερινή αγοραστική αξία) από τα {format_gr(target_today_val)} € που ήταν ο αρχικός σας στόχος."
                    elif target_type == "Μηνιαίες Δόσεις":
                        sec_mi = monthly_income_val * coverage_ratio
                        wi_sales_text = f"Πρακτικά, με αυτό το ρεαλιστικό σενάριο έχετε εξασφαλίσει <b>{format_gr(sec_mi)} € / μήνα</b> (σε σημερινή αγοραστική δύναμη) για ολόκληρη τη διάρκεια των {m_val} ετών, από τα {format_gr(monthly_income_val)} € που επιθυμείτε."
                    else:
                        sec_ils = initial_lump_sum_val * coverage_ratio
                        sec_als = annual_lump_sum_val * coverage_ratio
                        sec_mi = monthly_income_val * coverage_ratio
                        wi_sales_text = f"Πρακτικά, με αυτό το ρεαλιστικό σενάριο έχετε εξασφαλίσει αναλογικά (σε σημερινή αξία):<br>• <b>{format_gr(sec_ils)} €</b> Αρχικό Εφάπαξ<br>• <b>{format_gr(sec_als)} €</b> Ετήσιο Εφάπαξ<br>• <b>{format_gr(sec_mi)} € / μήνα</b> Εισόδημα"
                
                st.markdown("#### 📊 Αποτελέσματα Εναλλακτικού Σεναρίου")
                cw1, cw2, cw3 = st.columns(3)
                cw1.metric("Εκτιμώμενο Κεφάλαιο στη Λήξη", f"€ {format_gr(wi_fv)}")
                cw2.metric("Αρχικός Στόχος στη Λήξη", f"€ {format_gr(target_fv)}")
                cw3.metric("Ποσοστό Κάλυψης Στόχου", f"{format_gr(coverage_pct)}%")
                
                st.progress(min(coverage_pct / 100, 1.0))
                
                if wi_sales_text:
                    st.markdown(f"<div style='padding: 15px; background-color: #e8f4f8; border-left: 5px solid #2A9D8F; border-radius: 5px; margin-top: 15px; color: #1e293b;'>💡 {wi_sales_text}</div>", unsafe_allow_html=True)
                
                if coverage_pct < 100:
                    shortfall_wi = target_fv - wi_fv
                    st.warning(f"⚠️ Υπολείπονται **€ {format_gr(shortfall_wi)}** (σε μελλοντική αξία) για την 100% επίτευξη του στόχου.")
                else:
                    st.success("✅ Εξαιρετικά! Το εναλλακτικό σενάριο επαρκεί για να καλύψει πλήρως ή και να υπερβεί τον στόχο.")
            else:
                st.info("Συμπληρώστε τα έτη συσσώρευσης στο Βήμα 1 για να εμφανιστεί η ανάλυση.")
        
        all_results.append({
            "name": goal_name_val,
            "allocated_pv": alloc_val,
            "n": n_val,
            "rates": rates_percent,
            "r_ret": r_ret_val,
            "inf": inf_val,
            "g": g_val,
            "target_type": target_type,
            "target_today": target_today_val,
            "monthly_income": monthly_income_val,
            "m": m_val,
            "initial_lump_sum": initial_lump_sum_val,
            "annual_lump_sum": annual_lump_sum_val,
            "reg": reg_contribs,
            "ext": ext_contribs,
            "lump_today": lump_sum_today,
            "target_fv": target_fv,
            "balance_final": balance[-1] if len(balance) > 0 else 0.0,
            "wi_fv": wi_fv,
            "wi_coverage_pct": coverage_pct,
            "wi_sales_text": wi_sales_text,
            "wi_lump": wi_lump,
            "wi_freq": wi_freq,
            "wi_pmt_freq": wi_pmt_freq,
            "wi_g": wi_g,
            "wi_ext": wi_ext_contribs
        })

# --- MASTER DASHBOARD ---
with tabs[-1]:
    st.header("📊 Σύνοψη Χαρτοφυλακίου & Ταμειακών Ροών")
    
    unallocated = tc_val - total_allocated
    total_lump_required = sum([r["lump_today"] for r in all_results])
    
    if unallocated < 0:
        st.error(f"🚨 **Υπέρβαση Κεφαλαίου!** Έχετε υπερβεί το συνολικό διαθέσιμο κεφάλαιο κατά **{format_gr(abs(unallocated))} €**. Το μέγιστο κεφάλαιο που μπορείτε να χρησιμοποιήσετε είναι **{format_gr(tc_val)} €**.")
    
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        with st.container(border=True):
            st.caption("🏦 Συνολικό Διαθέσιμο Κεφάλαιο Σήμερα")
            st.subheader(f"€ {format_gr(tc_val)}")
    with mc2:
        with st.container(border=True):
            st.caption("⚖️ Υπολοιπόμενο Διαθέσιμο Κεφάλαιο προς Επένδυση (Unallocated)")
            if unallocated < 0:
                st.error(f"€ {format_gr(unallocated)}")
            else:
                st.subheader(f"€ {format_gr(unallocated)}")
    with mc3:
        with st.container(border=True):
            st.caption("🚨 Συνολικό Εφάπαξ Κενό Σήμερα")
            st.subheader(f"€ {format_gr(total_lump_required)}")
            
    st.markdown("### 📋 Συγκεντρωτικός Πίνακας Ταμειακών Ροών")
    
    master_years = []
    master_reg = []
    master_ext = []
    master_cf_text = []
    
    if max_years > 0:
        master_years = list(range(1, max_years + 1))
        master_reg = [0.0] * max_years
        master_ext = [0.0] * max_years
        
        for res in all_results:
            n_goal = res["n"]
            for y in range(n_goal):
                master_reg[y] += res["reg"][y]
                master_ext[y] += res["ext"][y]
        
        master_cf_text = get_cashflow_text(master_reg, master_ext, max_years)
            
        with st.container(border=True):
            for text in master_cf_text:
                st.write(f"🔹 {text.replace('<b>', '**').replace('</b>', '**')}")
                
        st.markdown("### 📈 Γράφημα Συνολικών Απαιτήσεων Ταμειακών Ροών")
        fig_master = go.Figure()
        fig_master.add_trace(go.Bar(x=master_years, y=master_reg, name='Σύνολο Τακτικών Καταβολών', marker_color='#FF9F1C'))
        fig_master.add_trace(go.Bar(x=master_years, y=master_ext, name='Σύνολο Έκτακτων Καταβολών', marker_color='#2A9D8F'))
        fig_master.update_layout(xaxis_title="Έτος Σχεδιασμού", yaxis_title="Συνολικό Απαιτούμενο Ποσό (€)", barmode='stack', hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_master, use_container_width=True)
    else:
        st.info("Συμπληρώστε τις παραμέτρους στους επιμέρους Στόχους για να δημιουργηθεί το πλάνο.")

    # --- ΕΞΑΓΩΓΕΣ (HTML / PDF) ---
    st.markdown("---")
    st.markdown("### 📄 Επιλογές Εξαγωγής")
    
    col_export1, col_export2 = st.columns(2)
    
    header_html = f"""
    <table style="width: 100%; border-bottom: 2px solid #FF9F1C; margin-bottom: 30px; padding-bottom: 10px;">
        <tr>
            <td style="width: 50%; vertical-align: middle; text-align: left;">
                {logo_img_tag}
            </td>
            <td style="width: 50%; text-align: right; vertical-align: middle;">
                <h2 style="margin: 0; color: #1E3A8A; font-size: 24px; border: none; padding: 0;">Στρατηγικό Οικονομικό Πλάνο</h2>
                <p style="margin: 5px 0 0 0; font-size: 16px; color: #555;"><b>Πελάτης:</b> {display_name}</p>
            </td>
        </tr>
    </table>
    """
    
    # CSS που μεταμορφώνει το έγγραφο σε παρουσίαση επιπέδου Marketing (Infographics)
    print_button_html = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        
        body { 
            font-family: 'Roboto', Tahoma, Geneva, Verdana, sans-serif; 
            color: #2b2b2b; 
            line-height: 1.6; 
            padding: 40px; 
            max-width: 1000px; 
            margin: 0 auto; 
            background-color: #fafbfc;
        }
        
        @media print {
            .no-print { display: none !important; }
            body { padding: 0 !important; margin: 0 !important; background-color: #fff; }
            .goal-card { page-break-inside: avoid; }
        }
        
        .print-btn {
            background-color: #1E3A8A; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-bottom: 25px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: background-color 0.3s;
        }
        .print-btn:hover { background-color: #152d6b; }
        
        /* Infographic CSS Elements */
        .summary-dashboard { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 30px; }
        .kpi-box { flex: 1; background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); border-top: 4px solid #1E3A8A; text-align: center; }
        .kpi-box.warning { border-top: 4px solid #e63946; }
        .kpi-title { font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; margin-bottom: 10px; }
        .kpi-value { font-size: 24px; color: #1E3A8A; font-weight: 700; margin: 0; }
        .kpi-value.warning { color: #e63946; }
        
        .goal-card { background: #fff; padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.03); }
        .goal-header { border-bottom: 2px solid #f0f2f5; padding-bottom: 15px; margin-bottom: 20px; }
        .goal-header h3 { margin: 0; color: #1E3A8A; font-size: 24px; display: flex; align-items: center; gap: 10px; }
        
        .story-section { margin-bottom: 25px; }
        .story-title { font-size: 18px; color: #2A9D8F; font-weight: 700; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
        .story-text { font-size: 15px; color: #444; background: #f8f9fa; padding: 15px 20px; border-radius: 8px; border-left: 4px solid #2A9D8F; margin: 0; }
        
        .strategy-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }
        .strategy-item { background: #f0f4f8; padding: 12px 15px; border-radius: 6px; font-size: 14px; }
        .strategy-item span { display: block; font-size: 12px; color: #666; text-transform: uppercase; }
        .strategy-item strong { color: #1E3A8A; font-size: 16px; }
        
        .action-plan { background: #fff9f0; padding: 20px; border-radius: 8px; border: 1px solid #ffe8cc; margin-top: 25px; }
        .action-title { color: #d97706; font-weight: 700; font-size: 16px; margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #ffe8cc; padding-bottom: 10px; }
        .cashflow-list { list-style: none; padding: 0; margin: 0; }
        .cashflow-list li { position: relative; padding-left: 20px; margin-bottom: 8px; font-size: 15px; }
        .cashflow-list li::before { content: '→'; position: absolute; left: 0; color: #FF9F1C; font-weight: bold; }
        
        .whatif-box { background: #f1f8f6; padding: 25px; border-radius: 8px; margin-top: 30px; border: 1px solid #d4ece6; }
        .whatif-title { color: #1c7b70; margin-top: 0; display: flex; align-items: center; gap: 8px; font-size: 18px; border-bottom: 1px solid #d4ece6; padding-bottom: 10px; }
        
        /* Custom Progress Bar CSS */
        .progress-wrapper { margin: 20px 0; }
        .progress-labels { display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; color: #555; margin-bottom: 5px; }
        .progress-track { height: 16px; background: #e2e8f0; border-radius: 10px; overflow: hidden; position: relative; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #2A9D8F 0%, #34d399 100%); transition: width 0.5s ease; }
        
        .sales-highlight { background: #fff; border-left: 4px solid #FF9F1C; padding: 15px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-top: 15px; font-size: 15px; color: #1e293b; font-weight: 500; }
        
        .footer { margin-top: 50px; font-size: 12px; color: #777; text-align: center; border-top: 1px solid #ddd; padding-top: 20px; }
    </style>
    <div class="no-print" style="text-align: right;">
        <button class="print-btn" onclick="window.print()">🖨️ Εκτύπωση / Αποθήκευση σε PDF</button>
    </div>
    """
    
    html_master_cf_list = "".join([f"<li>{t}</li>" for t in master_cf_text]) if master_cf_text else "<li>Δεν υπάρχουν ταμειακές ροές.</li>"
    
    detailed_goals_html = ""
    
    for res in all_results:
        if res['n'] == 0:
            continue
        
        rates_str = get_rates_text(res['rates'], res['n'])
        goal_cf_text = get_cashflow_text(res['reg'], res['ext'], res['n'])
        goal_cf_html = "".join([f"<li>{t}</li>" for t in goal_cf_text]) if goal_cf_text else "<li>Καμία επιπλέον ροή δεν απαιτείται. Το κεφάλαιο επαρκεί.</li>"
        
        # --- Αφήγηση Στόχου ---
        if res['target_type'] == "Εφάπαξ":
            target_desc = f"συνολικό εφάπαξ κεφάλαιο ύψους <b>{format_gr(res['target_today'])} €</b> (σε σημερινή αγοραστική δύναμη)"
        elif res['target_type'] == "Μηνιαίες Δόσεις":
            target_desc = f"ένα σταθερό μηνιαίο εισόδημα <b>{format_gr(res['monthly_income'])} €</b> για διάστημα <b>{res['m']} ετών</b>"
        else:
            target_desc = f"έναν συνδυασμό παροχών: <b>{format_gr(res['initial_lump_sum'])} €</b> ως αρχικό εφάπαξ, <b>{format_gr(res['annual_lump_sum'])} €</b> ετησίως και <b>{format_gr(res['monthly_income'])} €</b> τον μήνα για <b>{res['m']} χρόνια</b>"

        # --- Αφήγηση Εναλλακτικού Σεναρίου (What-If) ---
        wi_export_html = ""
        if res.get('wi_sales_text'):
            wi_ext_text = f"<br>• Έκτακτες καταβολές: <b>Ναι</b>" if sum(res.get('wi_ext', [])) > 0 else ""
            fill_pct = min(res['wi_coverage_pct'], 100)
            
            wi_export_html = f"""
            <div class="whatif-box">
                <h4 class="whatif-title">🔄 Η Σημερινή σας Πραγματικότητα (Εναλλακτικό Σενάριο)</h4>
                <p style="font-size: 14px; margin-bottom: 15px;">Ας δούμε τι ακριβώς πετυχαίνουμε με βάση τις σημερινές σας δυνατότητες αποταμίευσης. Υπολογίσαμε το παρακάτω σενάριο ρευστότητας:</p>
                
                <div class="strategy-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 20px;">
                    <div class="strategy-item"><span>Διαθέσιμο Εφάπαξ</span><strong>{format_gr(res.get('wi_lump', 0))} €</strong></div>
                    <div class="strategy-item"><span>Τακτική Αποταμίευση</span><strong>{format_gr(res.get('wi_pmt_freq', 0))} € /{res.get('wi_freq', '').replace('ία', 'ίο').replace('σια', 'σιο')}</strong></div>
                    <div class="strategy-item"><span>Ετήσια Αύξηση Δόσης</span><strong>{format_gr(res.get('wi_g', 0)*100)}%</strong></div>
                    <div class="strategy-item"><span>Εκτιμώμενη Λήξη</span><strong>{format_gr(res['wi_fv'])} €</strong></div>
                </div>
                
                <div class="progress-wrapper">
                    <div class="progress-labels">
                        <span>Ποσοστό Επίτευξης Αρχικού Στόχου</span>
                        <span style="color: #2A9D8F; font-size: 15px;">{format_gr(res['wi_coverage_pct'])}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" style="width: {fill_pct}%;"></div>
                    </div>
                </div>
                
                <div class="sales-highlight">
                    💡 {res['wi_sales_text']}
                </div>
            </div>
            """
        
        detailed_goals_html += f"""
        <div class="goal-card">
            <div class="goal-header">
                <h3>🎯 Στόχος: {res['name']}</h3>
            </div>
            
            <div class="story-section">
                <div class="story-title">Το Όραμά σας</div>
                <p class="story-text">Μας ζητήσατε να σχεδιάσουμε το μέλλον, ώστε σε <b>{res['n']} χρόνια από σήμερα</b> να έχετε απόλυτα εξασφαλίσει {target_desc}. Για να διασφαλίσουμε ότι τα χρήματά σας δεν θα χάσουν την αξία τους, έχουμε συνυπολογίσει έναν μέσο μακροπρόθεσμο πληθωρισμό <b>{res['inf']*100:.2f}%</b>.</p>
            </div>

            <div class="story-section">
                <div class="story-title">Η Επενδυτική Στρατηγική μας</div>
                <p class="story-text" style="background: #fdfdfd; border-color: #1E3A8A;">Για να προστατέψουμε το κεφάλαιό σας, θα εφαρμόσουμε μια δυναμική στρατηγική (Glide Path). Αξιοποιώντας το σημερινό δεσμευμένο κεφάλαιο των <b>{format_gr(res['allocated_pv'])} €</b>, θα ξεκινήσουμε με υψηλότερες αποδόσεις και σταδιακά θα "κλειδώνουμε" το κέρδος, μειώνοντας το ρίσκο όσο πλησιάζουμε στον στόχο σας.</p>
                
                <div class="strategy-grid">
                    <div class="strategy-item"><span>Κύκλοι Αποδόσεων (Glide Path)</span><strong>{rates_str}</strong></div>
                    <div class="strategy-item"><span>Απόδοση την περίοδο παροχών</span><strong>{res['r_ret']*100:.2f}%</strong></div>
                </div>
            </div>
            
            <div class="action-plan">
                <h4 class="action-title">🚀 Το Σχέδιο Δράσης (Για 100% Επίτευξη)</h4>
                <p style="margin-top:0; font-size: 14px; color: #555;">Για να πετύχετε τον στόχο σας στο απόλυτο ακέραιο, θα χρειαστεί σήμερα ένα <b>επιπλέον</b> εφάπαξ κεφάλαιο ύψους <b>{format_gr(res['lump_today'])} €</b>. <br>Εναλλακτικά, εάν επιλέξετε την τακτική αποταμίευση (με ετήσια αύξηση της δόσης κατά {res['g']*100:.2f}%), οι απαιτούμενες ταμειακές ροές διαμορφώνονται ως εξής:</p>
                <ul class="cashflow-list">
                    {goal_cf_html}
                </ul>
            </div>
            
            {wi_export_html}
        </div>
        """

    detailed_html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Στρατηγικό Οικονομικό Πλάνο - {display_name}</title>
        {print_button_html}
    </head>
    <body>
        {header_html}
        
        <h2 style="color: #1E3A8A; font-weight: 300; text-align: center; margin-bottom: 30px;">Σύνοψη Διαθέσιμου Χαρτοφυλακίου</h2>
        
        <div class="summary-dashboard">
            <div class="kpi-box">
                <div class="kpi-title">Συνολικό Διαθέσιμο Κεφάλαιο Σήμερα</div>
                <div class="kpi-value">{format_gr(tc_val)} €</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-title">Διαθέσιμο Κεφάλαιο (Unallocated)</div>
                <div class="kpi-value">{format_gr(unallocated)} €</div>
            </div>
            <div class="kpi-box warning">
                <div class="kpi-title">Συνολικό Εφάπαξ Έλλειμμα (Σήμερα)</div>
                <div class="kpi-value warning">{format_gr(total_lump_required)} €</div>
            </div>
        </div>

        <h2 style="color: #1E3A8A; font-weight: 300; margin-top: 40px; border-bottom: 2px solid #eee; padding-bottom: 10px;">Αναλυτική Χαρτογράφηση Στόχων</h2>
        {detailed_goals_html}

        <h2 style="color: #1E3A8A; font-weight: 300; margin-top: 40px; border-bottom: 2px solid #eee; padding-bottom: 10px;">Ολιστικό Σχέδιο Ταμειακών Ροών</h2>
        <div class="action-plan" style="background: #fff; border: 1px solid #e2e8f0;">
            <p style="margin-top:0; font-size: 15px; color: #555;">Παρακάτω παρουσιάζεται το άθροισμα όλων των απαιτούμενων ταμειακών ροών (για όλους τους στόχους) προκειμένου να πετύχετε την πλήρη οικονομική σας ανεξαρτησία βάσει του αρχικού σχεδιασμού:</p>
            <ul class="cashflow-list" style="margin-top: 15px;">
                {html_master_cf_list}
            </ul>
        </div>
        
        <div class="footer">
            <strong>Αυτή η έκθεση αποτελεί τον προσωπικό σας χάρτη για την οικονομική σας εξασφάλιση.</strong><br><br>
            Δημιουργήθηκε μέσω του Συστήματος Στρατηγικού Οικονομικού Σχεδιασμού.<br>
            Baltassis - Strategic Financial Planning Partner<br>
        </div>
    </body>
    </html>
    """
    
    with col_export1:
        st.download_button(
            label="📄 Σύντομη Εξαγωγή (Απλή HTML)",
            data=detailed_html_content, # Ενοποιήσαμε την ποιότητα.
            file_name=f"Financial_Plan_Overview{safe_name}.html",
            mime="text/html",
            use_container_width=True
        )
        
    with col_export2:
        st.download_button(
            label="📊 Αναλυτική Εξαγωγή (Οπτική Infographic / PDF)",
            data=detailed_html_content,
            file_name=f"Financial_Plan_Detailed{safe_name}.html",
            mime="text/html",
            use_container_width=True
        )
