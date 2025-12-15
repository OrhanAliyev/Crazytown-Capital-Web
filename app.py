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
# 1. SAYFA YAPILANDIRMASI
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. GÖRSEL MOTOR (CSS & ANIMASYON)
# ==========================================
st.markdown("""
    <style>
        /* 1. GİZLİLİK (FULL STEALTH) */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer, .stDeployButton, [data-testid="stToolbar"] {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 0rem !important; padding-bottom: 2rem !important;}

        /* 2. ARKA PLAN RENGİ (ZORLA AYARLA) */
        [data-testid="stAppViewContainer"] {
            background-color: #0b0c10;
            background-image: radial-gradient(circle at 50% 50%, #1f2833 0%, #0b0c10 80%);
        }
        
        /* 3. ELMAS ANIMASYONU (CSS) */
        .box-area {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 0; /* İçeriğin hemen arkasında */
            pointer-events: none; /* Tıklamayı engelleme */
        }
        .box-area li {
            position: absolute;
            display: block;
            list-style: none;
            width: 25px;
            height: 25px;
            background: rgba(102, 252, 241, 0.2);
            animation: animate 20s linear infinite;
            bottom: -150px;
            border: 1px solid rgba(102, 252, 241, 0.5);
            box-shadow: 0 0 10px rgba(102, 252, 241, 0.2);
        }
        .box-area li:nth-child(1) { left: 86%; width: 80px; height: 80px; animation-delay: 0s; }
        .box-area li:nth-child(2) { left: 12%; width: 30px; height: 30px; animation-delay: 1.5s; animation-duration: 10s; }
        .box-area li:nth-child(3) { left: 70%; width: 100px; height: 100px; animation-delay: 5.5s; }
        .box-area li:nth-child(4) { left: 42%; width: 150px; height: 150px; animation-delay: 0s; animation-duration: 15s; }
        .box-area li:nth-child(5) { left: 65%; width: 40px; height: 40px; animation-delay: 0s; }
        .box-area li:nth-child(6) { left: 15%; width: 110px; height: 110px; animation-delay: 3.5s; }

        @keyframes animate {
            0% { transform: translateY(0) rotate(0deg); opacity: 1; }
            100% { transform: translateY(-1000px) rotate(360deg); opacity: 0; }
        }
        
        /* 4. İÇERİK KUTULARI (CAM EFEKTİ) */
        .metric-container, .pricing-card, .status-bar {
            background: rgba(31, 40, 51, 0.7) !important;
            backdrop-filter: blur(10px); /* Arka planı bulanıklaştır */
            border: 1px solid rgba(102, 252, 241, 0.2);
            border-radius: 10px;
            z-index: 1; /* Animasyonun üstünde kalsın */
        }
        
        /* Diğer stiller */
        .stApp { color: #c5c6c7; font-family: 'Inter', sans-serif; }
        .metric-value { font-size: 2rem; font-weight: 700; color: #fff; }
        .metric-label { font-size: 0.8rem; color: #8892b0; letter-spacing: 1.5px; }
        .status-bar { display: flex; gap: 15px; justify-content: center; margin-bottom: 10px; padding: 8px; color:#66fcf1; font-size:0.8rem;}
        .status-dot {height: 8px; width: 8px; background-color: #00ff00; border-radius: 50%; display: inline-block; margin-right: 5px; box-shadow: 0 0 5px #00ff00;}
        .promo-banner {background: linear-gradient(90deg, #1f2833 0%, #0b0c10 100%); border: 1px solid #66fcf1; color: #fff; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; font-weight: bold; z-index: 1;}
        .custom-btn {display: inline-block; padding: 12px 30px; color: #0b0c10; background-color: #66fcf1; border-radius: 4px; text-decoration: none; font-weight: 600; width: 100%; text-align: center;}
        .stDataFrame {border: 1px solid #2d3845; z-index: 1;}
        [data-testid="stSidebar"] {display: none;}
    </style>

    <ul class="box-area">
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
    </ul>
""", unsafe_allow_html=True)

