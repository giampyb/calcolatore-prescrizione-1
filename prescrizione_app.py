import streamlit as st
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math

# --- Configurazione Pagina ---
# NOTA: Il tema (chiaro/scuro) si adatterà automaticamente
# alle impostazioni del tuo sistema (Mac/telefono).
st.set_page_config(page_title="Calcolatore Prescrizione", layout="centered")

# Stile CSS personalizzato
st.markdown("""
    <style>
    .reportview-container { margin-top: -2em; }
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .footer-disclaimer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f0f2f6; color: #555; text-align: center;
        padding: 10px; font-size: 12px; border-top: 1px solid #ccc;
    }
    /* Stili per tema chiaro (background-color) */
    body[data-theme="light"] .box-ordinaria {
        background-color: #fed7aa; /* Arancio Chiaro */
        color: #333;
    }
    body[data-theme="light"] .box-massima {
        background-color: #bbf7d0; /* Verde Chiaro */
        color: #333;
    }
    /* Stili per tema scuro (background-color) */
    body[data-theme="dark"] .box-ordinaria {
        background-color: #9a3412; /* Arancio Scuro */
        color: #fff;
    }
    body[data-theme="dark"] .box-massima {
        background-color: #166534; /* Verde Scuro */
        color: #fff;
    }
    .box-ordinaria, .box-massima {
        padding: 15px; border-radius: 10px; text-align: center;
        margin-bottom: 10px;
    }
    .big-date { font-size: 24px; font-weight: bold; display: block; }
    .label-result { font-size: 16px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚖️ Calcolatore Prescrizione Reati")

# --- COLONNE INPUT ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Pena Edittale")
    if 'pena_anni' not in st.session_state: st.session_state.pena_anni = 6

    def update_slider(): st.session_state.pena_anni = st.session_state.slider_key
    def update_number(): st.session_state.slider_key = st.session_state.pena_anni

    pena_anni = st.number_input("Anni", min_value=0, max_value=30, key='pena_anni', on_change=update_number)
    st.slider("Selettore Anni", 0, 30, key='slider_key', on_change=update_slider, label_visibility="collapsed")
    
    pena_mesi = st.number_input("Mesi", min_value=0, max_value=11, value=0)

with col2:
    st.subheader("2. Date")
    data_commissione = st.date_input("Data Commissione Reato", value=date(2015, 1, 1), format="DD/MM/YYYY")
    has_interruzione = st.checkbox("C'è stata interruzione?")
    data_interruzione = None
    if has_interruzione:
        data_interruzione = st.date_input("Data Ultima Interruzione", value=date.today(), format="DD/MM/YYYY")

# --- OPZIONI ---
st.subheader("3. Qualifiche e Recidiva")
c1, c2, c3 = st.columns(3)
with c1:
    is_tentato = st.checkbox("Reato Tentato (Art. 56)")
    is_raddoppio = st.checkbox("Raddoppio Termini")
with c2:
    tipo_reato = st.selectbox("Tipo Reato (Minimi)", ["Delitto (Min 6 anni)", "Contravvenzione (Min 4 anni)"])
    minimo_edittale = 6 if "Delitto" in tipo_reato else 4
with c3:
    cap_label = st.selectbox("Cap Aumento (Art. 161)", [
        "Standard (+1/4)", 
        "Recidiva Art. 99 c. 2,4,5 (+1/2)", 
        "Recidiva Art. 99 c. 6 (+2/3)", 
        "Abitualità (Doppio)"
    ])
    
    cap_val = 1.25
    if "1/2" in cap_label: cap_val = 1.5
    elif "2/3" in cap_label: cap_val = 1.66666
    elif "Doppio" in cap_label: cap_val = 2.0

# --- SOSPENSIONI ---
st.subheader("4. Sospensioni")
sosp_col1, sosp_col2 = st.columns([1, 2])

with sosp_col1:
    st.info("Automatiche")
    is_covid = st.checkbox("Sosp. COVID (64 gg)")
    
    orlando_days = 0
    start_orl = date(2017, 8, 3)
    end_orl = date(2019, 12, 31)
    if start_orl <= data_commissione <= end_orl:
        orlando_days = 548
        st.markdown("""<div style="background-color:#e0f2fe; padding:10px; border-radius:5px; font-size:12px; color:#0c4a6e;">
        <b>Regime Orlando Attivo:</b><br>Applicati +1.5 anni (548gg) automatici.</div>""", unsafe_allow_html=True)

with sosp_col2:
    st.write("Periodi Manuali (Aggiungi righe)")
    
    # Inizializzato con una lista vuota [] per permettere l'aggiunta dinamica
    edited_df = st.data_editor(
        [],  
        column_config={
            "Inizio": st.column_config.DateColumn("Data Inizio", format="DD/MM/YYYY"),
            "Fine": st.column_config.DateColumn("Data Fine", format="DD/MM/YYYY"),
        },
        num_rows="dynamic",
        hide_index=True,
        key="sospensioni_manuali"
    )

# --- LOGICA DI CALCOLO ---
if st.button("CALCOLA PRESCRIZIONE", use_container_width=True, type="primary"):
    
    logs = []
    
    pena_base_mesi = (pena_anni * 12) + pena_mesi
    logs.append("Pena edittale base: {} mesi".format(pena_base_mesi))

    if cap_val == 1.5:
        aumento = math.ceil(pena_base_mesi * 0.5)
        pena_base_mesi += aumento
        logs.append("Aumento Recidiva (+1/2) su base: +{} mesi -> Nuova base: {}".format(aumento, pena_base_mesi))
    elif 1.6 < cap_val < 1.7:
        aumento = math.ceil(pena_base_mesi * (2/3))
        pena_base_mesi += aumento
        logs.append("Aumento Recidiva (+2/3) su base: +{} mesi -> Nuova base: {}".format(aumento, pena_base_mesi))
    elif cap_val == 2.0:
        aumento = pena_base_mesi
        pena_base_mesi += aumento
        logs.append("Aumento Abitualità (+100%) su base: +{} mesi -> Nuova base: {}".format(aumento, pena_base_mesi))

    if is_tentato:
        riduzione = math.ceil(pena_base_mesi / 3)
        pena_base_mesi -= riduzione
        logs.append("Riduzione Tentativo (-1/3): -{} mesi -> Nuova base: {}".format(riduzione, pena_base_mesi))

    term_ordinario = pena_base_mesi
    minimo_mesi = minimo_edittale * 12
    if term_ordinario < minimo_mesi:
        term_ordinario = minimo_mesi
        logs.append("Applicazione Minimo Edittale ({} anni): Termine portato a {} mesi".format(minimo_edittale, term_ordinario))
    
    if is_raddoppio:
        term_ordinario *= 2
        logs.append("Raddoppio Termini: {} mesi".format(term_ordinario))

    giorni_sosp = 0
    
    manual_days = 0
    for row in edited_df:
        d_start = row.get("Inizio")
        d_end = row.get("Fine")
        if d_start and d_end and isinstance(d_start, date) and isinstance(d_end, date) and d_end > d_start:
            # CORREZIONE: Non conta il giorno finale
            delta = (d_end - d_start).days
            manual_days += delta
            logs.append("Sosp. Manuale {} - {}: {} giorni".format(d_start.strftime('%d/%m/%Y'), d_end.strftime('%d/%m/%Y'), delta))
    
    giorni_sosp += manual_days
    
    if is_covid: 
        # --- CORREZIONE DEL BUG ---
        # Era 'g_sosp', ora è 'giorni_sosp'
        giorni_sosp += 64
        logs.append("Sospensione COVID: +64 giorni")
    
    if orlando_days > 0:
        giorni_sosp += 548
        logs.append("Sospensione Orlando (L. 103/2017): +548 giorni")

    logs.append("<b>TOTALE SOSPENSIONI: {} giorni</b>".format(giorni_sosp))

    start_ord = data_interruzione if (has_interruzione and data_interruzione) else data_commissione
    data_ord_base = start_ord + relativedelta(months=term_ordinario)
    data_ord_finale = data_ord_base + timedelta(days=giorni_sosp)
    
    term_max_mesi = math.ceil(term_ordinario * cap_val)
    data_max_base = data_commissione + relativedelta(months=term_max_mesi)
    data_max_finale = data_max_base + timedelta(days=giorni_sosp)

    st.markdown("---")
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.markdown("""
        <div class="box-ordinaria">
            <span class="label-result">Prescrizione Ordinaria</span>
            <span class="big-date">{}</span>
            <small>(da {})</small>
        </div>
        """.format(data_ord_finale.strftime('%d/%m/%Y'), start_ord.strftime('%d/%m/%Y')), unsafe_allow_html=True)
        
    with res_col2:
        st.markdown("""
        <div class="box-massima">
            <span class="label-result">Prescrizione Massima</span>
            <span class="big-date">{}</span>
            <small>(da {})</small>
        </div>
        """.format(data_max_finale.strftime('%d/%m/%Y'), data_commissione.strftime('%d/%m/%Y')), unsafe_allow_html=True)

    with st.expander("🔍 Mostra passaggi dettagliati"):
        for log in logs:
            st.markdown("- {}".format(log), unsafe_allow_html=True)

st.markdown('<div class="footer-disclaimer">App realizzata dal dr. Giampiero Borraccia con Gemini AI</div>', unsafe_allow_html=True)