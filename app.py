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

# --- CSS (DÜZELTİLMİŞ) ---
st.markdown("""
    <style>
        /* TEMEL */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 100%;}
        
        /* ARKA PLAN */
        .stApp {
            background-color: #0b0c10;
            background: radial-gradient(circle at center, #1f2833 0%, #0b0c10 100%);
            color: #c5c6c7; font-family: 'Inter', sans-serif;
        }

        /* ELMAS ANIMASYONU (ARKADA) */
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

        /* İÇERİK KUTULARI (ÖNDE) */
        .glass-card, .metric-container, .pricing-card, .login-box {
            background: rgba(31, 40, 51, 0.9); backdrop-filter: blur(10px);
            border: 1px solid #2d3845; border-radius: 12px; padding: 20px;
            text-align: center; z-index: 2; margin-bottom: 20px;
        }
        .login-box { max-width: 400px; margin: 50px auto; border: 1px solid #66fcf1; }
        
        /* BUTONLAR */
        .stButton button {
            background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: bold !important;
            border: none !important; border-radius: 4px !important; width: 100%; transition: 0.3s;
        }
        .stButton button:hover { background-color: #fff !important; box-shadow: 0 0 10px #66fcf1; }
        
        /* HEADER */
        .hero-title { font-size: 3rem; font-weight: 800; text-align: center; color: #fff; text-shadow: 0 0 20px #66fcf1; margin-bottom: 10px; position: relative; z-index: 2; }
        
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 2. GOOGLE SHEET BAĞLANTISI (OTOMATİK TAMİR)
# ==========================================
def get_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            return gspread.authorize(creds)
        return None
    except Exception as e:
        st.error(f"Secret Error: {e}")
        return None

# Users sayfasını kontrol et ve yoksa oluştur
def check_and_fix_users_sheet():
    client = get_client()
    if not client: return None
    try:
        sheet = client.open("Crazytown_Journal")
        try:
            worksheet = sheet.worksheet("Users")
            return worksheet
        except:
            # Sayfa yoksa OTOMATİK OLUŞTUR
            worksheet = sheet.add_worksheet(title="Users", rows="100", cols="4")
            worksheet.append_row(["Username", "Password", "Name", "Plan"])
            return worksheet
    except Exception as e:
        st.error(f"Spreadsheet Error: {e}")
        return None

# İşlem verilerini çek
def load_trade_data():
    client = get_client()
    if not client: return pd.DataFrame()
    try:
        sheet = client.open("Crazytown_Journal").sheet1
        data = sheet.get_all_records()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        if 'R_Kazanc' in df.columns:
            df['R_Kazanc'] = pd.to_numeric(df['R_Kazanc'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

# ==========================================
# 3. KULLANICI İŞLEMLERİ
# ==========================================
def register_user(username, password, name):
    ws = check_and_fix_users_sheet()
    if not ws: return "Connection Error"
    
    users = ws.get_all_records()
    for u in users:
        if str(u.get('Username')) == username:
            return "Exists"
    
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
# 4. SAYFA YÖNETİMİ (SESSION STATE)
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'current_page' not in st.session_state: st.session_state.current_page = 'Home'

def go_to(page):
    st.session_state.current_page = page
    st.rerun()

# --- SAYFA: HOME ---
def show_home():
    # Ticker Tape
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}, {"description": "USDT.D", "proName": "CRYPTOCAP:USDT.D"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    st.markdown('<div class="hero-title">CRAZYTOWN CAPITAL</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#66fcf1; z-index:2; position:relative;">AI POWERED | INSTITUTIONAL | SECURE</p>', unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2:
        if st.button("🚀 LOGIN"): go_to("Login")
    with c4:
        if st.button("💎 REGISTER"): go_to("Register")

    st.write("")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="glass-card"><h3>🤖 AI Sniper</h3><p>24/7 Market Scanning & FVG Detection</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="glass-card"><h3>📊 Pro Dashboard</h3><p>Institutional grade analytics & reporting</p></div>""", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align:center; color:#fff; z-index:2; position:relative;'>MEMBERSHIP PLANS</h3>", unsafe_allow_html=True)
    pc1, pc2, pc3 = st.columns(3)
    with pc1: st.markdown("""<div class="pricing-card"><h3>STARTER</h3><h1>$30</h1></div>""", unsafe_allow_html=True)
    with pc2: st.markdown("""<div class="pricing-card" style="border:1px solid #66fcf1"><h3>PRO</h3><h1>$75</h1></div>""", unsafe_allow_html=True)
    with pc3: st.markdown("""<div class="pricing-card"><h3>LIFETIME</h3><h1>$250</h1></div>""", unsafe_allow_html=True)

# --- SAYFA: REGISTER ---
def show_register():
    st.markdown('<div class="hero-title" style="font-size:2rem;">BECOME A MEMBER</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    
    with st.form("reg_form"):
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")
        new_name = st.text_input("Full Name")
        sub = st.form_submit_button("CREATE ACCOUNT")
        
        if sub:
            if new_user and new_pass:
                res = register_user(new_user, new_pass, new_name)
                if res == "Success":
                    st.success("Account Created! Redirecting to Login...")
                    time.sleep(2)
                    go_to("Login")
                elif res == "Exists": st.error("Username taken!")
                else: st.error(f"Error: {res}")
            else: st.warning("Fill all fields")
    
    if st.button("Back"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- SAYFA: LOGIN ---
def show_login():
    st.markdown('<div class="hero-title" style="font-size:2rem;">MEMBER LOGIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    
    with st.form("login_form"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        sub = st.form_submit_button("ENTER DASHBOARD")
        
        if sub:
            # Admin Bypass
            if user == "admin" and pwd == "password123":
                st.session_state.logged_in = True
                st.session_state.user_info = {"Name": "Orhan Aliyev", "Plan": "ADMIN"}
                st.success("Welcome Admin")
                time.sleep(1)
                st.rerun()
            
            # Normal User Check
            u_data = login_user(user, pwd)
            if u_data:
                st.session_state.logged_in = True
                st.session_state.user_info = u_data
                st.success(f"Welcome {u_data.get('Name')}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    
    if st.button("Back"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- SAYFA: DASHBOARD ---
def show_dashboard():
    df = load_trade_data()
    u_info = st.session_state.user_info
    
    # Top Bar
    c1, c2 = st.columns([3,1])
    with c1: st.markdown(f"**User:** {u_info.get('Name')} | **Plan:** {u_info.get('Plan')}")
    with c2: 
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            go_to("Home")
            
    # Dashboard Content
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    tab1, tab2 = st.tabs(["DASHBOARD", "SETTINGS"])
    
    with tab1:
        if df.empty:
            st.info("No trading data available yet in 'Crazytown_Journal' sheet1.")
        else:
            total = len(df)
            net = df['R_Kazanc'].sum()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Trades", total)
            col2.metric("Net Return (R)", f"{net:.2f}R")
            
            df['Cum'] = df['R_Kazanc'].cumsum()
            fig = px.line(df, x='Tarih', y='Cum', title="Growth Curve")
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)
            
    with tab2:
        st.write("Account Settings")
        st.info(f"Connected as: {u_info.get('Username')}")

# ==========================================
# 5. ANA YÖNLENDİRME (ROUTER)
# ==========================================
if st.session_state.logged_in:
    show_dashboard()
else:
    if st.session_state.current_page == 'Home': show_home()
    elif st.session_state.current_page == 'Register': show_register()
    elif st.session_state.current_page == 'Login': show_login()
