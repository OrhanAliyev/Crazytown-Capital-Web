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
# 1. AYARLAR VE TASARIM
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TASARIMI (V300) ---
st.markdown("""
    <style>
        /* TEMEL AYARLAR */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        
        /* ARKA PLAN VE RENKLER */
        .stApp {
            background-color: #0b0c10;
            background: radial-gradient(circle at center, #1f2833 0%, #0b0c10 100%);
            color: #c5c6c7; font-family: 'Inter', sans-serif;
        }

        /* ELMAS ANIMASYONU */
        .area { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; overflow: hidden; }
        .circles { position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: hidden; }
        .circles li {
            position: absolute; display: block; list-style: none; width: 20px; height: 20px;
            background: rgba(102, 252, 241, 0.1); animation: animate 25s linear infinite;
            bottom: -150px; border: 1px solid rgba(102, 252, 241, 0.3); transform: rotate(45deg);
        }
        .circles li:nth-child(1){ left: 25%; width: 80px; height: 80px; animation-delay: 0s; }
        .circles li:nth-child(2){ left: 10%; width: 20px; height: 20px; animation-delay: 2s; animation-duration: 12s; }
        .circles li:nth-child(3){ left: 70%; width: 20px; height: 20px; animation-delay: 4s; }
        @keyframes animate {
            0%{ transform: translateY(0) rotate(45deg); opacity: 0; }
            50%{ opacity: 0.5; }
            100%{ transform: translateY(-1000px) rotate(720deg); opacity: 0; }
        }

        /* KUTULAR VE KARTLAR */
        .glass-card {
            background: rgba(31, 40, 51, 0.85); backdrop-filter: blur(10px);
            border: 1px solid #66fcf1; border-radius: 12px; padding: 30px;
            margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            z-index: 2; position: relative;
        }
        
        .metric-container, .pricing-card {
            background: rgba(31, 40, 51, 0.85); backdrop-filter: blur(10px);
            border: 1px solid #2d3845; border-radius: 8px; padding: 20px;
            text-align: center; z-index: 2;
        }
        
        /* BUTONLAR VE INPUTLAR */
        .stButton button {
            background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: bold !important;
            border: none !important; border-radius: 4px !important; width: 100%;
        }
        .stTextInput input { background-color: #1f2833 !important; color: white !important; border: 1px solid #2d3845 !important; }
        
        /* HEADER */
        .hero-title { font-size: 3.5rem; font-weight: 800; text-align: center; color: #fff; text-shadow: 0 0 20px #66fcf1; margin-bottom: 10px; }
        .hero-sub { font-size: 1.2rem; text-align: center; color: #66fcf1; letter-spacing: 2px; margin-bottom: 40px; }
        
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Animasyon
st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 2. VERİTABANI BAĞLANTILARI
# ==========================================
@st.cache_resource
def get_google_sheet_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            return gspread.authorize(creds)
        return None
    except: return None

def load_trade_data():
    client = get_google_sheet_client()
    if not client: return pd.DataFrame()
    try:
        sheet = client.open("Crazytown_Journal").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if 'R_Kazanc' in df.columns:
            df['R_Kazanc'] = pd.to_numeric(df['R_Kazanc'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

# KULLANICI İŞLEMLERİ (Register/Login)
def register_user(username, password, name):
    client = get_google_sheet_client()
    if not client: return False
    try:
        sheet = client.open("Crazytown_Journal").worksheet("Users")
        # Kullanıcı var mı kontrol et
        users = sheet.get_all_records()
        for u in users:
            if u['Username'] == username:
                return "Exists"
        
        # Yoksa ekle
        sheet.append_row([username, password, name, "Free Member"])
        return "Success"
    except Exception as e:
        return str(e)

def login_user(username, password):
    client = get_google_sheet_client()
    if not client: return None
    try:
        sheet = client.open("Crazytown_Journal").worksheet("Users")
        users = sheet.get_all_records()
        for u in users:
            if str(u['Username']) == username and str(u['Password']) == password:
                return u # Kullanıcı bilgilerini döndür
        return None
    except: return None

# ==========================================
# 3. SAYFA YÖNETİMİ
# ==========================================
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_info' not in st.session_state: st.session_state['user_info'] = {}
if 'page' not in st.session_state: st.session_state['page'] = 'Home'

# Menü Fonksiyonu (Navigation)
def navigate_to(page): st.session_state['page'] = page

# --- SAYFA: HOME (LANDING PAGE) ---
def show_home():
    # Ticker Tape (Herkese Açık)
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}, {"description": "USDT.D", "proName": "CRYPTOCAP:USDT.D"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)
    
    st.markdown('<div class="hero-title">CRAZYTOWN CAPITAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">AI POWERED | INSTITUTIONAL | SECURE</div>', unsafe_allow_html=True)

    # Butonlar
    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2: 
        if st.button("🚀 LOGIN"): navigate_to("Login")
    with c4: 
        if st.button("💎 REGISTER"): navigate_to("Register")

    st.write("")
    
    # Tanıtım Bölümü
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="glass-card">
            <h3>🤖 AI Sniper Algorithms</h3>
            <p>Our bots scan the market 24/7. While you sleep, our algorithms catch the FVG and Fibonacci levels with extreme precision.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="glass-card">
            <h3>📊 Institutional Dashboard</h3>
            <p>Stop gambling. Start trading with data. Access our proprietary dashboard to see Win Rates, Profit Factor, and Live Signals.</p>
        </div>
        """, unsafe_allow_html=True)

    # Fiyatlar
    st.subheader("CHOOSE YOUR PATH")
    pc1, pc2, pc3 = st.columns(3)
    with pc1: st.markdown("""<div class="pricing-card"><h3>STARTER</h3><h1>$30</h1><p>/month</p></div>""", unsafe_allow_html=True)
    with pc2: st.markdown("""<div class="pricing-card" style="border-color:#66fcf1"><h3>PROFESSIONAL</h3><h1>$75</h1><p>/quarter</p></div>""", unsafe_allow_html=True)
    with pc3: st.markdown("""<div class="pricing-card"><h3>LIFETIME</h3><h1>$250</h1><p>one-time</p></div>""", unsafe_allow_html=True)

