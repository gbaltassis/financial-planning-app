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

# --- MAIN PAGE HEADER (Εμφανίζεται σταθερά στην κορυφή) ---
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

# Υπολογισμός συνολικού δεσμευμένου κεφαλαίου για UI
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

# Επίλυση για κάθε Στόχο
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
        
        st.subheader("1. Οικονομικό Περιβάλλον")
        env1, env2, env3, env4 = st.columns(4)
        n = env1.number_input("Έτη Συσσώρευσης", min_value=1, max_value=60, value=None, key=f"n_{i}")
        n_val = int(n) if n is not None else 0
        
        r_acc = env2.number_input("Βασική Απόδοση Συσσώρευσης (%)", min_value=0.0, max_value=20.0, value=None, key=f"r_acc_{i}")
        
        r_ret = env3.number_input("Απόδοση Διατήρησης (%)", min_value=0.0, max_value=20.0, value=None, key=f"r_ret_{i}")
        r_ret_val = (r_ret if r_ret is not None else 0.0) / 100
        
        inf = env4.number_input("Πληθωρισμός (%)", min_value=0.0, max_value=20.0, value=None, key=f"inf_{i}")
        inf_val = (inf if inf is not None else 0.0) / 100
        
        if n_val > max_years:
            max_years = n_val
            
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
            
        st.subheader("3. Ευελιξία, Αποδόσεις & Έκτακτες Καταβολές")
        flex1, flex2 = st.columns(2)
        g = flex1.number_input("Ετήσια Αύξηση Δόσης / Step-up (%)", min_value=0.0, max_value=20.0, value=None, key=f"g_{i}")
        g_val = (g if g is not None else 0.0) / 100
        
        # Πίνακας έκτακτων καταβολών με Δυναμική Απόδοση
        rows_for_df = n_val if n_val > 0 else 1
        default_rate = r_acc if r_acc is not None else 0.0
        df_extra_init = pd.DataFrame({
            "Έτος": list(range(1, rows_for_df + 1)),
            "Απόδοση (%)": [default_rate] * rows_for_df,
            "Έκτακτη (€)": [0.0] * rows_for_df
        })
        
        flex2.markdown("<span style='font-size:14px; font-weight:bold; color:#555;'>Παραμετροποίηση ανά Έτος</span>", unsafe_allow_html=True)
        edited_df = flex2.data_editor(df_extra_init, hide_index=True, use_container_width=True, key=f"df_{i}")
        
        # --- ΑΝΑΛΟΓΙΣΤΙΚΗ ΜΗΧΑΝΗ (Εκτελείται μόνο αν έχει μπει το Έτος Συσσώρευσης) ---
        if n_val > 0:
            rates_percent = edited_df["Απόδοση (%)"].tolist()[:n_val]
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
                
            # Προεξόφληση/Ανατοκισμός με Μεταβλητά Επιτόκια
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
        
        # Αποθήκευση όλων των παραμέτρων
        all_results.append({
            "name": goal_name_val,
            "n": n_val,
            "rates": rates_percent,
            "r_ret": r_ret_val,
            "inf": inf_val,
            "g": g_val,
            "target_type": target_type,
            "reg": reg_contribs,
            "ext": ext_contribs,
            "lump_today": lump_sum_today,
            "target_fv": target_fv,
            "balance_final": balance[-1] if len(balance) > 0 else 0.0
        })
        
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
                st.write("Συμπληρώστε τα Έτη Συσσώρευσης (κελί 1) για να υπολογιστούν οι ροές.")
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
            st.caption("⚖️ Υπολοιπόμενο Διαθέσιμο Κεφάλαιο προς Επένδυση (Unallocated) - Δεν αξιοποιήθηκε για τους στόχους")
            if unallocated < 0:
                st.error(f"€ {format_gr(unallocated)}")
            else:
                st.subheader(f"€ {format_gr(unallocated)}")
    with mc3:
        with st.container(border=True):
            st.caption("🚨 Συνολικό Εφάπαξ Κενό Σήμερα (Κεφάλαιο που απαιτείται σήμερα για την επίτευξη του συνόλου των στόχων)")
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
    
    print_button_html = """
    <style>
        @media print {
            .no-print { display: none !important; }
            body { padding: 0 !important; margin: 0 !important; }
        }
        .print-btn {
            background-color: #1E3A8A;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 25px;
            display: inline-block;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: background-color 0.3s;
        }
        .print-btn:hover { background-color: #152d6b; }
    </style>
    <div class="no-print" style="text-align: right;">
        <button class="print-btn" onclick="window.print()">🖨️ Εκτύπωση / Αποθήκευση σε PDF</button>
    </div>
    """
    
    html_master_cf_list = "".join([f"<li>{t}</li>" for t in master_cf_text]) if master_cf_text else "<li>Δεν υπάρχουν ταμειακές ροές.</li>"
    
    goals_short_html = ""
    detailed_goals_html = ""
    
    for res in all_results:
        if res['n'] == 0:
            continue
        
        rates_str = get_rates_text(res['rates'], res['n'])
        goal_cf_text = get_cashflow_text(res['reg'], res['ext'], res['n'])
        goal_cf_html = "".join([f"<li style='font-size: 14px; margin-bottom: 4px;'>{t}</li>" for t in goal_cf_text]) if goal_cf_text else "<li>Καμία Ροή</li>"
        
        goals_short_html += f"""
        <div style='background: #f4f6f9; padding: 15px; margin-bottom: 10px; border-radius: 8px;'>
            <h3 style='margin-top: 0; color: #1E3A8A;'>{res['name']}</h3>
            <p><b>Διάρκεια:</b> {res['n']} έτη</p>
            <p><b>Στόχος στη Λήξη:</b> {format_gr(res['target_fv'])} €</p>
            <p><b>Απαιτούμενο Εφάπαξ Σήμερα:</b> {format_gr(res['lump_today'])} €</p>
            <div style='margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd;'>
                <p style='margin-bottom: 5px; font-weight: bold; color: #555;'>Ταμειακές Ροές Στόχου:</p>
                <ul style='padding: 5px 20px; background: none; border: none;'>{goal_cf_html}</ul>
            </div>
        </div>
        """
        
        detailed_goals_html += f"""
        <div style='background: #f4f6f9; padding: 20px; margin-bottom: 15px; border-radius: 8px; border-left: 6px solid #1E3A8A;'>
            <h3 style='margin-top: 0; color: #1E3A8A; font-size: 22px;'>{res['name']}</h3>
            <table style='width: 100%; border-collapse: collapse; margin-bottom: 15px;'>
                <tr>
                    <td style='padding: 5px; width: 50%;'><b>Έτη Συσσώρευσης:</b> {res['n']}</td>
                    <td style='padding: 5px; width: 50%;'><b>Απόδοση Συσσώρευσης:</b> {rates_str}</td>
                </tr>
                <tr>
                    <td style='padding: 5px;'><b>Απόδοση Διατήρησης:</b> {res['r_ret']*100:.2f}%</td>
                    <td style='padding: 5px;'><b>Πληθωρισμός:</b> {res['inf']*100:.2f}%</td>
                </tr>
                <tr>
                    <td style='padding: 5px;'><b>Ετήσια Αύξηση Δόσης (Step-up):</b> {res['g']*100:.2f}%</td>
                    <td style='padding: 5px;'><b>Τύπος Στόχου:</b> {res['target_type']}</td>
                </tr>
            </table>
            <div style='border-top: 1px solid #ddd; padding-top: 10px;'>
                <p><b>Στόχος στη Λήξη (Αναπροσαρμοσμένος):</b> {format_gr(res['target_fv'])} €</p>
                <p><b>Απαιτούμενο Επιπλέον Εφάπαξ Σήμερα:</b> {format_gr(res['lump_today'])} €</p>
                <p><b>Συνολικό Κεφάλαιο στη Λήξη:</b> {format_gr(res['balance_final'])} €</p>
            </div>
            <div style='margin-top: 15px; padding-top: 10px; border-top: 1px dashed #aaa;'>
                <p style='margin-bottom: 5px; font-weight: bold; color: #555;'>Απαιτούμενες Ταμειακές Ροές Στόχου:</p>
                <ul style='padding: 5px 20px; background: none; border: none;'>{goal_cf_html}</ul>
            </div>
        </div>
        """

    short_html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Συνοπτικό Οικονομικό Πλάνο</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; padding: 40px; max-width: 900px; margin: 0 auto; }}
            h2 {{ color: #2A9D8F; margin-top: 30px; }}
            .summary-box {{ border: 2px solid #1E3A8A; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
            ul.master-cf {{ background: #f9f9fb; padding: 20px 40px; border-radius: 8px; border-left: 5px solid #FF9F1C; }}
            ul.master-cf li {{ margin-bottom: 10px; font-size: 16px; }}
            .footer {{ margin-top: 50px; font-size: 12px; color: #777; text-align: center; border-top: 1px solid #ddd; padding-top: 20px; }}
        </style>
    </head>
    <body>
        {print_button_html}
        {header_html}
        
        <div class="summary-box">
            <h2>Γενική Σύνοψη</h2>
            <p><b>Συνολικό Διαθέσιμο Κεφάλαιο:</b> {format_gr(tc_val)} €</p>
            <p><b>Αδιάθετο Υπόλοιπο:</b> {format_gr(unallocated)} €</p>
            <p><b>Συνολικό Εφάπαξ Κενό Σήμερα:</b> {format_gr(total_lump_required)} €</p>
        </div>

        <h2>Ανάλυση Στόχων</h2>
        {goals_short_html}

        <h2>Συγκεντρωτικό Πλάνο Ταμειακών Ροών</h2>
        <ul class="master-cf">
            {html_master_cf_list}
        </ul>
        
        <div class="footer">
            Δημιουργήθηκε μέσω του Συστήματος Στρατηγικού Οικονομικού Σχεδιασμού.<br>
            Baltassis - Strategic Financial Planning Partner<br>
        </div>
    </body>
    </html>
    """
    
    detailed_html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Αναλυτικό Οικονομικό Πλάνο</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; padding: 40px; max-width: 1000px; margin: 0 auto; }}
            h2 {{ color: #2A9D8F; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            .summary-box {{ border: 2px solid #1E3A8A; padding: 20px; border-radius: 10px; margin-bottom: 30px; background-color: #fff; }}
            ul.master-cf {{ background: #f9f9fb; padding: 20px 40px; border-radius: 8px; border-left: 5px solid #FF9F1C; }}
            ul.master-cf li {{ margin-bottom: 10px; font-size: 16px; }}
            .footer {{ margin-top: 50px; font-size: 12px; color: #777; text-align: center; border-top: 1px solid #ddd; padding-top: 20px; }}
        </style>
    </head>
    <body>
        {print_button_html}
        {header_html}
        
        <div class="summary-box">
            <h2>Γενική Σύνοψη Χαρτοφυλακίου</h2>
            <p><b>Συνολικό Διαθέσιμο Κεφάλαιο Σήμερα:</b> {format_gr(tc_val)} €</p>
            <p><b>Διαθέσιμο Κεφάλαιο προς Επένδυση (Unallocated):</b> {format_gr(unallocated)} €</p>
            <p><b>Συνολικό Εφάπαξ Κενό Σήμερα:</b> {format_gr(total_lump_required)} €</p>
        </div>

        <h2>Αναλυτικές Καρτέλες Στόχων</h2>
        {detailed_goals_html}

        <h2>Συγκεντρωτικό Πλάνο Ταμειακών Ροών (Όλοι οι Στόχοι)</h2>
        <ul class="master-cf">
            {html_master_cf_list}
        </ul>
        
        <div class="footer">
            Δημιουργήθηκε μέσω του Συστήματος Στρατηγικού Οικονομικού Σχεδιασμού.<br>
            Baltassis - Strategic Financial Planning Partner<br>
        </div>
    </body>
    </html>
    """
    
    with col_export1:
        st.download_button(
            label="📄 Σύντομη Εξαγωγή",
            data=short_html_content,
            file_name=f"Financial_Plan_Short{safe_name}.html",
            mime="text/html",
            use_container_width=True
        )
        
    with col_export2:
        st.download_button(
            label="📊 Αναλυτική Εξαγωγή (Χωρίς Γράφημα)",
            data=detailed_html_content,
            file_name=f"Financial_Plan_Detailed{safe_name}.html",
            mime="text/html",
            use_container_width=True
        )
