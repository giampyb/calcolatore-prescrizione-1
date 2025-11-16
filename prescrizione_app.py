import streamlit as st
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math
import pandas as pd

# --- NUOVA FUNZIONE HELPER PER CALCOLO IBRIDO ---
def format_hybrid_time(float_mesi):
    """Converte mesi fluttuanti (es. 2.666) in stringa 'X mesi e Y giorni'."""
    try:
        mesi_int = math.floor(float_mesi)
        giorni = math.floor((float_mesi - mesi_int) * 30)
        
        anni = mesi_int // 12
        mesi_rimanenti = mesi_int % 12
        
        parts = []
        if anni > 0:
            parts.append(f"{anni} {'anno' if anni == 1 else 'anni'}")
        if mesi_rimanenti > 0:
            parts.append(f"{mesi_rimanenti} {'mese' if mesi_rimanenti == 1 else 'mesi'}")
        
        # Aggiunge i giorni solo se ci sono, o se è l'unico valore
        if giorni > 0:
            parts.append(f"{giorni} {'giorno' if giorni == 1 else 'giorni'}")
        
        if not parts:
            return "0 giorni"
        
        # Logica di congiunzione
        if len(parts) == 1:
            return parts[0]
        if len(parts) == 2:
            return f"{parts[0]} e {parts[1]}"
        if len(parts) == 3: # Max caso: Anni, Mesi e Giorni
            return f"{parts[0]}, {parts[1]} e {parts[2]}"

    except Exception:
        return "N/A"

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
        padding: 10px; 
        font-size: 14px; /* --- Carattere leggermente più grande --- */
        border-top: 1px solid #ccc;
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
    
    /* 3. Imposta il quadratino (quando SPUNTATO) a ROSA CHIARO */
    div[data-testid="stCheckbox"] input:checked + div {
        background-color: #FFB6C1 !important; /* Rosa Chiaro (sostituisce il rosso) */
        border-color: #E7A1B0 !important; /* Bordo rosa più scuro */
    }
    
    /* 4. Rende il segno di spunta NERO (visibile sul rosa chiaro) */
    div[data-testid="stCheckbox"] input:checked + div svg path {
        stroke: #000000 !important; /* Nero (era bianco) */
    }
    /* --- FINE MODIFICA CHECKBOX --- */


    /* Allinea il pulsante di rimozione ❌ */
    .st-emotion-cache-1cflm81 {
        padding-top: 29px;
    }
    </style>
    """, unsafe_allow_html=True)

# Titolo aggiornato senza "(BETA)"
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

    # --- MODIFICA: Layout a colonne per pulsante Info ---
    info_col1, info_col2 = st.columns([3, 1])
    with info_col1:
        is_raddoppio = st.checkbox("Raddoppio Termini")
    with info_col2:
        with st.popover("Info"):
            st.markdown("""
            Il raddoppio dei termini della prescrizione si applica ai seguenti reati:

            **1. Art. 157 c.p. comma 6**
            * Art. 375, c. 3, c.p. (Frode in processo penale e depistaggio, aggravato)
            * Art. 416, c.p. (finalizzato a reati di falso artt. 453, 454, 455, 460, 461, 490, 491, 493-bis)
            * Art. 416, c. 6, c.p. (finalizzato a reati contro la persona, artt. 600, 601, 602)
            * Art. 572 c.p. (Maltrattamenti contro familiari e conviventi)
            * Art. 589, c. 2 e 3, c.p. (Omicidio colposo aggravato, violazione norme circolazione stradale o sicurezza lavoro)
            * Art. 589-bis c.p. (Omicidio stradale)
            * Art. 590-bis c.p. (Lesioni personali stradali gravi o gravissime)
            * Art. 600 c.p. (Riduzione o mantenimento in schiavitù)
            * Art. 600-bis c.p. (Prostituzione minorile)
            * Art. 600-ter c.p. (Pornografia minorile)
            * Art. 600-quater c.p. (Detenzione di materiale pornografico)
            * Art. 600-quater.1 c.p. (Pornografia virtuale)
            * Art. 600-quinquies c.p. (Iniziative turistiche per sfruttamento prostituzione minorile)
            * Art. 601 c.p. (Tratta di persone)
            * Art. 602 c.p. (Acquisto e alienazione di schiavi)
            * Art. 609-bis c.p. (Violenza sessuale)
            * Art. 609-ter c.p. (Violenza sessuale aggravata)
            * Art. 609-quater c.p. (Atti sessuali con minorenne)
            * Art. 609-quinquies c.p. (Corruzione di minorenne)
            * Art. 609-octies c.p. (Violenza sessuale di gruppo)
            * Art. 609-undecies c.p. (Adescamento di minorenni)
            * Art. 612-bis c.p. (Atti persecutori)

            **2. Reati contro l'ambiente (Titolo VI-bis c.p.)**
            * Art. 452-bis c.p. (Inquinamento ambientale)
            * Art. 452-ter c.p. (Morte o lesioni come conseguenza)
            * Art. 452-quater c.p. (Disastro ambientale)
            * Art. 452-quinquies c.p. (Delitti colposi contro l'ambiente)
            * Art. 452-sexies c.p. (Traffico e abbandono di materiale ad alta radioattività)
            * Art. 452-septies c.p. (Impedimento del controllo)
            * Art. 452-terdecies c.p. (Omessa bonifica)

            **3. Reati di criminalità organizzata (Art. 51, c. 3-bis, c.p.p.)**
            * Art. 416-bis c.p. (Associazione di tipo mafioso)
            * Art. 416-ter c.p. (Scambio elettorale politico-mafioso)
            * Art. 630 c.p. (Sequestro di persona a scopo di estorsione)
            * Art. 416 c.p. (Associazione per delinquere) finalizzata a specifici delitti (es. immigrazione clandestina, contraffazione)
            * Art. 74 D.P.R. 309/90 (Associazione finalizzata al traffico di stupefacenti)
            * Art. 291-quater D.P.R. 43/73 (Associazione finalizzata al contrabbando di T.L.E.)
            * Art. 452-quaterdecies c.p. (Attività organizzate per il traffico illecito di rifiuti)
            * Delitti commessi con aggravante del metodo mafioso (Art. 416-bis.1 c.p.)

            **4. Reati con finalità di terrorismo (Art. 51, c. 3-quater, c.p.p.)**
            * Art. 270-bis c.p. (Associazioni con finalità di terrorismo)
            * Tutti i delitti commessi con l'aggravante della finalità di terrorismo (Art. 270-sexies c.p.)
            """)
    
    # --- FINE MODIFICA ---

    # --- Checkbox per Art. 63 c. 4 ---
    is_art_63 = st.checkbox("Concorso Aggravanti (Art. 63 c. 4)")
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
    elif "2/3" in cap_label: cap_val = 1.6666666667 # Manteniamo precisione
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


# --- LOGICA DI CALCOLO (MODIFICATA PER CALCOLO IBRIDO) ---
if st.button("CALCOLA PRESCRIZIONE", use_container_width=True, type="primary"):
    
    logs = []
    
    # --- CALCOLO IBRIDO: Mesi e Giorni (da decimali) ---
    
    # 1. Pena base (come float)
    pena_base_mesi_float = float((pena_anni * 12) + pena_mesi)
    logs.append(f"Pena edittale base: <b>{format_hybrid_time(pena_base_mesi_float)}</b> ({pena_base_mesi_float:.2f} mesi)")

    # 2. Aumento Recidiva (calcolo su float)
    if cap_val == 1.5:
        aumento_float = pena_base_mesi_float * 0.5
        pena_base_mesi_float += aumento_float
        logs.append(f"Aumento Recidiva (+1/2) su base: +{format_hybrid_time(aumento_float)} -> Nuova base: <b>{format_hybrid_time(pena_base_mesi_float)}</b>")
    elif 1.6 < cap_val < 1.7:
        aumento_float = pena_base_mesi_float * (2/3)
        pena_base_mesi_float += aumento_float
        logs.append(f"Aumento Recidiva (+2/3) su base: +{format_hybrid_time(aumento_float)} -> Nuova base: <b>{format_hybrid_time(pena_base_mesi_float)}</b>")
    elif cap_val == 2.0:
        aumento_float = pena_base_mesi_float
        pena_base_mesi_float += aumento_float
        logs.append(f"Aumento Abitualità (+100%) su base: +{format_hybrid_time(aumento_float)} -> Nuova base: <b>{format_hybrid_time(pena_base_mesi_float)}</b>")

    # --- Passo 2.5 per Art. 63 c. 4 ---
    if is_art_63:
        aumento_art_63_float = pena_base_mesi_float / 3.0
        pena_base_mesi_float += aumento_art_63_float
        logs.append(f"Aumento Concorso Agg. (Art. 63 c. 4): +1/3 (+{format_hybrid_time(aumento_art_63_float)}) -> Nuova base: <b>{format_hybrid_time(pena_base_mesi_float)}</b>")

    # 3. Tentativo (calcolo su float)
    if is_tentato:
        riduzione_float = pena_base_mesi_float / 3.0
        pena_base_mesi_float -= riduzione_float
        logs.append(f"Riduzione Tentativo (-1/3): -{format_hybrid_time(riduzione_float)} -> Nuova base: <b>{format_hybrid_time(pena_base_mesi_float)}</b>")

    # 4. Minimo Edittale (confronto float)
    term_ordinario_float = pena_base_mesi_float
    minimo_mesi_float = float(minimo_edittale * 12)
    
    if term_ordinario_float < minimo_mesi_float:
        term_ordinario_float = minimo_mesi_float
        logs.append(f"Tempo Minimo di Prescrizione ({minimo_edittale} anni): Termine portato a <b>{format_hybrid_time(term_ordinario_float)}</b>")
    
    # 5. Raddoppio (calcolo su float)
    if is_raddoppio:
        term_ordinario_float *= 2.0
        logs.append(f"Raddoppio Termini: <b>{format_hybrid_time(term_ordinario_float)}</b>")

    # 6. Sospensioni (calcolo in giorni interi)
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

    # --- CALCOLO DATE FINALI (IBRIDO) ---

    # 7. Prescrizione Ordinaria
    start_ord = data_interruzione if (has_interruzione and data_interruzione) else data_commissione
    
    # Separa mesi interi e giorni frazionari
    ord_mesi_int = math.floor(term_ordinario_float)
    ord_giorni_extra = math.floor((term_ordinario_float - ord_mesi_int) * 30)
    
    data_ord_base = start_ord + relativedelta(months=ord_mesi_int)
    # Somma i giorni frazionari ai giorni di sospensione
    data_ord_finale = data_ord_base + timedelta(days=(ord_giorni_extra + giorni_sosp))
    
    
    # 8. Prescrizione Massima
    term_max_float = term_ordinario_float * cap_val
    
    # Separa mesi interi e giorni frazionari
    max_mesi_int = math.floor(term_max_float)
    max_giorni_extra = math.floor((term_max_float - max_mesi_int) * 30)
    
    logs.append(f"Calcolo termine massimo (Art. 161): {format_hybrid_time(term_ordinario_float)} * {cap_val:.2f} ({cap_label}) = <b>{format_hybrid_time(term_max_float)}</b>")

    data_max_base = data_commissione + relativedelta(months=max_mesi_int)
    # Somma i giorni frazionari ai giorni di sospensione
    data_max_finale = data_max_base + timedelta(days=(max_giorni_extra + giorni_sosp))


    # --- Risultati ---
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
        <div class_name="box-massima">
            <span class="label-result">Prescrizione Massima</span>
            <span class="big-date">{data_max_finale.strftime('%d/%m/%Y')}</span>
            <small>(da {data_commissione.strftime('%d/%m/%Y')})</Ssmall>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🔍 Mostra passaggi dettagliati"):
        for log in logs:
            st.markdown(f"- {log}", unsafe_allow_html=True)

# --- Testo Footer aggiornato ---
st.markdown('<div class="footer-disclaimer">App realizzata con Gemini AI da Giampiero Borraccia (magistrato)</div>', unsafe_allow_html=True)