# --- SAYFA: REGISTER ---
def show_register():
    st.markdown('<div class="hero-title" style="font-size:2rem;">JOIN THE ELITE</div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.form("reg_form"):
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            new_name = st.text_input("Full Name")
            submitted = st.form_submit_button("CREATE ACCOUNT")
            
            if submitted:
                if new_user and new_pass:
                    result = register_user(new_user, new_pass, new_name)
                    if result == "Success":
                        st.success("Account created successfully! Please Login.")
                        time.sleep(1)
                        navigate_to("Login")
                        st.rerun()
                    elif result == "Exists":
                        st.error("Username already taken.")
                    else:
                        st.error(f"Error: {result}")
                else:
                    st.warning("Please fill all fields.")
        
        if st.button("Back to Home"): navigate_to("Home")

# --- SAYFA: LOGIN ---
def show_login():
    st.markdown('<div class="hero-title" style="font-size:2rem;">MEMBER ACCESS</div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.form("login_form"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            submitted = st.form_submit_button("ENTER SYSTEM")
            
            if submitted:
                # Admin bypass
                if user == "admin" and pwd == "password123":
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = {"Name": "Orhan Aliyev", "Plan": "ADMIN"}
                    st.rerun()
                
                # Google Sheet kontrolü
                u_data = login_user(user, pwd)
                if u_data:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = u_data
                    st.success(f"Welcome back, {u_data['Name']}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        
        if st.button("Back to Home"): navigate_to("Home")

# --- SAYFA: DASHBOARD (PRIVATE) ---
def show_dashboard():
    df = load_trade_data()
    u_info = st.session_state['user_info']
    
    # Üst Menü
    c1, c2 = st.columns([3,1])
    with c1: st.markdown(f"**Welcome, {u_info.get('Name', 'Trader')}** | Plan: {u_info.get('Plan', 'Free')}")
    with c2: 
        if st.button("LOGOUT"): 
            st.session_state['logged_in'] = False
            st.session_state['page'] = 'Home'
            st.rerun()
            
    # --- DASHBOARD İÇERİĞİ (V201'den) ---
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    if df.empty:
        st.info("Waiting for data...")
    else:
        # KPI
        total = len(df); win = len(df[df['Sonuç'] == 'WIN']); rate = (win / total * 100) if total > 0 else 0
        net_r = df['R_Kazanc'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-container"><h1>{total}</h1><p>TRADES</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-container"><h1>{rate:.1f}%</h1><p>WIN RATE</p></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-container"><h1>{net_r:.2f}R</h1><p>NET RETURN</p></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-container"><h1>V10.2</h1><p>AI MODEL</p></div>', unsafe_allow_html=True)
        
        st.write("")
        g1, g2 = st.columns([2,1])
        with g1:
            df['Cum'] = df['R_Kazanc'].cumsum()
            fig = go.Figure(go.Scatter(x=df['Tarih'], y=df['Cum'], mode='lines', fill='tozeroy', line=dict(color='#66fcf1')))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.markdown("### 📡 ACTIVE SIGNALS")
            st.info("BTC/USDT - LONG (Entry: 98,500)")
            st.warning("ETH/USDT - WATCH")

# ==========================================
# 4. YÖNLENDİRME MERKEZİ
# ==========================================
if st.session_state['logged_in']:
    show_dashboard()
else:
    if st.session_state['page'] == 'Home': show_home()
    elif st.session_state['page'] == 'Login': show_login()
    elif st.session_state['page'] == 'Register': show_register()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
