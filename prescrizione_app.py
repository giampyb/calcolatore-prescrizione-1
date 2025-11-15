import streamlit as st
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math
import pandas as pd

# --- FUNZIONE HELPER PER ANNI/MESI ---
def mesi_in_anni_mesi(tot_mesi):
    """Converte un numero totale di mesi in una stringa 'X anni e Y mesi'."""
    try:
        tot_mesi = int(tot_mesi)
        anni = tot_mesi // 12
        mesi = tot_mesi % 12
        if anni > 0:
            return f"{anni} {'anno' if anni == 1 else 'anni'} e {mesi} {'mese' if mesi == 1 else 'mesi'}"
        else:
            return f"{mesi} {'mese' if mesi == 1 else 'mesi'}"
    except Exception:
        return ""

# --- Configurazione Pagina ---
st.set_page_config(
    page_title="Calcolatore Prescrizione",
    layout="centered"
)

# Stile CSS personalizzato (SOLO TEMA CHIARO)
st.markdown("""
    <style>
    .reportview-container { margin-top: -2em; }
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .footer-disclaimer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f0f2f6; color: #000000; /* TESTO NERO */
        text-align: center;
        padding: 10px; font-size: 12px; border-top: 1px solid #ccc;
    }
    
    /* Stili per tema chiaro (rimossi quelli dark) */
    .box-ordinaria {
        background-color: #fed7aa; /* Arancio Chiaro */
        color: #000000; /* --- TESTO NERO --- */
    }
    .box-massima {
        background-color: #bbf7d0; /* Verde Chiaro */
        color: #000000; /* --- TESTO NERO --- */
    }
    
    .box-ordinaria, .box-massima {
        padding: 15px; border-radius: 10px; text-align: center;
        margin-bottom: 10px;
    }
    .big-date { font-size: 24px; font-weight: bold; display: block; }
    .label-result { font-size: 16px; font-weight: 600; }
    
    /* Forza sfondo BEIGE e TESTO NERO GLOBALE */
    body, .stApp {
        background-color: #F5F5DC !important; /* Beige */
        color: #000000 !important; /* TESTO NERO */
    }
    
    /* --- Forza testo nero su tutti gli elementi comuni --- */
    h1, h2, h3, h4, h5, h6, label, span, p, .st-emotion-cache-1jic0ts p,
    .st-emotion-cache-16idsys p, .st-emotion-cache-1h9ot3c {
        color: #000000 !important;
    }

    /* Sfondo BIANCO e Testo NERO per i widget di input */
    .stNumberInput input, 
    .stDateInput input, 
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; /* Bianco */
        color: #000000 !important; /* --- TESTO NERO --- */
    }
    div[data-baseweb="select"] > div {
        background-color: white !important;
        color: #000000 !important; /* --- TESTO NERO --- */
    }
    
    /* Eccezione per i box informativi (es. Orlando) */
    .st-emotion-cache-1wivapv {
        color: #0c4a6e !important; /* Mantiene il testo blu scuro per st.info */
    }
    
    /* --- Bottoni standard (es. "Aggiungi periodo") bianchi --- */
    div[data-testid="stButton"] > button {
        background-color: #FFFFFF !important; /* Sfondo bianco */
        color: #000000 !important;        /* Testo nero */
        border: 1px solid #CCCCCC !important; /* Bordo grigio chiaro */
    }

    /* --- MODIFICA CHECKBOX --- */
    
    /* 1. Rende il container del checkbox (la riga intera) bianco */
    div[data-testid="stCheckbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CCCCCC !important;
        padding-left: 10px; 
        border-radius: 8px; 
        padding-top: 5px; 
        padding-bottom: 5px; 
    }
    
    /* 2. Imposta il quadratino (quando NON spuntato) a GRIGIO */
    div[data-testid="stCheckbox"] input:not(:checked) + div {
        background-color: #EEEEEE !important; /* Grigio Chiaro */
        border: 1px solid #AAAAAA !important;
    }
    
    /* 3. Imposta il quadratino (quando SPUNTATO) a ROSSO */
    div[data-testid="stCheckbox"] input:checked + div {
        background-color: #D32F2F !important; /* Rosso */
        border-color: #B71C1C !important;
    }
    
    /* 4. Rende il segno di spunta bianco (visibile sul rosso) */
    div[data-testid="stCheckbox"] input:checked + div svg path {
        stroke: white !important;
    }
    /* --- FINE MODIFICA CHECKBOX --- */


    /* Allinea il pulsante di rimozione ❌ */
    .st-emotion-cache-1cflm81 {
        padding-top: 29px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚖️ Calcolatore Prescrizione Reati")

# --- Inizializza session_state per sospensioni ---
if 'active_periods' not in st.session_state:
    st.session_state.active_periods = []
if 'last_period_id' not in st.session_state:
    st.session_state.last_period_id = 0

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
    tipo_reato = st.selectbox("Tipo Reato (Minimo)", ["Delitto (Min 6 anni)", "Contravvenzione (Min 4 anni)"])
    minimo_edittale = 6 if "Delitto" in tipo_reato else 4
with c3:
    cap_label = st.selectbox("Aumento recidiva (Art. 161 c.p.)", [
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
    st.write("Periodi Manuali")
    
    # Pulsante per aggiungere nuovi periodi
    if st.button("Aggiungi periodo"):
        new_id = st.session_state.last_period_id + 1
        st.session_state.last_period_id = new_id
        st.session_state.active_periods.append(new_id)

    periods_to_remove = []

    # Mostra i campi data per ogni periodo attivo
    for period_id in st.session_state.active_periods:
        r_col1, r_col2, r_col3 = st.columns([4, 4, 1])
        with r_col1:
            st.date_input("Data Inizio", key=f"start_{period_id}", format="DD/MM/YYYY", value=None)
        with r_col2:
            st.date_input("Data Fine", key=f"end_{period_id}", format="DD/MM/YYYY", value=None)
        with r_col3:
            # Pulsante per rimuovere il periodo
            if st.button("❌", key=f"remove_{period_id}"):
                periods_to_remove.append(period_id)

    # Logica di rimozione (eseguita dopo il rendering)
    if periods_to_remove:
        st.session_state.active_periods = [p for p in st.session_state.active_periods if p not in periods_to_remove]
        # Pulisce i valori rimossi da session_state
        for p_id in periods_to_remove:
            if f"start_{p_id}" in st.session_state: del st.session_state[f"start_{p_id}"]
            if f"end_{p_id}" in st.session_state: del st.session_state[f"end_{p_id}"]
        st.rerun()


# --- LOGICA DI CALCOLO ---
if st.button("CALCOLA PRESCRIZIONE", use_container_width=True, type="primary"):
    
    logs = []
    
    pena_base_mesi = (pena_anni * 12) + pena_mesi
    # MODIFICA 1: Aggiunto (anni e mesi)
    logs.append(f"Pena edittale base: {pena_base_mesi} mesi ({mesi_in_anni_mesi(pena_base_mesi)})")

    if cap_val == 1.5:
        aumento = math.ceil(pena_base_mesi * 0.5)
        pena_base_mesi += aumento
        logs.append(f"Aumento Recidiva (+1/2) su base: +{aumento} mesi -> Nuova base: {pena_base_mesi} mesi ({mesi_in_anni_mesi(pena_base_mesi)})")
    elif 1.6 < cap_val < 1.7:
        aumento = math.ceil(pena_base_mesi * (2/3))
        pena_base_mesi += aumento
        logs.append(f"Aumento Recidiva (+2/3) su base: +{aumento} mesi -> Nuova base: {pena_base_mesi} mesi ({mesi_in_anni_mesi(pena_base_mesi)})")
    elif cap_val == 2.0:
        aumento = pena_base_mesi
        pena_base_mesi += aumento
        logs.append(f"Aumento Abitualità (+100%) su base: +{aumento} mesi -> Nuova base: {pena_base_mesi} mesi ({mesi_in_anni_mesi(pena_base_mesi)})")

    if is_tentato:
        riduzione = math.ceil(pena_base_mesi / 3)
        pena_base_mesi -= riduzione
        logs.append(f"Riduzione Tentativo (-1/3): -{riduzione} mesi -> Nuova base: {pena_base_mesi} mesi ({mesi_in_anni_mesi(pena_base_mesi)})")

    term_ordinario = pena_base_mesi
    minimo_mesi = minimo_edittale * 12
    if term_ordinario < minimo_mesi:
        term_ordinario = minimo_mesi
        logs.append(f"Tempo Minimo di Prescrizione ({minimo_edittale} anni): Termine portato a {term_ordinario} mesi ({mesi_in_anni_mesi(term_ordinario)})")
    
    if is_raddoppio:
        term_ordinario *= 2
        logs.append(f"Raddoppio Termini: {term_ordinario} mesi ({mesi_in_anni_mesi(term_ordinario)})")

    giorni_sosp = 0
    
    manual_days = 0
    for period_id in st.session_state.active_periods:
        d_start = st.session_state.get(f"start_{period_id}")
        d_end = st.session_state.get(f"end_{period_id}")
            
        if d_start and d_end:
            if d_end >= d_start:
                delta = (d_end - d_start).days + 1
                manual_days += delta
                logs.append(f"Sosp. Manuale {d_start.strftime('%d/%m/%Y')} - {d_end.strftime('%d/%m/%Y')}: {delta} giorni")
    
    giorni_sosp += manual_days
    
    if is_covid: 
        giorni_sosp += 64
        logs.append("Sospensione COVID: +64 giorni")
    
    if orlando_days > 0:
        giorni_sosp += 548
        logs.append("Sospensione Orlando (L. 103/2017): +548 giorni")

    logs.append(f"<b>TOTALE SOSPENSIONI: {giorni_sosp} giorni</b>")

    start_ord = data_interruzione if (has_interruzione and data_interruzione) else data_commissione
    data_ord_base = start_ord + relativedelta(months=term_ordinario)
    data_ord_finale = data_ord_base + timedelta(days=giorni_sosp)
    
    term_max_mesi = math.ceil(term_ordinario * cap_val)
    
    # MODIFICA 2: Aggiunto log per calcolo termine massimo
    logs.append(f"Calcolo termine massimo (Art. 161): {term_ordinario} mesi * {cap_val:.2f} ({cap_label}) = {term_max_mesi} mesi ({mesi_in_anni_mesi(term_max_mesi)})")

    data_max_base = data_commissione + relativedelta(months=term_max_mesi)
    data_max_finale = data_max_base + timedelta(days=giorni_sosp)

    st.markdown("---")
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.markdown(f"""
        <div class="box-ordinaria">
            <span class="label-result">Prescrizione Ordinaria</span>
            <span class="big-date">{data_ord_finale.strftime('%d/%m/%Y')}</span>
            <small>(da {start_ord.strftime('%d/%m/%Y')})</small>
        </div>
        """, unsafe_allow_html=True)
        
    with res_col2:
        st.markdown(f"""
        <div class="box-massima">
            <span class="label-result">Prescrizione Massima</span>
            <span class="big-date">{data_max_finale.strftime('%d/%m/%Y')}</span>
            <small>(da {data_commissione.strftime('%d/%m/%Y')})</small>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🔍 Mostra passaggi dettagliati"):
        for log in logs:
            st.markdown(f"- {log}", unsafe_allow_html=True)

st.markdown('<div class="footer-disclaimer">App realizzata dal dr. Giampiero Borraccia con Gemini AI</div>', unsafe_allow_html=True)