import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random
import time

# ==========================================
# 1. AYARLAR VE GİZLİLİK
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Portal",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS: PORTAL VE DÜZEN DÜZELTMESİ ---
st.markdown("""
    <style>
        /* 1. GİZLİLİK (FULL STEALTH) */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer, .stDeployButton, [data-testid="stToolbar"] {display: none !important;}
        .stApp > header {display: none !important;}
        
        /* 2. ANA YAPI DÜZELTMESİ */
        .block-container {
            padding-top: 1rem !important; 
            padding-bottom: 2rem !important; 
            max-width: 100% !important;
            z-index: 1; /* İçerik önde */
        }

        /* 3. ARKA PLAN VE RENKLER */
        .stApp {
            background-color: #0b0c10;
            background: radial-gradient(circle at center, #1f2833 0%, #0b0c10 100%);
            color: #c5c6c7;
            font-family: 'Inter', sans-serif;
        }

        /* 4. GİRİŞ KUTUSU (LOGIN BOX) - DÜZELTİLDİ */
        .login-container {
            background: rgba(31, 40, 51, 0.95);
            backdrop-filter: blur(15px);
            padding: 40px;
            border-radius: 12px;
            border: 1px solid #66fcf1;
            box-shadow: 0 0 30px rgba(102, 252, 241, 0.15);
            text-align: center;
            margin-top: 50px;
        }

        /* 5. ELMAS ANIMASYONU (SADECE ARKA PLAN) */
        .area {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
            z-index: 0; /* İçeriğin arkasında */
            pointer-events: none; overflow: hidden;
        }
        .circles { position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: hidden; }
        .circles li {
            position: absolute; display: block; list-style: none; width: 20px; height: 20px;
            background: rgba(102, 252, 241, 0.1); animation: animate 25s linear infinite;
            bottom: -150px; border: 1px solid rgba(102, 252, 241, 0.3); transform: rotate(45deg);
        }
        .circles li:nth-child(1){ left: 25%; width: 80px; height: 80px; animation-delay: 0s; }
        .circles li:nth-child(2){ left: 10%; width: 20px; height: 20px; animation-delay: 2s; animation-duration: 12s; }
        .circles li:nth-child(3){ left: 70%; width: 20px; height: 20px; animation-delay: 4s; }
        .circles li:nth-child(4){ left: 40%; width: 60px; height: 60px; animation-delay: 0s; animation-duration: 18s; }
        .circles li:nth-child(5){ left: 65%; width: 20px; height: 20px; animation-delay: 0s; }

        @keyframes animate {
            0%{ transform: translateY(0) rotate(45deg); opacity: 0; }
            50%{ opacity: 0.5; }
            100%{ transform: translateY(-1000px) rotate(720deg); opacity: 0; }
        }

        /* 6. KART VE TABLO TASARIMLARI */
        .metric-container, .pricing-card, .status-bar, .promo-banner, .vip-card {
            background: rgba(31, 40, 51, 0.85) !important; 
            backdrop-filter: blur(10px);
            border: 1px solid #2d3845; border-radius: 8px; 
            z-index: 2; /* En önde */
        }
        .status-bar { display: flex; gap: 15px; justify-content: center; margin-bottom: 10px; padding: 8px; color: #66fcf1; font-size: 0.8rem; }
        .status-dot {height: 8px; width: 8px; background-color: #00ff00; border-radius: 50%; display: inline-block; margin-right: 5px; box-shadow: 0 0 5px #00ff00;}
        .metric-value { font-size: 2rem; font-weight: 700; color: #fff; }
        
        /* BUTONLAR */
        .stButton button {
            background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: bold !important;
            border: none !important; border-radius: 4px !important; width: 100% !important;
        }
        .stButton button:hover { background-color: #45a29e !important; color: #fff !important; }
        
        .custom-btn { display: inline-block; padding: 12px 30px; background-color: #66fcf1; color: #0b0c10; border-radius: 4px; text-decoration: none; font-weight: 600; width: 100%; text-align: center; }
        .stTextInput input { background-color: #1f2833 !important; color: white !important; border: 1px solid #2d3845 !important; }
        
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- ARKA PLAN ANIMASYONU ---
st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 2. VERİ VE OTURUM
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {}

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

# ==========================================
# 3. GİRİŞ SAYFASI (LOGIN PAGE)
# ==========================================
def login_page():
    # Sayfayı ortalamak için boş kolonlar
    c1, c2, c3 = st.columns([1, 1, 1])
    
    with c2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: #fff; font-size: 3rem; text-shadow: 0 0 15px #66fcf1; margin-bottom:0;">CRAZYTOWN</h1>
            <p style="color: #66fcf1; letter-spacing: 4px; font-size: 0.9rem;">ACCESS CONTROL SYSTEM</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Giriş Formu (CSS ile stilize edilmiş kutu)
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("<h3 style='color:#fff; text-align:center;'>MEMBER LOGIN</h3>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            st.write("")
            submitted = st.form_submit_button("SECURE LOGIN ➜")
            
            if submitted:
                if username == "admin" and password == "password123":
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = {"name": "Orhan Aliyev", "plan": "LIFETIME ADMIN"}
                    st.success("Access Granted.")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Access Denied.")
        st.markdown('</div>', unsafe_allow_html=True)

        # VIP Sorgulama
        st.markdown("<br><p style='text-align:center; color:#66fcf1;'>--- OR ---</p>", unsafe_allow_html=True)
        with st.expander("🔍 CHECK VIP STATUS (No Login Required)"):
            email_check = st.text_input("Enter Email / ID")
            if st.button("CHECK STATUS"):
                if "admin" in email_check or "orhan" in email_check:
                    st.success("✅ ACTIVE MEMBER: LIFETIME PRO PLAN")
                else:
                    st.error("❌ NO ACTIVE SUBSCRIPTION FOUND")

# ==========================================
# 4. ANA DASHBOARD (MAIN APP)
# ==========================================
def main_dashboard():
    df = load_data()
    u_info = st.session_state['user_info']
    
    # Üst Bilgi Barı (Profil)
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(31,40,51,0.6); padding:10px 20px; border-radius:8px; border-bottom:1px solid #66fcf1; margin-bottom:15px;">
        <div style="color:#66fcf1; font-weight:bold; font-size:0.9rem;">🟢 SYSTEM: ONLINE</div>
        <div style="text-align:right;">
            <span style="color:#fff; font-weight:bold;">{u_info.get('name', 'User')}</span>
            <span style="color:#888; margin:0 10px;">|</span>
            <span style="color:#00ff00; font-size:0.8rem; border:1px solid #00ff00; padding:2px 6px; border-radius:4px;">{u_info.get('plan', 'Member')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Ticker Tape
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}, {"description": "USDT.D", "proName": "CRYPTOCAP:USDT.D"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    st.write("")
    st.markdown("<h1 style='text-align: center; font-size: 3rem; color: #FFFFFF; text-shadow: 0 0 15px #66fcf1;'>CRAZYTOWN CAPITAL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #66fcf1; margin-top: -15px; letter-spacing: 2px; font-size: 0.9rem;'>INSTITUTIONAL GRADE ALGORITHMS</p>", unsafe_allow_html=True)
    st.write("")

    tab1, tab2, tab3 = st.tabs(["DASHBOARD", "MEMBERSHIP", "SETTINGS"])

    # --- TAB 1: DASHBOARD ---
    with tab1:
        if df.empty:
            st.info("📡 Connecting...")
        else:
            total = len(df); win = len(df[df['Sonuç'] == 'WIN']); rate = (win / total * 100) if total > 0 else 0
            net_r = df['R_Kazanc'].sum()
            pf = (df[df['R_Kazanc'] > 0]['R_Kazanc'].sum() / abs(df[df['R_Kazanc'] < 0]['R_Kazanc'].sum())) if abs(df[df['R_Kazanc'] < 0]['R_Kazanc'].sum()) > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-container"><div class="metric-value">{total}</div><div>TOTAL TRADES</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-container"><div class="metric-value">{rate:.1f}%</div><div>WIN RATE</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-container"><div class="metric-value" style="color:{"#66fcf1" if net_r>0 else "#ff4b4b"}">{net_r:.2f}R</div><div>NET RETURN</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-container"><div class="metric-value">{pf:.2f}</div><div>PROFIT FACTOR</div></div>', unsafe_allow_html=True)
            st.write("")

            g1, g2 = st.columns([2, 1])
            with g1:
                df['Cum'] = df['R_Kazanc'].cumsum()
                fig = go.Figure(go.Scatter(x=df['Tarih'], y=df['Cum'], mode='lines', fill='tozeroy', line=dict(color='#66fcf1')))
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=10,b=0), height=300)
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig_pie = px.pie(df, names='Sonuç', values=[1]*len(df), hole=0.7, color='Sonuç', color_discrete_map={'WIN':'#66fcf1', 'LOSS':'#ff4b4b'})
                fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(l=20,r=20,t=10,b=20), height=300)
                st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("---")
            mi1, mi2, mi3 = st.columns(3)
            with mi1: st.markdown("##### GAUGE"); components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>{"interval": "4h", "width": "100%", "isTransparent": true, "height": "350", "symbol": "BINANCE:BTCUSDT", "showIntervalTabs": false, "displayMode": "single", "locale": "en", "colorTheme": "dark"}</script></div>""", height=350)
            with mi2: st.markdown("##### FEAR & GREED"); components.html("""<img src="https://alternative.me/crypto/fear-and-greed-index.png" style="width:100%; border-radius:10px;" />""", height=350)
            with mi3: st.markdown("##### CALENDAR"); components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"colorTheme": "dark", "isTransparent": true, "width": "100%", "height": "350", "locale": "en", "importanceFilter": "-1,0,1", "currencyFilter": "USD"}</script></div>""", height=350)

            st.markdown("---"); st.markdown("##### LIVE LOG")
            def style_df(row): return [f'color: {"#66fcf1" if row["Sonuç"]=="WIN" else "#ff4b4b"}; font-weight: bold' if col == "Sonuç" else 'color: #c5c6c7' for col in row.index]
            st.dataframe(df.style.apply(style_df, axis=1), use_container_width=True, hide_index=True)

    # --- TAB 2: MEMBERSHIP ---
    with tab2:
        st.markdown("""<div class="promo-banner">🔥 LIMITED OFFER: LIFETIME ACCESS</div>""", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown("""<div class="pricing-card"><div class="plan-name">STARTER</div><div class="plan-price">$30</div><a href="https://t.me/Orhan1909" class="custom-btn">SELECT</a></div>""", unsafe_allow_html=True)
        with col2: st.markdown("""<div class="pricing-card" style="border-color:#66fcf1"><div class="plan-name">PRO</div><div class="plan-price">$75</div><a href="https://t.me/Orhan1909" class="custom-btn">POPULAR</a></div>""", unsafe_allow_html=True)
        with col3: st.markdown("""<div class="pricing-card"><div class="plan-name">LIFETIME</div><div class="plan-price">$250</div><a href="https://t.me/Orhan1909" class="custom-btn">CONTACT</a></div>""", unsafe_allow_html=True)

    # --- TAB 3: SETTINGS ---
    with tab3:
        st.subheader("⚙️ ACCOUNT")
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"User: {u_info.get('name')}\n\nStatus: Active")
            if st.button("🔒 LOGOUT", type="primary"):
                st.session_state['logged_in'] = False
                st.rerun()
        with c2:
            st.markdown("##### HELP & SUPPORT")
            st.markdown("Contact: **orhanaliyev02@gmail.com**")
            st.markdown("Telegram: **@Orhan1909**")

# ==========================================
# 5. UYGULAMA AKIŞI
# ==========================================
if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
