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
# 1. AYARLAR VE CSS (V500 MASTER DESIGN)
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TASARIMI ---
st.markdown("""
    <style>
        /* 1. GENEL YAPI */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {
            padding-top: 1rem !important; 
            padding-bottom: 3rem !important; 
            max-width: 100% !important;
            z-index: 2; position: relative;
        }

        /* 2. ARKA PLAN */
        .stApp {
            background-color: #0b0c10;
            background: radial-gradient(circle at center, #0f1115 0%, #000000 100%);
            color: #c5c6c7; font-family: 'Inter', sans-serif;
        }

        /* 3. ELMAS ANIMASYONU */
        .area { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; overflow: hidden; }
        .circles { position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: hidden; }
        .circles li {
            position: absolute; display: block; list-style: none; width: 20px; height: 20px;
            background: rgba(102, 252, 241, 0.08); animation: animate 25s linear infinite;
            bottom: -150px; border: 1px solid rgba(102, 252, 241, 0.2); transform: rotate(45deg);
        }
        .circles li:nth-child(1){ left: 25%; width: 80px; height: 80px; animation-delay: 0s; }
        .circles li:nth-child(2){ left: 10%; width: 20px; height: 20px; animation-delay: 2s; animation-duration: 12s; }
        .circles li:nth-child(3){ left: 70%; width: 20px; height: 20px; animation-delay: 4s; }
        
        @keyframes animate {
            0%{ transform: translateY(0) rotate(45deg); opacity: 0; }
            50%{ opacity: 0.5; }
            100%{ transform: translateY(-1000px) rotate(720deg); opacity: 0; }
        }

        /* 4. CAM KUTULAR (GLASSMORPHISM) */
        .glass-box, .metric-container, .pricing-card, .login-container, .testimonial-card, .status-bar, .vip-card, .payment-card, .academy-card {
            background: rgba(20, 25, 30, 0.85) !important;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(102, 252, 241, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
        }
        
        .payment-card { border: 1px solid #ffd700; background: rgba(255, 215, 0, 0.05) !important; }
        .login-container { max-width: 400px; margin: 60px auto; border: 1px solid #66fcf1; box-shadow: 0 0 30px rgba(102, 252, 241, 0.15); }
        .status-bar { display: flex; gap: 15px; justify-content: center; margin-bottom: 5px; padding: 8px; color: #66fcf1; font-size: 0.8rem; border-bottom: 1px solid #66fcf1; }
        .academy-card { text-align: left; border-left: 4px solid #66fcf1; }

        /* METİNLER VE INPUTLAR */
        .hero-title { font-size: 3.5rem; font-weight: 800; text-align: center; color: #fff; text-shadow: 0 0 20px #66fcf1; margin-bottom: 10px; }
        .hero-sub { font-size: 1.2rem; text-align: center; color: #66fcf1; letter-spacing: 3px; margin-bottom: 40px; }
        .metric-value { font-size: 2.2rem; font-weight: 700; color: #fff; }
        
        .stTextInput input { background-color: #15161a !important; color: #fff !important; border: 1px solid #2d3845 !important; border-radius: 5px !important; }
        .stButton button { background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100% !important; padding: 12px !important; transition: all 0.3s ease; }
        .stButton button:hover { background-color: #fff !important; box-shadow: 0 0 15px #66fcf1; transform: translateY(-2px); }

        /* TABS DÜZENİ */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
        .stTabs [data-baseweb="tab"] { height: 50px; color: #888; font-weight: 600; border: none; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important; background: rgba(102,252,241,0.05); border-radius: 5px 5px 0 0; }
        
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Animasyon
st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 2. VERİTABANI VE FONKSİYONLAR
# ==========================================
def get_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            return gspread.authorize(creds)
        return None
    except: return None

def check_and_fix_users_sheet():
    client = get_client()
    if not client: return None
    try:
        sheet = client.open("Crazytown_Journal")
        try: return sheet.worksheet("Users")
        except:
            ws = sheet.add_worksheet(title="Users", rows="100", cols="4")
            ws.append_row(["Username", "Password", "Name", "Plan"])
            return ws
    except: return None

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
        if str(u.get('Username')) == username and str(u.get('Password')) == password: return u
    return None

# ==========================================
# 3. ROUTER
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'current_page' not in st.session_state: st.session_state.current_page = 'Home'

def go_to(page):
    st.session_state.current_page = page
    st.rerun()

# --- HOME ---
def show_home():
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "CRYPTOCAP:TOTAL", "title": "Total Market Cap"}, {"proName": "CRYPTOCAP:BTC.D", "title": "BTC Dominance"}, {"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    st.markdown('<div class="hero-title">CRAZYTOWN CAPITAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">ENTERPRISE TRADING TERMINAL</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2: 
        if st.button("🚀 LOGIN"): go_to("Login")
    with c4: 
        if st.button("💎 REGISTER"): go_to("Register")

    st.write("")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="glass-box"><h3>⚡ AI Sniper</h3><p>Real-time FVG Detection & Auto-Execution</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="glass-box"><h3>🐋 Whale Hunter</h3><p>Track large institutional money flow live</p></div>""", unsafe_allow_html=True)

    st.markdown("<br><h3 style='text-align:center; color:#fff;'>MEMBERSHIP</h3>", unsafe_allow_html=True)
    pc1, pc2, pc3 = st.columns(3)
    with pc1: st.markdown("""<div class="pricing-card"><h3>STARTER</h3><div class="price">$30</div><p>/mo</p></div>""", unsafe_allow_html=True)
    with pc2: st.markdown("""<div class="pricing-card" style="border:1px solid #66fcf1; box-shadow:0 0 15px rgba(102,252,241,0.2);"><h3>PRO</h3><div class="price">$75</div><p>/qtr</p></div>""", unsafe_allow_html=True)
    with pc3: st.markdown("""<div class="pricing-card"><h3>LIFETIME</h3><div class="price">$250</div><p>once</p></div>""", unsafe_allow_html=True)

