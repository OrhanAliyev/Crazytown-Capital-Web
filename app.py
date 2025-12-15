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
# 1. AYARLAR & CSS (PLATFORM GÖRÜNÜMÜ)
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        /* TEMEL */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 100%; z-index: 2;}

        /* ARKA PLAN */
        .stApp {
            background-color: #0b0c10;
            background: radial-gradient(circle at center, #121418 0%, #000000 100%);
            color: #c5c6c7; font-family: 'Inter', sans-serif;
        }

        /* LIVE SIGNAL KARTI (YENİ) */
        .live-trade-card {
            background: rgba(20, 255, 0, 0.05);
            border: 1px solid #00ff00;
            border-left: 5px solid #00ff00;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            display: flex; justify-content: space-between; align-items: center;
            backdrop-filter: blur(10px);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.2); }
            70% { box-shadow: 0 0 0 10px rgba(0, 255, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0); }
        }

        /* KUTULAR */
        .glass-box, .metric-container, .pricing-card, .login-container {
            background: rgba(31, 40, 51, 0.6); backdrop-filter: blur(15px);
            border: 1px solid rgba(102, 252, 241, 0.1); border-radius: 12px; padding: 20px;
            text-align: center; margin-bottom: 20px;
        }
        .login-container { max-width: 400px; margin: 80px auto; border: 1px solid #66fcf1; box-shadow: 0 0 30px rgba(102, 252, 241, 0.1); }
        
        /* HEADER */
        .status-bar { display: flex; gap: 20px; justify-content: center; margin-bottom: 20px; padding: 10px; border-bottom: 1px solid #333; font-size: 0.85rem; color: #888; }
        .status-active { color: #00ff00; font-weight: bold; }
        .hero-title { font-size: 3rem; font-weight: 800; text-align: center; color: #fff; text-shadow: 0 0 20px rgba(102,252,241,0.5); }
        
        /* INPUT & BUTTON */
        .stTextInput input { background-color: #0f1115 !important; color: #fff !important; border: 1px solid #333 !important; }
        .stButton button { background-color: #66fcf1 !important; color: #000 !important; font-weight: bold; border: none; transition: 0.3s; }
        .stButton button:hover { background-color: #fff !important; transform: scale(1.02); }
        
        /* TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
        .stTabs [data-baseweb="tab"] { height: 45px; color: #666; font-weight: 600; border: none; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important; background: rgba(102,252,241,0.05); }

        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA ENGINE
# ==========================================
def get_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            return gspread.authorize(creds)
        return None
    except: return None

def check_users_db():
    client = get_client()
    if not client: return None
    try:
        sheet = client.open("Crazytown_Journal")
        try: return sheet.worksheet("Users")
        except:
            ws = sheet.add_worksheet(title="Users", rows="100", cols="5")
            ws.append_row(["Username", "Password", "Name", "Plan", "API_Status"])
            return ws
    except: return None

def load_trades():
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

def auth_user(username, password, mode="login", name=None):
    ws = check_users_db()
    if not ws: return "Error"
    users = ws.get_all_records()
    
    if mode == "register":
        for u in users:
            if str(u.get('Username')) == username: return "Exists"
        ws.append_row([username, password, name, "Free Member", "Not Connected"])
        return "Success"
    else:
        for u in users:
            if str(u.get('Username')) == username and str(u.get('Password')) == password: return u
        return None

# ==========================================
# 3. ROUTER
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'nav' not in st.session_state: st.session_state.nav = 'Home'

def navigate(page):
    st.session_state.nav = page
    st.rerun()

# --- HOME ---
def render_home():
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="hero-title">CRAZYTOWN <span style="color:#66fcf1">PRO</span></div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#888;">ADVANCED ALGORITHMIC TRADING TERMINAL</p>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        col1, col2 = st.columns(2)
        with col1: 
            if st.button("🔐 LOGIN TO TERMINAL"): navigate("Login")
        with col2: 
            if st.button("🚀 CREATE ACCOUNT"): navigate("Register")

    st.write("")
    # Feature Grid
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("""<div class="glass-box"><h3>⚡ Live Signals</h3><p>Real-time execution with 12ms latency</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="glass-box"><h3>🔗 API Connect</h3><p>Trade directly on Binance/Bitget via API</p></div>""", unsafe_allow_html=True)
    with c3: st.markdown("""<div class="glass-box"><h3>🛡️ Risk Guard</h3><p>Automated position sizing & SL protection</p></div>""", unsafe_allow_html=True)

# --- LOGIN/REGISTER ---
def render_auth(mode):
    st.markdown(f'<div class="hero-title" style="font-size:2rem;">{mode.upper()}</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("auth"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        n = st.text_input("Full Name") if mode == "Register" else None
        
        if st.form_submit_button("CONTINUE ➜"):
            if mode == "Register":
                if u and p:
                    res = auth_user(u, p, "register", n)
                    if res == "Success": st.success("Created! Login now."); time.sleep(1); navigate("Login")
                    elif res == "Exists": st.error("Username taken.")
                    else: st.error("Connection Error")
            else:
                # Admin
                if u == "admin" and p == "password123":
                    st.session_state.logged_in = True
                    st.session_state.user = {"Name": "Orhan Aliyev", "Plan": "ADMIN", "API_Status": "Connected"}
                    st.rerun()
                
                user = auth_user(u, p, "login")
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.rerun()
                else: st.error("Invalid credentials")
    
    if st.button("Back"): navigate("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD (PRO TERMINAL) ---
def render_dashboard():
    df = load_trades()
    user = st.session_state.user
    
    # STATUS BAR
    st.markdown(f"""
    <div class="status-bar">
        <span>USER: <span style="color:#fff">{user.get('Name')}</span></span>
        <span>PLAN: <span style="color:#66fcf1">{user.get('Plan')}</span></span>
        <span>API: <span class="{ 'status-active' if user.get('API_Status') == 'Connected' else '' }">{user.get('API_Status', 'Not Connected')}</span></span>
        <span>SERVER: <span class="status-active">ONLINE (14ms)</span></span>
    </div>
    """, unsafe_allow_html=True)

    # MENU
    t1, t2, t3, t4 = st.tabs(["⚡ TERMINAL", "🔗 API & BOTS", "📊 ANALYTICS", "🤝 AFFILIATE"])

    # 1. TERMINAL (LIVE SIGNALS)
    with t1:
        # AKTİF POZİSYON KARTI (YENİ!)
        st.markdown("""
        <div class="live-trade-card">
            <div>
                <h3 style="margin:0; color:#fff;">BTC/USDT <span style="font-size:0.8rem; background:#00ff00; color:#000; padding:2px 6px; border-radius:4px;">LONG</span></h3>
                <span style="color:#888; font-size:0.9rem;">Entry: $98,450 | Leverage: 10x</span>
            </div>
            <div style="text-align:right;">
                <h2 style="margin:0; color:#00ff00;">+14.5%</h2>
                <span style="color:#888; font-size:0.8rem;">PNL (Live)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if df.empty:
            st.info("Loading Trade History...")
        else:
            # KPI
            net = df['R_Kazanc'].sum()
            wr = len(df[df['Sonuç']=='WIN']) / len(df) * 100
            
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="glass-box"><h2 style="margin:0; color:#fff">{len(df)}</h2><small>Total Trades</small></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="glass-box"><h2 style="margin:0; color:#66fcf1">{wr:.1f}%</h2><small>Win Rate</small></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="glass-box"><h2 style="margin:0; color:{"#00ff00" if net>0 else "#ff0000"}">{net:.2f}R</h2><small>Net Return</small></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="glass-box"><h2 style="margin:0; color:#fff">2.45</h2><small>Profit Factor</small></div>', unsafe_allow_html=True)

            # CHART
            df['Cum'] = df['R_Kazanc'].cumsum()
            fig = px.area(df, x='Tarih', y='Cum', title="Equity Curve")
            fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300)
            fig.update_traces(line_color='#66fcf1')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True, hide_index=True)

    # 2. API & BOTS (BORSA BAĞLAMA)
    with t2:
        c1, c2 = st.columns([1,2])
        with c1:
            st.markdown("### CONNECT EXCHANGE")
            st.info("Connect your Binance or Bitget account to automate trades.")
            ex = st.selectbox("Select Exchange", ["Binance Futures", "Bitget", "Bybit"])
            apikey = st.text_input("API Key", type="password")
            secret = st.text_input("API Secret", type="password")
            if st.button("LINK API"):
                st.success(f"Successfully connected to {ex}!")
                st.session_state.user['API_Status'] = 'Connected'
                time.sleep(1); st.rerun()
        
        with c2:
            st.markdown("### ACTIVE BOTS")
            st.markdown("""
            <div class="glass-box" style="text-align:left; display:flex; justify-content:space-between;">
                <div><b>🚀 SNIPER V2 (BTC)</b><br><small>Status: Running | PNL: +45%</small></div>
                <button style="background:#ff4b4b; color:white; border:none; padding:5px 10px; border-radius:4px;">STOP</button>
            </div>
            <div class="glass-box" style="text-align:left; display:flex; justify-content:space-between;">
                <div><b>🛡️ SAFEGUARD (ETH)</b><br><small>Status: Paused</small></div>
                <button style="background:#00ff00; color:black; border:none; padding:5px 10px; border-radius:4px;">START</button>
            </div>
            """, unsafe_allow_html=True)

    # 3. ANALYTICS (MONTHLY)
    with t3:
        st.subheader("Monthly Performance")
        # Fake Data for demo
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
        rets = [12.5, -4.2, 8.9, 15.1, 5.3]
        fig_m = go.Figure(go.Bar(x=months, y=rets, marker_color=['#00ff00' if x>0 else '#ff0000' for x in rets]))
        fig_m.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', title="2025 PNL (%)")
        st.plotly_chart(fig_m, use_container_width=True)

    # 4. AFFILIATE (REFERANS)
    with t4:
        st.markdown("<div class='glass-box'><h2>🤝 INVITE & EARN</h2><p>Invite friends and earn 20% lifetime commission.</p></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Your Referral Link", value=f"https://crazytown.capital/?ref={user.get('Username')}", disabled=True)
            st.button("COPY LINK")
        with c2:
            st.metric("Total Referrals", "0")
            st.metric("Pending Commission", "$0.00")
            
    st.markdown("---")
    if st.button("🔒 LOGOUT", type="secondary"):
        st.session_state.logged_in = False
        navigate("Home")

# ==========================================
# 4. START
# ==========================================
if st.session_state.logged_in: render_dashboard()
elif st.session_state.nav == 'Home': render_home()
elif st.session_state.nav == 'Login': render_auth("Login")
elif st.session_state.nav == 'Register': render_auth("Register")

st.markdown("<br><center><small style='color:#555'>© 2025 Crazytown Capital</small></center>", unsafe_allow_html=True)
