import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import random
import yfinance as yf
import pandas_ta as ta  # Teknik analiz kütüphanesi

# ==========================================
# 1. AYARLAR VE CSS (V600 ULTRA DESIGN)
# ==========================================
st.set_page_config(
    page_title="OA|Trade| V600 Terminal",
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
        .glass-box, .metric-container, .pricing-card, .login-container, .academy-card, .status-bar {
            background: rgba(20, 25, 30, 0.85) !important;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(102, 252, 241, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
        }
        
        .payment-card { border: 1px solid #ffd700; background: rgba(255, 215, 0, 0.05) !important; padding: 20px; border-radius:12px; }
        .login-container { max-width: 400px; margin: 60px auto; border: 1px solid #66fcf1; box-shadow: 0 0 30px rgba(102, 252, 241, 0.15); }
        .status-bar { display: flex; gap: 15px; justify-content: center; margin-bottom: 5px; padding: 8px; color: #66fcf1; font-size: 0.8rem; border-bottom: 1px solid #66fcf1; }
        .academy-card { text-align: left; border-left: 4px solid #66fcf1; }

        /* METİNLER VE INPUTLAR */
        .hero-title { font-size: 3.5rem; font-weight: 800; text-align: center; color: #fff; text-shadow: 0 0 20px #66fcf1; margin-bottom: 10px; }
        .hero-sub { font-size: 1.2rem; text-align: center; color: #66fcf1; letter-spacing: 3px; margin-bottom: 40px; }
        .metric-value { font-size: 2.2rem; font-weight: 700; color: #fff; }
        
        .stTextInput input, .stNumberInput input, .stSelectbox, .stDateInput input { background-color: #15161a !important; color: #fff !important; border: 1px solid #2d3845 !important; border-radius: 5px !important; }
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

# --- GÜNCELLEME: PnL Takvimi için Veri Yükleme ---
# Google Sheets yoksa geçici session_state kullanır
if 'pnl_data' not in st.session_state:
    st.session_state.pnl_data = pd.DataFrame(columns=['Date', 'Amount', 'Note'])

def save_pnl_entry(date, amount, note):
    # Eğer Google Sheets varsa oraya kaydet, yoksa session_state'e
    new_row = {'Date': pd.to_datetime(date), 'Amount': float(amount), 'Note': note}
    st.session_state.pnl_data = pd.concat([st.session_state.pnl_data, pd.DataFrame([new_row])], ignore_index=True)
    # Burada Google Sheets entegrasyonu da yapılabilir:
    # ws.append_row([str(date), amount, note])

def load_trade_data():
    client = get_client()
    if not client: return pd.DataFrame() # Boş döner
    try:
        sheet = client.open("Crazytown_Journal").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if 'R_Kazanc' in df.columns:
            df['R_Kazanc'] = pd.to_numeric(df['R_Kazanc'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

# --- YENİ ÖZELLİK: AI SIGNAL GENERATOR ---
@st.cache_data(ttl=300)
def get_market_signals():
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'XRP-USD']
    data = []
    for sym in symbols:
        try:
            df = yf.download(sym, period='1mo', interval='1d', progress=False)
            if len(df) > 0:
                rsi = df.ta.rsi(length=14).iloc[-1]
                ema_50 = df.ta.ema(length=50).iloc[-1]
                close = float(df['Close'].iloc[-1])
                
                signal = "NEUTRAL"
                color = "white"
                
                if rsi < 30: 
                    signal = "STRONG BUY 🚀"
                    color = "#00ff00"
                elif rsi > 70: 
                    signal = "STRONG SELL 🩸"
                    color = "#ff4b4b"
                elif close > ema_50 and rsi > 50:
                    signal = "BULL TREND 📈"
                    color = "#66fcf1"
                
                data.append({
                    "Coin": sym.replace('-USD', ''),
                    "Price": f"${close:,.2f}",
                    "RSI": f"{rsi:.1f}",
                    "Signal": signal,
                    "Color": color
                })
        except: continue
    return pd.DataFrame(data)

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
# 3. ROUTER VE SAYFALAR
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
    st.markdown('<div class="hero-title">OA|Trade</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">ENTERPRISE TRADING TERMINAL V6</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2: 
        if st.button("🚀 LOGIN"): go_to("Login")
    with c4: 
        if st.button("💎 REGISTER"): go_to("Register")

    st.write("")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="glass-box"><h3>⚡ AI Sniper</h3><p>Real-time FVG Detection & Auto-Execution</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="glass-box"><h3>🐋 Whale Hunter</h3><p>Track large institutional money flow live</p></div>""", unsafe_allow_html=True)

# --- LOGIN & REGISTER (Değişiklik Yok) ---
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
                if res == "Success": st.success("Account Created!"); time.sleep(1); go_to("Login")
                elif res == "Exists": st.error("Username Taken!")
                else: st.error("Error")
            else: st.warning("Fill all fields")
    if st.button("Back Home"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

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

    # 3. WHALE ALERT TOAST (YENİ ÖZELLİK)
    if st.button("🔔 Activate Whale Radar (Simulate)", use_container_width=True):
        w_coins = ["BTC", "ETH", "SOL"]
        w_act = random.choice(["Bought", "Sold", "Moved to Cold Wallet"])
        w_amt = random.randint(1, 50) * 1000000
        st.toast(f"🐋 WHALE ALERT: {w_amt}$ worth of {random.choice(w_coins)} was just {w_act}!", icon="🚨")

    st.write("")
    if st.button("🔒 LOGOUT", key="logout_dash"):
        st.session_state.logged_in = False
        go_to("Home")

    # --- ANA SEKMELER (GÜNCELLENDİ) ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 DASHBOARD", "📡 AI SCANNER", "🗓️ PnL CALENDAR", "🎓 ACADEMY", "🧮 TOOLS", "👑 VIP OFFICE"])
    
    # TAB 1: DASHBOARD
    with tab1:
        if df.empty:
            st.info("No personal trade data found via Google Sheets. Using demo visualization.")
            # Demo Data
            dates = pd.date_range(start="2023-01-01", periods=100)
            cum_rets = pd.Series(range(100)).apply(lambda x: x + random.randint(-5, 10)).cumsum()
            fig = go.Figure(go.Scatter(x=dates, y=cum_rets, mode='lines', fill='tozeroy', line=dict(color='#66fcf1')))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, title="Demo Equity Curve")
            st.plotly_chart(fig, use_container_width=True)
        else:
            total = len(df); win = len(df[df['Sonuç'] == 'WIN']); rate = (win / total * 100) if total > 0 else 0
            net = df['R_Kazanc'].sum()
            df['Cum'] = df['R_Kazanc'].cumsum()
            
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-container"><div class="metric-value">{total}</div><div class="metric-label">TRADES</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-container"><div class="metric-value">{rate:.1f}%</div><div class="metric-label">WIN RATE</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-container"><div class="metric-value" style="color:{"#66fcf1" if net>0 else "#ff4b4b"}">{net:.2f}R</div><div class="metric-label">NET RETURN</div></div>', unsafe_allow_html=True)
            
            fig = go.Figure(go.Scatter(x=df['Tarih'], y=df['Cum'], mode='lines', fill='tozeroy', line=dict(color='#66fcf1')))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, title="Equity Curve")
            st.plotly_chart(fig, use_container_width=True)

    # TAB 2: AI SCANNER (YENİ PYTHON ÖZELLİĞİ)
    with tab2:
        st.subheader("📡 AI SIGNAL GENERATOR (Python Native)")
        col_scan1, col_scan2 = st.columns([2, 1])
        
        with col_scan1:
            try:
                signals_df = get_market_signals()
                html_table = "<div class='glass-box' style='padding:0; overflow:hidden;'><table style='width:100%; border-collapse: collapse;'>"
                html_table += "<tr style='background:rgba(102, 252, 241, 0.1); color:#66fcf1;'><th>COIN</th><th>PRICE</th><th>RSI</th><th>AI SIGNAL</th></tr>"
                for index, row in signals_df.iterrows():
                    html_table += f"""<tr style='border-bottom:1px solid rgba(255,255,255,0.1);'><td style='padding:10px; font-weight:bold;'>{row['Coin']}</td><td style='padding:10px;'>{row['Price']}</td><td style='padding:10px;'>{row['RSI']}</td><td style='padding:10px; color:{row['Color']}; font-weight:bold;'>{row['Signal']}</td></tr>"""
                html_table += "</table></div>"
                st.markdown(html_table, unsafe_allow_html=True)
            except Exception as e: st.error(f"Data Feed Error: {e}")
        
        with col_scan2:
             components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>{"interval": "1m", "width": "100%", "isTransparent": true, "height": "400", "symbol": "BINANCE:BTCUSDT", "showIntervalTabs": true, "displayMode": "single", "locale": "en", "colorTheme": "dark"}</script></div>""", height=400)

    # TAB 3: PnL CALENDAR (YENİ ÖZELLİK - İSTEK ÜZERİNE)
    with tab3:
        st.markdown("<h2 style='text-align:center;'>🗓️ PROFIT & LOSS CALENDAR</h2>", unsafe_allow_html=True)
        
        # 1. Veri Girişi
        with st.expander("➕ ADD DAILY PnL RECORD", expanded=False):
            with st.form("pnl_entry"):
                c_d1, c_d2, c_d3 = st.columns(3)
                p_date = c_d1.date_input("Date", datetime.today())
                p_amt = c_d2.number_input("Profit/Loss ($)", step=10.0)
                p_note = c_d3.text_input("Note (Pair etc.)")
                if st.form_submit_button("ADD RECORD"):
                    save_pnl_entry(p_date, p_amt, p_note)
                    st.success("Record Added!")
                    st.rerun()

        # 2. Hesaplamalar
        pnl_df = st.session_state.pnl_data
        if not pnl_df.empty:
            pnl_df['Date'] = pd.to_datetime(pnl_df['Date'])
            pnl_df['Month'] = pnl_df['Date'].dt.strftime('%Y-%m')
            pnl_df['MonthName'] = pnl_df['Date'].dt.strftime('%B')
            
            # Aylık Gruplama
            monthly_pnl = pnl_df.groupby('Month')['Amount'].sum().reset_index()
            total_pnl = pnl_df['Amount'].sum()
            best_month = monthly_pnl['Amount'].max() if not monthly_pnl.empty else 0
            
            # Üst Metrikler
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"<div class='glass-box'><h3 style='color:{'#00ff00' if total_pnl>0 else '#ff4b4b'}'>${total_pnl:,.2f}</h3><p>TOTAL YEAR PnL</p></div>", unsafe_allow_html=True)
            m2.markdown(f"<div class='glass-box'><h3>{len(pnl_df)}</h3><p>DAYS TRADED</p></div>", unsafe_allow_html=True)
            m3.markdown(f"<div class='glass-box'><h3 style='color:#66fcf1'>${best_month:,.2f}</h3><p>BEST MONTH</p></div>", unsafe_allow_html=True)

            # Grafik: Aylık Kazanç
            fig_pnl = px.bar(monthly_pnl, x='Month', y='Amount', color='Amount',
                             color_continuous_scale=['#ff4b4b', '#00ff00'], title="Monthly Performance")
            fig_pnl.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pnl, use_container_width=True)
            
            # Tablo Detayı
            st.markdown("### 📜 Transaction Log")
            st.dataframe(pnl_df.sort_values(by='Date', ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No records yet. Add your daily profits above to see the calendar.")

    # TAB 4: ACADEMY
    with tab4:
        st.markdown("<h2 style='color:#fff;'>🎓 CRAZYTOWN ACADEMY</h2>", unsafe_allow_html=True)
        ac1, ac2 = st.columns(2)
        with ac1:
            st.markdown("""<div class="academy-card"><h3 style="color:#fff;">📘 TRADING 101</h3><p style="color:#ccc;">Temel borsa kavramları.</p></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="academy-card"><h3 style="color:#fff;">🧠 PSYCHOLOGY</h3><p style="color:#ccc;">FOMO yönetimi.</p></div>""", unsafe_allow_html=True)
        with ac2:
            st.markdown("""<div class="academy-card"><h3 style="color:#fff;">🐋 WHALE TRACKING</h3><p style="color:#ccc;">On-chain verileri okuma.</p></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="academy-card"><h3 style="color:#fff;">⚡ SMC & PRICE ACTION</h3><p style="color:#ccc;">Order Block stratejileri.</p></div>""", unsafe_allow_html=True)

    # TAB 5: TOOLS & BACKTESTER (YENİ ÖZELLİK)
    with tab5:
        st.subheader("🔙 STRATEGY BACKTESTER")
        col_b1, col_b2 = st.columns([1, 3])
        with col_b1:
            st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
            bt_coin = st.selectbox("Select Asset", ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"])
            bt_invest = st.number_input("Investment ($)", 100, 100000, 1000)
            bt_days = st.slider("Days Ago", 7, 365, 30)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_b2:
            try:
                df_bt = yf.download(bt_coin, period=f"{bt_days}d", interval="1d", progress=False)
                if not df_bt.empty:
                    start_price = float(df_bt['Close'].iloc[0])
                    end_price = float(df_bt['Close'].iloc[-1])
                    roi_perc = ((end_price - start_price) / start_price) * 100
                    profit = bt_invest * (roi_perc/100)
                    
                    c_res1, c_res2, c_res3 = st.columns(3)
                    color_res = "#00ff00" if profit > 0 else "#ff4b4b"
                    
                    c_res1.metric("Start Price", f"${start_price:,.2f}")
                    c_res2.metric("Current Price", f"${end_price:,.2f}")
                    c_res3.markdown(f"""<div class='glass-box' style='padding:10px; border:1px solid {color_res}'><h3 style='color:{color_res}; margin:0;'>${profit:+,.2f}</h3><small>PnL ({roi_perc:.2f}%)</small></div>""", unsafe_allow_html=True)
                    
                    df_bt['Portfolio Value'] = (df_bt['Close'] / start_price) * bt_invest
                    fig_bt = px.area(df_bt, x=df_bt.index, y='Portfolio Value', title=f"{bt_invest}$ Investment Growth")
                    fig_bt.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#66fcf1"))
                    fig_bt.update_traces(line_color='#66fcf1', fillcolor='rgba(102, 252, 241, 0.2)')
                    st.plotly_chart(fig_bt, use_container_width=True)
            except Exception as e: st.error("Data fetch failed.")
        
        st.markdown("---")
        st.subheader("🧮 CALCULATORS")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""<div class='glass-box'><h3>💰 ROI SIMULATOR</h3>""", unsafe_allow_html=True)
            caps = st.number_input("Capital ($)", 100, 100000, 1000, step=100)
            risk = st.slider("Risk Per Trade (%)", 0.5, 5.0, 2.0)
            prof = caps * (risk/100) * 20 
            st.markdown(f"""<h2 style="color:#66fcf1;">${caps+prof:,.2f}</h2><p>Projected Balance (20R Profit)</p></div>""", unsafe_allow_html=True)
        with c2:
             st.markdown("""<div class='glass-box'><h3>⚠️ RISK OF RUIN</h3>""", unsafe_allow_html=True)
             st.markdown(f"""<h2 style="color:#00ff00;">0.01%</h2><p>Probability (Demo)</p></div>""", unsafe_allow_html=True)

    # TAB 6: VIP OFFICE (Değişiklik Yok)
    with tab6:
        st.markdown("<h2 style='text-align:center; color:#fff;'>UPGRADE MEMBERSHIP</h2>", unsafe_allow_html=True)
        pc1, pc2, pc3 = st.columns(3)
        with pc1: st.markdown("""<div class="pricing-card"><h3>STARTER</h3><div class="price">$30</div><p>/month</p></div>""", unsafe_allow_html=True)
        with pc2: st.markdown("""<div class="pricing-card" style="border:1px solid #ffd700; box-shadow:0 0 15px rgba(255,215,0,0.2);"><h3 style="color:#ffd700">VIP</h3><div class="price">$75</div><p>/quarter</p></div>""", unsafe_allow_html=True)
        with pc3: st.markdown("""<div class="pricing-card"><h3>LIFETIME</h3><div class="price">$250</div><p>once</p></div>""", unsafe_allow_html=True)

# ==========================================
# 5. MAIN ROUTER
# ==========================================
if st.session_state.logged_in: show_dashboard()
elif st.session_state.current_page == 'Home': show_home()
elif st.session_state.current_page == 'Register': show_register()
elif st.session_state.current_page == 'Login': show_login()