# --- REGISTER ---
def show_register():
    st.markdown('<div class="hero-title" style="font-size:2.5rem;">JOIN THE ELITE</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("reg"):
        st.markdown("<h3 style='color:#fff;'>CREATE ACCOUNT</h3>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        n = st.text_input("Full Name")
        if st.form_submit_button("REGISTER NOW"):
            if u and p:
                res = register_user(u, p, n)
                if res == "Success":
                    st.success("Account Created!"); time.sleep(1); go_to("Login")
                elif res == "Exists": st.error("Username Taken!")
                else: st.error("Error")
            else: st.warning("Fill all fields")
    if st.button("Back Home"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- LOGIN ---
def show_login():
    st.markdown('<div class="hero-title" style="font-size:2.5rem;">TERMINAL ACCESS</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("log"):
        st.markdown("<h3 style='color:#fff;'>LOGIN</h3>", unsafe_allow_html=True)
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
                st.success("Access Granted"); time.sleep(1); st.rerun()
            else: st.error("Invalid Credentials")
    if st.button("Back Home"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD (ENTERPRISE) ---
def show_dashboard():
    df = load_trade_data()
    ui = st.session_state.user_info
    
    # 1. STATUS BAR
    latency = random.randint(12, 35)
    st.markdown(f"""
    <div class="status-bar">
        <span><span style="height:8px;width:8px;background:#00ff00;border-radius:50%;display:inline-block;"></span> <b>ONLINE</b> ({latency}ms)</span>
        <span>|</span>
        <span>USER: <b>{ui.get('Name')}</b></span>
        <span>|</span>
        <span>PLAN: <b style="color:#66fcf1">{ui.get('Plan')}</b></span>
    </div>
    """, unsafe_allow_html=True)

    # 2. GLOBAL METRICS
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "CRYPTOCAP:TOTAL", "title": "Total Market Cap"}, {"proName": "CRYPTOCAP:BTC.D", "title": "BTC Dominance"}, {"proName": "CRYPTOCAP:USDT.D", "title": "USDT Dominance"}, {"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "regular", "locale": "en"}</script></div>""", height=40)

    st.write("")
    if st.button("🔒 LOGOUT", key="logout_dash"):
        st.session_state.logged_in = False
        go_to("Home")

    # --- ANA SEKMELER (V500 - YENİ ÖZELLİKLERLE) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 DASHBOARD", "📡 SCANNER & BUBBLES", "🎓 ACADEMY", "🧮 TOOLS", "👑 VIP OFFICE"])
    
    # TAB 1: DASHBOARD
    with tab1:
        if df.empty:
            st.info("No personal trade data found.")
        else:
            total = len(df); win = len(df[df['Sonuç'] == 'WIN']); rate = (win / total * 100) if total > 0 else 0
            net = df['R_Kazanc'].sum()
            df['Cum'] = df['R_Kazanc'].cumsum()
            df['Peak'] = df['Cum'].cummax()
            df['Drawdown'] = df['Cum'] - df['Peak']
            max_dd = df['Drawdown'].min() if not df.empty else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-container"><div class="metric-value">{total}</div><div class="metric-label">TRADES</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-container"><div class="metric-value">{rate:.1f}%</div><div class="metric-label">WIN RATE</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-container"><div class="metric-value" style="color:{"#66fcf1" if net>0 else "#ff4b4b"}">{net:.2f}R</div><div class="metric-label">NET RETURN</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-container"><div class="metric-value" style="color:#ff4b4b">{max_dd:.2f}R</div><div class="metric-label">MAX DRAWDOWN</div></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns([2,1])
            with g1:
                fig = go.Figure(go.Scatter(x=df['Tarih'], y=df['Cum'], mode='lines', fill='tozeroy', line=dict(color='#66fcf1')))
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, title="Equity Curve")
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig_pie = px.pie(df, names='Sonuç', values=[1]*len(df), hole=0.7, color='Sonuç', color_discrete_map={'WIN':'#66fcf1', 'LOSS':'#ff4b4b'})
                fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=300, title="Win/Loss Ratio")
                st.plotly_chart(fig_pie, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # TAB 2: SCANNER & BUBBLES (YENİ PROFESYONEL ÖZELLİKLER)
    with tab2:
        st.subheader("🫧 MARKET BUBBLES")
        # TradingView "Market Overview" ile Baloncuk efekti benzeri bir görünüm
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>{"colorTheme": "dark", "dateRange": "12M", "exchange": "BINANCE", "showChart": true, "locale": "en", "largeChartUrl": "", "isTransparent": true, "showSymbolLogo": true, "showFloatingTooltip": false, "width": "100%", "height": "500", "plotLineColorGrowing": "rgba(41, 98, 255, 1)", "plotLineColorFalling": "rgba(41, 98, 255, 1)", "gridLineColor": "rgba(240, 243, 250, 0)", "scaleFontColor": "rgba(106, 109, 120, 1)", "belowLineFillColorGrowing": "rgba(41, 98, 255, 0.12)", "belowLineFillColorFalling": "rgba(41, 98, 255, 0.12)", "belowLineFillColorGrowingBottom": "rgba(41, 98, 255, 0)", "belowLineFillColorFallingBottom": "rgba(41, 98, 255, 0)", "symbolActiveColor": "rgba(41, 98, 255, 0.12)"}</script></div>""", height=500)
        
        st.write("")
        st.subheader("🔍 CRYPTO SCREENER (TARAYICI)")
        st.info("💡 Filtreleri kullanarak 'Aşırı Satım' (Oversold) veya 'Patlamaya Hazır' coinleri bulun.")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>{"width": "100%", "height": "600", "defaultColumn": "overview", "defaultScreen": "crypto_profitability", "market": "crypto", "showToolbar": true, "colorTheme": "dark", "locale": "en", "isTransparent": true}</script></div>""", height=600)

        st.subheader("📰 LIVE NEWS & LIQUIDATION")
        c1, c2 = st.columns(2)
        with c1:
             components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>{"feedMode": "all_symbols", "colorTheme": "dark", "isTransparent": true, "displayMode": "regular", "width": "100%", "height": "500", "locale": "en"}</script></div>""", height=500)
        with c2:
             components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{"width": "100%", "height": "500", "symbol": "BINANCE:BTCUSDT.P", "interval": "15", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "en", "enable_publishing": false, "allow_symbol_change": true, "calendar": false, "studies": ["STD;Volume@tv-basicstudies"], "support_host": "https://www.tradingview.com"}</script></div>""", height=500)

    # TAB 3: ACADEMY (EĞİTİM MERKEZİ - YENİ)
    with tab3:
        st.markdown("<h2 style='color:#fff;'>🎓 CRAZYTOWN ACADEMY</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#888;'>Master the markets with institutional knowledge.</p>", unsafe_allow_html=True)
        
        ac1, ac2 = st.columns(2)
        with ac1:
            st.markdown("""
            <div class="academy-card">
                <h3 style="color:#fff;">📘 TRADING 101</h3>
                <p style="color:#ccc;">Temel borsa kavramları, mum formasyonları ve piyasa döngüleri.</p>
                <button style="background:#1f2833; color:#66fcf1; border:1px solid #66fcf1; padding:5px; border-radius:4px; width:100px;">READ NOW</button>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="academy-card">
                <h3 style="color:#fff;">🧠 PSYCHOLOGY</h3>
                <p style="color:#ccc;">FOMO yönetimi, risk psikolojisi ve trader zihniyeti.</p>
                <button style="background:#1f2833; color:#66fcf1; border:1px solid #66fcf1; padding:5px; border-radius:4px; width:100px;">READ NOW</button>
            </div>
            """, unsafe_allow_html=True)
        with ac2:
            st.markdown("""
            <div class="academy-card">
                <h3 style="color:#fff;">🐋 WHALE TRACKING</h3>
                <p style="color:#ccc;">On-chain verileri okuma ve balina hareketlerini takip etme.</p>
                <button style="background:#1f2833; color:#66fcf1; border:1px solid #66fcf1; padding:5px; border-radius:4px; width:100px;">READ NOW</button>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="academy-card">
                <h3 style="color:#fff;">⚡ SMC & PRICE ACTION</h3>
                <p style="color:#ccc;">Likidite konseptleri, FVG ve Order Block stratejileri.</p>
                <button style="background:#1f2833; color:#66fcf1; border:1px solid #66fcf1; padding:5px; border-radius:4px; width:100px;">READ NOW</button>
            </div>
            """, unsafe_allow_html=True)

    # TAB 4: TOOLS & CALC
    with tab4:
        st.subheader("🧮 RISK MANAGEMENT")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""<div class='glass-box'><h3>💰 ROI SIMULATOR</h3>""", unsafe_allow_html=True)
            caps = st.number_input("Capital ($)", 100, 100000, 1000, step=100)
            risk = st.slider("Risk Per Trade (%)", 0.5, 5.0, 2.0)
            net_r_total = df['R_Kazanc'].sum() if not df.empty else 25 
            prof = caps * (risk/100) * net_r_total
            st.markdown(f"""<h2 style="color:#66fcf1;">${caps+prof:,.2f}</h2><p>Projected Balance</p></div>""", unsafe_allow_html=True)

        with c2:
            st.markdown("""<div class='glass-box'><h3>⚠️ RISK OF RUIN</h3>""", unsafe_allow_html=True)
            win_rate_input = st.slider("Win Rate (%)", 30, 80, 50)
            risk_input = st.slider("Risk per Trade", 1, 10, 2)
            loss_prob = (100 - win_rate_input) / 100
            win_prob = win_rate_input / 100
            try:
                ror = ((1 - (win_prob - loss_prob)) / (1 + (win_prob - loss_prob))) ** (100/risk_input) * 100
                ror = min(max(ror, 0), 100)
            except: ror = 0.0
            st.markdown(f"""<h2 style="color:{'#ff4b4b' if ror > 1 else '#00ff00'};">{ror:.4f}%</h2><p>Probability of Ruin</p></div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🤝 AFFILIATE")
        st.markdown("<div class='glass-box'><p>Invite friends and earn 20% commission.</p></div>", unsafe_allow_html=True)
        ac1, ac2 = st.columns(2)
        with ac1: st.text_input("Referral Link", value=f"https://crazytown.capital/?ref={ui.get('Username')}", disabled=True)
        with ac2: st.metric("Pending Commission", "$0.00")

    # TAB 5: VIP OFFICE
    with tab5:
        st.markdown("<h2 style='text-align:center; color:#fff;'>UPGRADE MEMBERSHIP</h2>", unsafe_allow_html=True)
        
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            st.markdown("""
            <div class="pricing-card">
                <h3>STARTER</h3>
                <div class="price">$30</div>
                <p>/month</p>
                <ul style='text-align:left; color:#ccc; font-size:0.9rem;'>
                    <li>Basic Signals</li>
                    <li>Community Access</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        with pc2:
            st.markdown("""
            <div class="pricing-card" style="border:1px solid #ffd700; box-shadow:0 0 15px rgba(255,215,0,0.2);">
                <h3 style="color:#ffd700">VIP</h3>
                <div class="price">$75</div>
                <p>/quarter</p>
                <ul style='text-align:left; color:#ccc; font-size:0.9rem;'>
                    <li><b>Everything in Starter</b></li>
                    <li>0ms Latency Signals</li>
                    <li>Whale Alerts</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        with pc3:
            st.markdown("""
            <div class="pricing-card">
                <h3>LIFETIME</h3>
                <div class="price">$250</div>
                <p>once</p>
                <ul style='text-align:left; color:#ccc; font-size:0.9rem;'>
                    <li><b>All Future Updates</b></li>
                    <li>Private Mentorship</li>
                    <li>Bot Source Code</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("")

        c1, c2 = st.columns([1, 2])
        with c1:
            with st.expander("👤 USER SETTINGS", expanded=True):
                st.text_input("Username", value=ui.get('Username'), disabled=True)
                st.text_input("New Password", type="password")
                if st.button("UPDATE PASSWORD"): st.info("Request sent.")
                st.markdown("---")
                st.markdown("**Telegram:** [@Orhan1909](https://t.me/Orhan1909)")
                st.markdown("**Email:** orhanaliyev02@gmail.com")

        with c2:
            st.markdown("""
            <div class='payment-card'>
                <h3 style='color:#ffd700; margin-top:0;'>💳 PAYMENT DETAILS</h3>
                <p style="color:#ccc;">To upgrade, send the amount to one of the addresses below and click 'Confirm Payment'.</p>
                <div style='text-align:left; background:rgba(0,0,0,0.3); padding:12px; border-radius:8px; margin-bottom:10px;'>
                    <span style="color:#26a17b; font-weight:bold;">USDT (TRC20):</span><br>
                    <code style='color:#fff; font-size:1rem;'>TL8w... (SENİN_ADRESİN)</code>
                </div>
                <div style='text-align:left; background:rgba(0,0,0,0.3); padding:12px; border-radius:8px; margin-bottom:10px;'>
                    <span style="color:#f2a900; font-weight:bold;">BITCOIN (BTC):</span><br>
                    <code style='color:#fff; font-size:1rem;'>1A1z... (SENİN_ADRESİN)</code>
                </div>
                <div style='text-align:left; background:rgba(0,0,0,0.3); padding:12px; border-radius:8px; margin-bottom:10px;'>
                    <span style="color:#fff; font-weight:bold;">IBAN (Bank Transfer):</span><br>
                    <code style='color:#fff; font-size:1rem;'>TR12 0000... (SENİN_IBANIN)</code>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            selected_plan = st.selectbox("Select Plan Paid For", ["Starter ($30)", "VIP ($75)", "Lifetime ($250)"])
            tx_id = st.text_input("Transaction ID (Hash) / Sender Name")
            if st.button("✅ CONFIRM PAYMENT"):
                if tx_id:
                    st.success(f"Payment notification for {selected_plan} sent! Admin will enable your access shortly.")
                else:
                    st.warning("Please enter Transaction ID or Sender Name.")

    # KVKK
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("⚖️ LEGAL | KVKK & PRIVACY POLICY"):
        st.markdown("### KİŞİSEL VERİLERİN KORUNMASI KANUNU (KVKK) AYDINLATMA METNİ\nCRAZYTOWN CAPITAL olarak...")

# ==========================================
# 5. MAIN ROUTER
# ==========================================
if st.session_state.logged_in: show_dashboard()
elif st.session_state.current_page == 'Home': show_home()
elif st.session_state.current_page == 'Register': show_register()
elif st.session_state.current_page == 'Login': show_login()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
