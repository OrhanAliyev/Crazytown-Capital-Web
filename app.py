import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import random

# ==========================================
# 1. AYARLAR VE TASARIM (EN ÖNEMLİ KISIM)
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS: V115 GÖRÜNÜMÜNÜ GERİ GETİRDİK ---
st.markdown("""
    <style>
        /* 1. TEMEL AYARLAR */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {
            padding-top: 1rem !important; 
            padding-bottom: 2rem !important; 
            max-width: 100% !important;
            z-index: 2; /* İçerik Önde */
            position: relative;
        }

        /* 2. ARKA PLAN (KOYU VE DERİN) */
        .stApp {
            background-color: #0b0c10;
            background: radial-gradient(circle at center, #1f2833 0%, #0b0c10 100%);
            color: #c5c6c7; font-family: 'Inter', sans-serif;
        }

        /* 3. ELMAS ANIMASYONU (ARKADA DÖNENLER) */
        .area { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; overflow: hidden; }
        .circles { position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: hidden; }
        .circles li {
            position: absolute; display: block; list-style: none; width: 20px; height: 20px;
            background: rgba(102, 252, 241, 0.15); animation: animate 25s linear infinite;
            bottom: -150px; border: 1px solid rgba(102, 252, 241, 0.3); transform: rotate(45deg);
        }
        .circles li:nth-child(1){ left: 25%; width: 80px; height: 80px; animation-delay: 0s; }
        .circles li:nth-child(2){ left: 10%; width: 20px; height: 20px; animation-delay: 2s; animation-duration: 12s; }
        .circles li:nth-child(3){ left: 70%; width: 20px; height: 20px; animation-delay: 4s; }
        .circles li:nth-child(4){ left: 40%; width: 60px; height: 60px; animation-delay: 0s; animation-duration: 18s; }
        .circles li:nth-child(5){ left: 65%; width: 20px; height: 20px; animation-delay: 0s; }
        .circles li:nth-child(6){ left: 75%; width: 110px; height: 110px; animation-delay: 3s; }
        .circles li:nth-child(7){ left: 35%; width: 150px; height: 150px; animation-delay: 7s; }
        .circles li:nth-child(8){ left: 50%; width: 25px; height: 25px; animation-delay: 15s; animation-duration: 45s; }
        
        @keyframes animate {
            0%{ transform: translateY(0) rotate(45deg); opacity: 0; }
            50%{ opacity: 0.5; }
            100%{ transform: translateY(-1000px) rotate(720deg); opacity: 0; }
        }

        /* 4. CAM KUTULAR (GLASSMORPHISM) */
        .glass-box, .metric-container, .pricing-card, .login-container {
            background: rgba(31, 40, 51, 0.85) !important;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(102, 252, 241, 0.3);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
        }
        
        /* GİRİŞ KUTUSU ÖZEL */
        .login-container {
            max-width: 400px;
            margin: 50px auto;
            border: 1px solid #66fcf1;
            box-shadow: 0 0 20px rgba(102, 252, 241, 0.2);
        }

        /* 5. METİNLER VE BAŞLIKLAR */
        .hero-title { font-size: 3.5rem; font-weight: 800; text-align: center; color: #fff; text-shadow: 0 0 20px #66fcf1; margin-bottom: 10px; }
        .hero-sub { font-size: 1.2rem; text-align: center; color: #66fcf1; letter-spacing: 3px; margin-bottom: 40px; }
        .metric-value { font-size: 2.5rem; font-weight: 700; color: #fff; text-shadow: 0 0 10px rgba(102,252,241,0.5); }
        .plan-price { font-size: 2.5rem; color: #fff; font-weight: 700; margin: 15px 0; }
        
        /* 6. INPUTLAR VE BUTONLAR */
        .stTextInput input {
            background-color: #15161a !important;
            color: #fff !important;
            border: 1px solid #2d3845 !important;
            border-radius: 5px !important;
        }
        .stButton button {
            background-color: #66fcf1 !important;
            color: #0b0c10 !important;
            font-weight: bold !important;
            border: none !important;
            border-radius: 5px !important;
            width: 100% !important;
            padding: 12px !important;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            background-color: #fff !important;
            box-shadow: 0 0 15px #66fcf1;
            transform: translateY(-2px);
        }

        /* 7. SEKME (TABS) TASARIMI */
        .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 1px solid #1f2833; }
        .stTabs [data-baseweb="tab"] { height: 50px; color: #888; font-weight: 500; border: none; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important; }
        
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Animasyonu Başlat
st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 2. GOOGLE SHEET & SİSTEM (OTOMATİK TAMİR)
# ==========================================
def get_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            return gspread.authorize(creds)
        return None
    except: return None

# Users sayfasını kontrol et/oluştur
def check_and_fix_users_sheet():
    client = get_client()
    if not client: return None
    try:
        sheet = client.open("Crazytown_Journal")
        try:
            return sheet.worksheet("Users")
        except:
            ws = sheet.add_worksheet(title="Users", rows="100", cols="4")
            ws.append_row(["Username", "Password", "Name", "Plan"])
            return ws
    except: return None

# İşlem verilerini çek
def load_trade_data():
    client = get_client()
    if not client: return pd.DataFrame()
    try:
        sheet = client.open("Crazytown_Journal").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if 'R_Kazanc' in df.columns:
            df['R_Kazanc'] = pd.to_numeric(df['R_Kazanc'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

# Üyelik İşlemleri
def register_user(username, password, name):
    ws = check_and_fix_users_sheet()
    if not ws: return "Connection Error"
    users = ws.get_all_records()
    for u in users:
        if str(u.get('Username')) == username: return "Exists"
    ws.append_row([username, password, name, "Free Member"])
    return "Success"

def login_user(username, password):
    ws = check_and_fix_users_sheet()
    if not ws: return None
    users = ws.get_all_records()
    for u in users:
        if str(u.get('Username')) == username and str(u.get('Password')) == password:
            return u
    return None

# ==========================================
# 3. SAYFA YÖNETİMİ
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'current_page' not in st.session_state: st.session_state.current_page = 'Home'

def go_to(page):
    st.session_state.current_page = page
    st.rerun()

# --- HOME PAGE (AÇILIŞ) ---
def show_home():
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    st.markdown('<div class="hero-title">CRAZYTOWN CAPITAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">AI POWERED | INSTITUTIONAL | SECURE</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2: 
        if st.button("🚀 MEMBER LOGIN"): go_to("Login")
    with c4: 
        if st.button("💎 JOIN NOW"): go_to("Register")

    st.write("")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="glass-box"><h3>🤖 AI Sniper Algorithms</h3><p>24/7 Market Scanning & Automated FVG Detection</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="glass-box"><h3>📊 Institutional Dashboard</h3><p>Real-time analytics, Win-Rate tracking & Risk Management</p></div>""", unsafe_allow_html=True)

    st.markdown("<br><h3 style='text-align:center; color:#fff;'>MEMBERSHIP PLANS</h3>", unsafe_allow_html=True)
    pc1, pc2, pc3 = st.columns(3)
    with pc1: st.markdown("""<div class="pricing-card"><h3>STARTER</h3><div class="plan-price">$30</div><p>/month</p></div>""", unsafe_allow_html=True)
    with pc2: st.markdown("""<div class="pricing-card" style="border:1px solid #66fcf1; box-shadow:0 0 15px rgba(102,252,241,0.2);"><h3>PRO</h3><div class="plan-price">$75</div><p>/quarter</p></div>""", unsafe_allow_html=True)
    with pc3: st.markdown("""<div class="pricing-card"><h3>LIFETIME</h3><div class="plan-price">$250</div><p>one-time</p></div>""", unsafe_allow_html=True)