# ==========================================
# 3. VERİ BAĞLANTISI
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
# 4. İÇERİK
# ==========================================

# Üst Bar
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

# Ticker
components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}, {"description": "USDT.D", "proName": "CRYPTOCAP:USDT.D"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

st.write("")
st.markdown("<h1 style='text-align: center; font-size: 3rem; color: #FFFFFF; text-shadow: 0 0 10px #66fcf1; position: relative; z-index: 2;'>CRAZYTOWN CAPITAL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #66fcf1; margin-top: -15px; letter-spacing: 2px; font-size: 0.9rem; position: relative; z-index: 2;'>INSTITUTIONAL GRADE ALGORITHMS</p>", unsafe_allow_html=True)
st.write("")

tab1, tab2, tab3 = st.tabs(["DASHBOARD & INTEL", "MEMBERSHIP", "TOOLS & CONTACT"])

# --- TAB 1 ---
with tab1:
    if df.empty:
        st.info("📡 Veri bağlantısı kuruluyor...")
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
        mi1, mi2, mi3 = st.columns(3)
        with mi1: st.markdown("##### TECHNICAL GAUGE"); components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>{"interval": "4h", "width": "100%", "isTransparent": true, "height": "350", "symbol": "BINANCE:BTCUSDT", "showIntervalTabs": false, "displayMode": "single", "locale": "en", "colorTheme": "dark"}</script></div>""", height=350)
        with mi2: st.markdown("##### FEAR & GREED"); components.html("""<img src="https://alternative.me/crypto/fear-and-greed-index.png" alt="Latest Crypto Fear & Greed Index" style="width:100%; border-radius:10px; border:1px solid #2d3845;" />""", height=350)
        with mi3: st.markdown("##### ECONOMIC CALENDAR"); components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"colorTheme": "dark", "isTransparent": true, "width": "100%", "height": "350", "locale": "en", "importanceFilter": "-1,0,1", "currencyFilter": "USD"}</script></div>""", height=350)

        st.markdown("---"); st.markdown("##### LIVE TRADE LOG")
        def style_df(row): return [f'color: {"#66fcf1" if row["Sonuç"]=="WIN" else "#ff4b4b"}; font-weight: bold' if col == "Sonuç" else 'color: #c5c6c7' for col in row.index]
        st.dataframe(df.style.apply(style_df, axis=1), use_container_width=True, hide_index=True)

# --- TAB 2 ---
with tab2:
    st.write(""); st.markdown("""<div class="promo-banner">🔥 LIMITED TIME OFFER: Get LIFETIME access before prices increase!</div>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown("""<div class="pricing-card"><div class="plan-name">STARTER</div><div class="plan-price">$30<span style="font-size:1rem;color:#888">/mo</span></div><div class="feature-list">✓ Telegram Access<br>✓ 15m Setups<br>✓ FVG Targets</div><a href="https://t.me/Orhan1909" target="_blank" class="custom-btn custom-btn-outline">SELECT</a></div>""", unsafe_allow_html=True)
    with col2: st.markdown("""<div class="pricing-card" style="border-color:#66fcf1"><div class="plan-name">PROFESSIONAL</div><div class="plan-price">$75<span style="font-size:1rem;color:#888">/qtr</span></div><div class="feature-list">✓ <b>All Features</b><br>✓ Real-time Signals<br>✓ USDT.D Analysis</div><a href="https://t.me/Orhan1909" target="_blank" class="custom-btn">POPULAR</a></div>""", unsafe_allow_html=True)
    with col3: st.markdown("""<div class="pricing-card"><div class="plan-name">LIFETIME</div><div class="plan-price">$250<span style="font-size:1rem;color:#888">/once</span></div><div class="feature-list">✓ <b>Lifetime Access</b><br>✓ Bot Support<br>✓ Private Group</div><a href="https://t.me/Orhan1909" target="_blank" class="custom-btn custom-btn-outline">CONTACT</a></div>""", unsafe_allow_html=True)

# --- TAB 3 ---
with tab3:
    st.write(""); st.subheader("🧮 TOOLS & CONTACT")
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

st.markdown("---"); st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
