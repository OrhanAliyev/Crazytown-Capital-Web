import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- YAPILANDIRMA ---
st.set_page_config(page_title="Crazytown Capital", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# --- GİZLİLİK VE TASARIM CSS ---
st.markdown("""
    <style>
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer, .stDeployButton, [data-testid="stToolbar"] {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 0rem !important; padding-bottom: 2rem !important;}
        .stApp {background-color: #0b0c10; color: #c5c6c7; font-family: 'Inter', sans-serif;}
        .stTabs [data-baseweb="tab-list"] {gap: 20px; border-bottom: 1px solid #1f2833; padding-top: 10px;}
        .stTabs [data-baseweb="tab"] {height: 50px; color: #888; font-weight: 500; border: none;}
        .stTabs [data-baseweb="tab"]:hover {color: #66fcf1;}
        .stTabs [aria-selected="true"] {color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important;}
        .metric-container {background-color: #1f2833; border-radius: 8px; padding: 20px; text-align: center; border: 1px solid #2d3845; transition: transform 0.2s ease;}
        .metric-container:hover {transform: translateY(-2px); border-color: #66fcf1;}
        .metric-value {font-size: 2rem; font-weight: 700; color: #fff; margin-bottom: 5px;}
        .metric-label {font-size: 0.8rem; color: #8892b0; text-transform: uppercase; letter-spacing: 1.5px;}
        .pricing-card {background-color: #1f2833; border-radius: 12px; padding: 40px 20px; text-align: center; border: 1px solid #2d3845; height: 100%; transition: all 0.3s ease;}
        .pricing-card:hover {border-color: #66fcf1; transform: translateY(-5px);}
        .plan-name {color: #66fcf1; font-size: 1.1rem; font-weight: 700; letter-spacing: 2px; margin-bottom: 15px;}
        .plan-price {color: #fff; font-size: 2.5rem; font-weight: 700; margin-bottom: 30px;}
        .testimonial-card {background-color: #15161a; border-left: 3px solid #66fcf1; padding: 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;}
        .testimonial-text {font-style: italic; color: #e0e0e0; font-size: 0.95rem;}
        .testimonial-author {margin-top: 10px; color: #66fcf1; font-weight: bold; font-size: 0.85rem;}
        .promo-banner {background: linear-gradient(90deg, #1f2833 0%, #0b0c10 100%); border: 1px solid #66fcf1; color: #fff; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; font-weight: bold;}
        .custom-btn {display: inline-block; padding: 12px 30px; color: #0b0c10; background-color: #66fcf1; border-radius: 4px; text-decoration: none; font-weight: 600; width: 100%; text-align: center;}
        .custom-btn:hover {background-color: #45a29e; color: #fff;}
        .custom-btn-outline {background-color: transparent; border: 1px solid #66fcf1; color: #66fcf1;}
        .custom-btn-outline:hover {background-color: #66fcf1; color: #0b0c10;}
        .stDataFrame {border: 1px solid #2d3845;}
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- VERİ BAĞLANTISI ---
@st.cache_data(ttl=60)
def load_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Cloud Secrets Kullanımı (Local veya Cloud)
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        else:
            # Eğer secret yoksa boş dön (Hata vermesin)
            return pd.DataFrame()
            
        client = gspread.authorize(creds)
        sheet = client.open("Crazytown_Journal").sheet1
        data = sheet.get_all_records()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        if 'R_Kazanc' in df.columns:
            df['R_Kazanc'] = df['R_Kazanc'].astype(str).str.replace(',', '.')
            df['R_Kazanc'] = pd.to_numeric(df['R_Kazanc'], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

df = load_data()

# --- HEADER & TICKER ---
components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}, {"description": "USDT.D", "proName": "CRYPTOCAP:USDT.D"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": false, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)
st.write("")
st.markdown("<h1 style='text-align: center; font-size: 3rem; color: #FFFFFF;'>CRAZYTOWN CAPITAL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #66fcf1; margin-top: -15px; letter-spacing: 2px; font-size: 0.9rem;'>ALGORITHMIC TRADING SYSTEMS</p>", unsafe_allow_html=True)
st.write("")

tab1, tab2, tab3 = st.tabs(["PERFORMANCE", "MEMBERSHIP", "CONTACT"])

# --- TAB 1: DASHBOARD ---
with tab1:
    if df.empty:
        st.info("📡 Bağlantı kuruluyor veya veri yok. Lütfen bekleyin...")
    else:
        total = len(df); win = len(df[df['Sonuç'] == 'WIN']); rate = (win / total * 100) if total > 0 else 0
        net_r_total = df['R_Kazanc'].sum()
        pf = (df[df['R_Kazanc'] > 0]['R_Kazanc'].sum() / abs(df[df['R_Kazanc'] < 0]['R_Kazanc'].sum())) if abs(df[df['R_Kazanc'] < 0]['R_Kazanc'].sum()) > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-container"><div class="metric-value">{total}</div><div class="metric-label">TOTAL TRADES</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-container"><div class="metric-value">{rate:.1f}%</div><div class="metric-label">WIN RATE</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-container"><div class="metric-value" style="color:{"#66fcf1" if net_r_total>0 else "#ff4b4b"}">{net_r_total:.2f}R</div><div class="metric-label">NET RETURN</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-container"><div class="metric-value">{pf:.2f}</div><div class="metric-label">PROFIT FACTOR</div></div>', unsafe_allow_html=True)
        st.write("")

        g1, g2 = st.columns([2, 1])
        with g1:
            df['Cum'] = df['R_Kazanc'].cumsum()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Tarih'], y=df['Cum'], mode='lines', fill='tozeroy', line=dict(color='#66fcf1', width=2), fillcolor='rgba(102, 252, 241, 0.1)'))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), height=300, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#1f2833'))
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            fig_pie = px.pie(df, names='Sonuç', values=[1]*len(df), hole=0.7, color='Sonuç', color_discrete_map={'WIN':'#66fcf1', 'LOSS':'#ff4b4b'})
            fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(l=20, r=20, t=10, b=20), height=300, annotations=[dict(text=f"{rate:.0f}%", x=0.5, y=0.5, font_size=24, showarrow=False, font_color="white")])
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---"); st.subheader("📡 MARKET INTELLIGENCE")
        mi1, mi2 = st.columns(2)
        with mi1: components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>{"interval": "4h", "width": "100%", "isTransparent": true, "height": "400", "symbol": "BINANCE:BTCUSDT", "showIntervalTabs": true, "displayMode": "single", "locale": "en", "colorTheme": "dark"}</script></div>""", height=400)
        with mi2: components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"colorTheme": "dark", "isTransparent": true, "width": "100%", "height": "400", "locale": "en", "importanceFilter": "-1,0,1", "currencyFilter": "USD"}</script></div>""", height=400)

        st.markdown("---"); st.subheader("🧮 ROI SIMULATOR")
        roi1, roi2, roi3 = st.columns([1,1,2])
        with roi1: caps = st.number_input("Capital ($)", 100, 100000, 1000)
        with roi2: risk = st.slider("Risk (%)", 0.5, 5.0, 2.0)
        prof = caps * (risk/100) * net_r_total; bal = caps + prof
        with roi3: st.markdown(f"""<div style="background:#1f2833; padding:15px; border-radius:8px; border:1px solid #66fcf1; text-align:center;"><span style="color:#888;">PROJECTED BALANCE</span><br><span style="color:#fff; font-size:2.2rem; font-weight:bold;">${bal:,.2f}</span></div>""", unsafe_allow_html=True)
        
        st.markdown("---"); st.markdown("##### TRADE LOG")
        def style_df(row): return [f'color: {"#66fcf1" if row["Sonuç"]=="WIN" else "#ff4b4b"}; font-weight: bold' if col == "Sonuç" else 'color: #c5c6c7' for col in row.index]
        st.dataframe(df.style.apply(style_df, axis=1), use_container_width=True, hide_index=True)

# --- TAB 2: MEMBERSHIP ---
with tab2:
    st.write(""); st.markdown("""<div class="promo-banner">🔥 LIMITED TIME OFFER: Get LIFETIME access before price increase!</div>""", unsafe_allow_html=True)
    st.subheader("💬 TRADER FEEDBACK"); sp1, sp2, sp3 = st.columns(3)
    with sp1: st.markdown("""<div class="testimonial-card"><div class="testimonial-text">"Risk management is top tier."</div><div class="testimonial-author">@Crypto***</div></div>""", unsafe_allow_html=True)
    with sp2: st.markdown("""<div class="testimonial-card"><div class="testimonial-text">"Transparency sold me."</div><div class="testimonial-author">@Alex***</div></div>""", unsafe_allow_html=True)
    with sp3: st.markdown("""<div class="testimonial-card"><div class="testimonial-text">"FVG setups are insane."</div><div class="testimonial-author">@Mehmet***</div></div>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown("""<div class="pricing-card"><div class="plan-name">STARTER</div><div class="plan-price">$30<span style="font-size:1rem;color:#888">/mo</span></div><div class="feature-list">✓ Telegram Access<br>✓ 15m Setups<br>✓ FVG Targets</div><a href="https://t.me/Orhan1909" target="_blank" class="custom-btn custom-btn-outline">SELECT</a></div>""", unsafe_allow_html=True)
    with col2: st.markdown("""<div class="pricing-card" style="border-color:#66fcf1"><div class="plan-name">PROFESSIONAL</div><div class="plan-price">$75<span style="font-size:1rem;color:#888">/qtr</span></div><div class="feature-list">✓ <b>All Features</b><br>✓ Real-time Signals<br>✓ USDT.D Analysis</div><a href="https://t.me/Orhan1909" target="_blank" class="custom-btn">POPULAR</a></div>""", unsafe_allow_html=True)
    with col3: st.markdown("""<div class="pricing-card"><div class="plan-name">LIFETIME</div><div class="plan-price">$250<span style="font-size:1rem;color:#888">/once</span></div><div class="feature-list">✓ <b>Lifetime Access</b><br>✓ Bot Support<br>✓ Private Group</div><a href="https://t.me/Orhan1909" target="_blank" class="custom-btn custom-btn-outline">CONTACT</a></div>""", unsafe_allow_html=True)

# --- TAB 3: CONTACT ---
with tab3:
    st.write(""); c1, c2 = st.columns(2)
    with c1: st.markdown("""### 📨 Telegram<br><a href="https://t.me/Orhan1909" class="custom-btn">OPEN CHAT</a>""", unsafe_allow_html=True)
    with c2: st.markdown("""### 📧 Email<br><div style="background:#1f2833; padding:12px; border-radius:4px; text-align:center;">orhanaliyev02@gmail.com</div>""", unsafe_allow_html=True)
    st.divider(); st.subheader("❓ FAQ")
    with st.expander("How do I get access?"): st.write("Contact via Telegram after payment.")
    with st.expander("Is capital safe?"): st.write("Strict risk management used.")
    with st.expander("Can I cancel?"): st.write("Yes, anytime.")

st.markdown("---"); st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)