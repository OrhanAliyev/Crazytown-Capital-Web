import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random

# ==========================================
# 1. AYARLAR VE CSS (DÜZELTİLMİŞ)
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS: İÇERİK ÖNDE, ELMASLAR ARKADA ---
st.markdown("""
    <style>
        /* GİZLİLİK */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer, .stDeployButton, [data-testid="stToolbar"] {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 0rem !important; padding-bottom: 2rem !important; z-index: 2; position: relative;}

        /* ARKA PLAN */
        .stApp {
            background: #0b0c10;
            background: linear-gradient(to bottom, #1f2833, #0b0c10);
            color: #c5c6c7;
            font-family: 'Inter', sans-serif;
        }

        /* ELMAS ANIMASYONU (SADECE ARKA PLAN) */
        .area {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0; /* En altta kalsın */
            overflow: hidden;
            pointer-events: none; /* Tıklamayı engelleme */
        }
        .circles {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }
        .circles li {
            position: absolute;
            display: block;
            list-style: none;
            width: 20px;
            height: 20px;
            background: rgba(102, 252, 241, 0.15); /* Hafif görünür */
            animation: animate 25s linear infinite;
            bottom: -150px;
            border: 1px solid rgba(102, 252, 241, 0.3);
            transform: rotate(45deg); /* Kareyi elmas yap */
        }
        .circles li:nth-child(1){ left: 25%; width: 80px; height: 80px; animation-delay: 0s; }
        .circles li:nth-child(2){ left: 10%; width: 20px; height: 20px; animation-delay: 2s; animation-duration: 12s; }
        .circles li:nth-child(3){ left: 70%; width: 20px; height: 20px; animation-delay: 4s; }
        .circles li:nth-child(4){ left: 40%; width: 60px; height: 60px; animation-delay: 0s; animation-duration: 18s; }
        .circles li:nth-child(5){ left: 65%; width: 20px; height: 20px; animation-delay: 0s; }
        .circles li:nth-child(6){ left: 75%; width: 110px; height: 110px; animation-delay: 3s; }
        .circles li:nth-child(7){ left: 35%; width: 150px; height: 150px; animation-delay: 7s; }
        .circles li:nth-child(8){ left: 50%; width: 25px; height: 25px; animation-delay: 15s; animation-duration: 45s; }
        .circles li:nth-child(9){ left: 20%; width: 15px; height: 15px; animation-delay: 2s; animation-duration: 35s; }
        .circles li:nth-child(10){ left: 85%; width: 150px; height: 150px; animation-delay: 0s; animation-duration: 11s; }

        @keyframes animate {
            0%{ transform: translateY(0) rotate(45deg); opacity: 0; border-radius: 0; }
            50%{ opacity: 0.5; }
            100%{ transform: translateY(-1000px) rotate(720deg); opacity: 0; border-radius: 20%; }
        }

        /* KART TASARIMLARI (CAM EFEKTİ İLE) */
        .metric-container, .pricing-card, .status-bar, .promo-banner {
            background: rgba(31, 40, 51, 0.85) !important; /* Arkası hafif görünsün */
            backdrop-filter: blur(5px);
            border: 1px solid #2d3845;
            border-radius: 8px;
            z-index: 2; /* Yazılar önde */
        }
        .status-bar {display: flex; gap: 15px; justify-content: center; margin-bottom: 10px; padding: 8px; color: #66fcf1; font-size: 0.8rem;}
        .status-dot {height: 8px; width: 8px; background-color: #00ff00; border-radius: 50%; display: inline-block; margin-right: 5px; box-shadow: 0 0 5px #00ff00;}
        .metric-container {padding: 20px; text-align: center; transition: transform 0.2s ease;}
        .metric-container:hover {transform: translateY(-2px); border-color: #66fcf1;}
        .metric-value {font-size: 2rem; font-weight: 700; color: #fff;}
        .metric-label {font-size: 0.8rem; color: #8892b0; letter-spacing: 1.5px;}
        .pricing-card {padding: 40px 20px; text-align: center; height: 100%;}
        .pricing-card:hover {border-color: #66fcf1; transform: translateY(-5px);}
        .plan-name {color: #66fcf1; font-size: 1.1rem; font-weight: 700; letter-spacing: 2px; margin-bottom: 15px;}
        .plan-price {color: #fff; font-size: 2.5rem; font-weight: 700; margin-bottom: 30px;}
        .feature-list {text-align: left; margin-left: 10%; color: #c5c6c7; font-size: 0.9rem; line-height: 2.2; margin-bottom: 30px;}
        .custom-btn {display: inline-block; padding: 12px 30px; color: #0b0c10; background-color: #66fcf1; border-radius: 4px; text-decoration: none; font-weight: 600; width: 100%; text-align: center;}
        .custom-btn:hover {background-color: #45a29e; color: #fff;}
        .custom-btn-outline {background-color: transparent; border: 1px solid #66fcf1; color: #66fcf1;}
        .custom-btn-outline:hover {background-color: #66fcf1; color: #0b0c10;}
        .stTabs [data-baseweb="tab-list"] {gap: 20px; border-bottom: 1px solid #1f2833;}
        .stTabs [data-baseweb="tab"] {height: 50px; color: #888; font-weight: 500; border: none;}
        .stTabs [aria-selected="true"] {color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important;}
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- ARKA PLAN HTML (ELMASLAR) ---
st.markdown("""
    <div class="area">
        <ul class="circles">
            <li></li><li></li><li></li><li></li><li></li>
            <li></li><li></li><li></li><li></li><li></li>
        </ul>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 2. VERİ BAĞLANTISI (HATA KORUMALI)
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        else: return pd.DataFrame()
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

# ==========================================
# 3. İÇERİK (HEADER & DASHBOARD)
# ==========================================

# Sistem Durumu (Status Bar)
latency = random.randint(12, 45)
st.markdown(f"""
<div class="status-bar">
    <span><span class="status-dot"></span>SYSTEM: <b>ONLINE</b></span>
    <span>|</span>
    <span>LATENCY: <b>{latency}ms</b></span>
    <span>|</span>
    <span>AI MODEL: <b>V10.2 (Sniper)</b></span>
</div>
""", unsafe_allow_html=True)

# Ticker Tape (Borsa Şeridi)
components.html("""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {
  "symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}, {"description": "USDT.D", "proName": "CRYPTOCAP:USDT.D"}],
  "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"
}
  </script>
</div>
""", height=50)

st.write("")
st.markdown("<h1 style='text-align: center; font-size: 3rem; color: #FFFFFF; text-shadow: 0 0 10px #66fcf1; z-index: 5;'>CRAZYTOWN CAPITAL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #66fcf1; margin-top: -15px; letter-spacing: 2px; font-size: 0.9rem; z-index: 5;'>INSTITUTIONAL GRADE ALGORITHMS</p>", unsafe_allow_html=True)
st.write("")

tab1, tab2, tab3 = st.tabs(["DASHBOARD & INTEL", "MEMBERSHIP", "TOOLS & CONTACT"])

# --- TAB 1: DASHBOARD ---
with tab1:
    if df.empty:
        st.info("📡 Connecting to secure servers...")
    else:
        # KPI Hesapları
        total = len(df)
        win = len(df[df['Sonuç'] == 'WIN'])
        rate = (win / total * 100) if total > 0 else 0
        net_r_total = df['R_Kazanc'].sum()
        pf = (df[df['R_Kazanc'] > 0]['R_Kazanc'].sum() / abs(df[df['R_Kazanc'] < 0]['R_Kazanc'].sum())) if abs(df[df['R_Kazanc'] < 0]['R_Kazanc'].sum()) > 0 else 0

        # KPI Kartları
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-container"><div class="metric-value">{total}</div><div class="metric-label">TOTAL TRADES</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-container"><div class="metric-value">{rate:.1f}%</div><div class="metric-label">WIN RATE</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-container"><div class="metric-value" style="color:{"#66fcf1" if net_r_total>0 else "#ff4b4b"}">{net_r_total:.2f}R</div><div class="metric-label">NET RETURN</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-container"><div class="metric-value">{pf:.2f}</div><div class="metric-label">PROFIT FACTOR</div></div>', unsafe_allow_html=True)
        
        st.write("")

        # Grafikler
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

        # Market Intel
        st.markdown("---")
        st.subheader("📡 MARKET INTELLIGENCE")
        mi1, mi2, mi3 = st.columns(3)
        with mi1: 
            st.markdown("##### TECHNICAL GAUGE")
            components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>{"interval": "4h", "width": "100%", "isTransparent": true, "height": "350", "symbol": "BINANCE:BTCUSDT", "showIntervalTabs": false, "displayMode": "single", "locale": "en", "colorTheme": "dark"}</script></div>""", height=350)
        with mi2:
            st.markdown("##### FEAR & GREED INDEX")
            components.html("""<img src="https://alternative.me/crypto/fear-and-greed-index.png" alt="Latest Crypto Fear & Greed Index" style="width:100%; border-radius:10px; border:1px solid #2d3845;" />""", height=350)
        with mi3:
            st.markdown("##### ECONOMIC CALENDAR")
            components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"colorTheme": "dark", "isTransparent": true, "width": "100%", "height": "350", "locale": "en", "importanceFilter": "-1,0,1", "currencyFilter": "USD"}</script></div>""", height=350)

        # Tablo
        st.markdown("---")
        st.markdown("##### LIVE TRADE LOG")
        def style_df(row):
            color = '#66fcf1' if row['Sonuç'] == 'WIN' else '#ff4b4b'
            return [f'color: {color}; font-weight: 600' if col == 'Sonuç' else 'color: #c5c6c7' for col in row.index]
        st.dataframe(df.style.apply(style_df, axis=1), use_container_width=True, hide_index=True)