# --- REGISTER PAGE ---
def show_register():
    st.markdown('<div class="hero-title" style="font-size:2.5rem;">JOIN THE ELITE</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("reg"):
        st.markdown("<h3 style='color:#fff;'>CREATE ACCOUNT</h3>", unsafe_allow_html=True)
        u = st.text_input("Choose Username")
        p = st.text_input("Choose Password", type="password")
        n = st.text_input("Full Name")
        if st.form_submit_button("REGISTER NOW"):
            if u and p:
                res = register_user(u, p, n)
                if res == "Success":
                    st.success("Account Created! Redirecting...")
                    time.sleep(2)
                    go_to("Login")
                elif res == "Exists": st.error("Username Taken!")
                else: st.error(f"Error: {res}")
            else: st.warning("Fill all fields")
    if st.button("Back Home"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- LOGIN PAGE ---
def show_login():
    st.markdown('<div class="hero-title" style="font-size:2.5rem;">SECURE LOGIN</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("log"):
        st.markdown("<h3 style='color:#fff;'>MEMBER ACCESS</h3>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("ENTER SYSTEM"):
            if u == "admin" and p == "password123":
                st.session_state.logged_in = True
                st.session_state.user_info = {"Name": "Orhan Aliyev", "Plan": "ADMIN"}
                st.rerun()
            
            ud = login_user(u, p)
            if ud:
                st.session_state.logged_in = True
                st.session_state.user_info = ud
                st.success("Access Granted")
                time.sleep(1)
                st.rerun()
            else: st.error("Invalid Credentials")
    if st.button("Back Home"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD (V115 GÖRÜNÜMÜ) ---
def show_dashboard():
    df = load_trade_data()
    ui = st.session_state.user_info
    
    # Top Bar
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(31,40,51,0.6); padding:10px 20px; border-radius:8px; border:1px solid #66fcf1; margin-bottom:15px;">
        <div style="color:#66fcf1; font-weight:bold;">🟢 SYSTEM ONLINE</div>
        <div style="text-align:right; color:#fff;">
            User: <b>{ui.get('Name')}</b> | Plan: <span style="color:#00ff00;">{ui.get('Plan')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    st.write("")
    if st.button("🔒 LOGOUT", key="logout_dash"):
        st.session_state.logged_in = False
        go_to("Home")

    tab1, tab2 = st.tabs(["DASHBOARD", "INTELLIGENCE"])
    
    with tab1:
        if df.empty:
            st.info("Awaiting data...")
        else:
            total = len(df); win = len(df[df['Sonuç'] == 'WIN']); rate = (win / total * 100) if total > 0 else 0
            net = df['R_Kazanc'].sum()
            pf = (df[df['R_Kazanc'] > 0]['R_Kazanc'].sum() / abs(df[df['R_Kazanc'] < 0]['R_Kazanc'].sum())) if abs(df[df['R_Kazanc'] < 0]['R_Kazanc'].sum()) > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-container"><div class="metric-value">{total}</div><div style="color:#888;">TRADES</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-container"><div class="metric-value">{rate:.1f}%</div><div style="color:#888;">WIN RATE</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-container"><div class="metric-value" style="color:{"#66fcf1" if net>0 else "#ff4b4b"}">{net:.2f}R</div><div style="color:#888;">NET RETURN</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-container"><div class="metric-value">{pf:.2f}</div><div style="color:#888;">PROFIT FACTOR</div></div>', unsafe_allow_html=True)
            
            st.write("")
            g1, g2 = st.columns([2,1])
            with g1:
                df['Cum'] = df['R_Kazanc'].cumsum()
                fig = go.Figure(go.Scatter(x=df['Tarih'], y=df['Cum'], mode='lines', fill='tozeroy', line=dict(color='#66fcf1', width=2)))
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig_pie = px.pie(df, names='Sonuç', values=[1]*len(df), hole=0.7, color='Sonuç', color_discrete_map={'WIN':'#66fcf1', 'LOSS':'#ff4b4b'})
                fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=300, margin=dict(l=20,r=20,t=10,b=20))
                st.plotly_chart(fig_pie, use_container_width=True)
            
            st.markdown("##### LIVE LOG")
            def style_df(row): return [f'color: {"#66fcf1" if row["Sonuç"]=="WIN" else "#ff4b4b"}; font-weight: bold' if col == "Sonuç" else 'color: #c5c6c7' for col in row.index]
            st.dataframe(df.style.apply(style_df, axis=1), use_container_width=True, hide_index=True)

    with tab2:
        mi1, mi2, mi3 = st.columns(3)
        with mi1: st.markdown("##### GAUGE"); components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>{"interval": "4h", "width": "100%", "isTransparent": true, "height": "350", "symbol": "BINANCE:BTCUSDT", "showIntervalTabs": false, "displayMode": "single", "locale": "en", "colorTheme": "dark"}</script></div>""", height=350)
        with mi2: st.markdown("##### FEAR & GREED"); components.html("""<img src="https://alternative.me/crypto/fear-and-greed-index.png" style="width:100%; border-radius:10px;" />""", height=350)
        with mi3: st.markdown("##### CALENDAR"); components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"colorTheme": "dark", "isTransparent": true, "width": "100%", "height": "350", "locale": "en", "importanceFilter": "-1,0,1", "currencyFilter": "USD"}</script></div>""", height=350)

# ==========================================
# 5. MAIN ROUTER
# ==========================================
if st.session_state.logged_in:
    show_dashboard()
else:
    if st.session_state.current_page == 'Home': show_home()
    elif st.session_state.current_page == 'Register': show_register()
    elif st.session_state.current_page == 'Login': show_login()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