# --- TAB 2: MEMBERSHIP ---
with tab2:
    st.write("")
    st.markdown("""<div class="promo-banner">🔥 LIMITED TIME OFFER: Get LIFETIME access before prices increase!</div>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <div class="plan-name">STARTER</div>
            <div class="plan-price">$30<span style="font-size:1rem;color:#888">/mo</span></div>
            <div class="feature-list">✓ Telegram Access<br>✓ 15m Setups<br>✓ FVG Targets</div>
            <a href="https://t.me/Orhan1909" target="_blank" class="custom-btn custom-btn-outline">SELECT</a>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="pricing-card" style="border-color:#66fcf1">
            <div class="plan-name">PROFESSIONAL</div>
            <div class="plan-price">$75<span style="font-size:1rem;color:#888">/qtr</span></div>
            <div class="feature-list">✓ <b>All Features</b><br>✓ Real-time Signals<br>✓ USDT.D Analysis</div>
            <a href="https://t.me/Orhan1909" target="_blank" class="custom-btn">POPULAR</a>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="pricing-card">
            <div class="plan-name">LIFETIME</div>
            <div class="plan-price">$250<span style="font-size:1rem;color:#888">/once</span></div>
            <div class="feature-list">✓ <b>Lifetime Access</b><br>✓ Bot Support<br>✓ Private Group</div>
            <a href="https://t.me/Orhan1909" target="_blank" class="custom-btn custom-btn-outline">CONTACT</a>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 3: TOOLS & CONTACT ---
with tab3:
    st.write("")
    st.subheader("🧮 TRADING CALCULATORS")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 💰 ROI SIMULATOR")
        caps = st.number_input("Capital ($)", 100, 100000, 1000)
        risk = st.slider("Risk (%)", 0.5, 5.0, 2.0)
        prof = caps * (risk/100) * (net_r_total if not df.empty else 0)
        st.markdown(f"""<div style="background:rgba(31,40,51,0.8); padding:10px; border-radius:5px; border:1px solid #333; text-align:center;">Potential Balance: <b style="color:#66fcf1">${caps+prof:,.2f}</b></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("##### ⚠️ RISK OF RUIN")
        st.markdown(f"""<div style="background:rgba(31,40,51,0.8); padding:10px; border-radius:5px; border:1px solid #333; text-align:center;">Risk of Ruin: <b style="color:#66fcf1">0.0000%</b></div>""", unsafe_allow_html=True)
    
    st.divider()
    
    co1, co2 = st.columns(2)
    with co1: st.markdown("""### 📨 Telegram<br><a href="https://t.me/Orhan1909" class="custom-btn">OPEN CHAT</a>""", unsafe_allow_html=True)
    with co2: st.markdown("""### 📧 Email<br><div style="background:#1f2833; padding:12px; border-radius:4px; text-align:center;">orhanaliyev02@gmail.com</div>""", unsafe_allow_html=True)
    
    st.write(""); st.subheader("❓ FAQ")
    with st.expander("How do I get access?"): st.write("Contact via Telegram after payment.")
    with st.expander("Is capital safe?"): st.write("Strict risk management used.")

st.markdown("---"); st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
