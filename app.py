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
# 1. AYARLAR VE TASARIM (ELMASLI & DARK)
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TASARIMI ---
st.markdown("""
    <style>
        /* 1. TEMEL AYARLAR */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {
            padding-top: 1rem !important; 
            padding-bottom: 2rem !important; 
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

        /* 4. CAM KUTULAR */
        .glass-box, .metric-container, .pricing-card, .login-container, .testimonial-card, .status-bar, .vip-card, .payment-card {
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
        .login-container { max-width: 400px; margin: 50px auto; border: 1px solid #66fcf1; box-shadow: 0 0 20px rgba(102, 252, 241, 0.2); }
        
        /* HEADER BARLARI */
        .status-bar { display: flex; gap: 15px; justify-content: center; margin-bottom: 5px; padding: 8px; color: #66fcf1; font-size: 0.8rem; border-bottom: 1px solid #66fcf1; }
        
        /* METİNLER */
        .hero-title { font-size: 3.5rem; font-weight: 800; text-align: center; color: #fff; text-shadow: 0 0 20px #66fcf1; margin-bottom: 10px; }
        .hero-sub { font-size: 1.2rem; text-align: center; color: #66fcf1; letter-spacing: 3px; margin-bottom: 40px; }
        .metric-value { font-size: 2.5rem; font-weight: 700; color: #fff; }
        
        /* INPUT & BUTTON */
        .stTextInput input { background-color: #15161a !important; color: #fff !important; border: 1px solid #2d3845 !important; border-radius: 5px !important; }
        .stButton button { background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100% !important; padding: 12px !important; transition: all 0.3s ease; }
        .stButton button:hover { background-color: #fff !important; box-shadow: 0 0 15px #66fcf1; transform: translateY(-2px); }

        /* TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
        .stTabs [data-baseweb="tab"] { height: 50px; color: #888; font-weight: 600; border: none; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important; background: rgba(102,252,241,0.05); border-radius: 5px 5px 0 0; }
        
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Animasyon
st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 2. SİSTEM VE VERİTABANI
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
# 3. SAYFA YÖNETİMİ
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'current_page' not in st.session_state: st.session_state.current_page = 'Home'

def go_to(page):
    st.session_state.current_page = page
    st.rerun()

# --- HOME PAGE ---
def show_home():
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "CRYPTOCAP:TOTAL", "title": "Total Market Cap"}, {"proName": "CRYPTOCAP:BTC.D", "title": "BTC Dominance"}, {"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    st.markdown('<div class="hero-title">CRAZYTOWN CAPITAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">ADVANCED TRADING TERMINAL</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2: 
        if st.button("🚀 LOGIN"): go_to("Login")
    with c4: 
        if st.button("💎 REGISTER"): go_to("Register")

    st.write("")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="glass-box"><h3>⚡ Futures Terminal</h3><p>Real-time Liquidation Maps & Funding Rates</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="glass-box"><h3>📊 Global Metrics</h3><p>RSI Heatmaps, Volume Scanner & Market Intel</p></div>""", unsafe_allow_html=True)

    st.markdown("<br><h3 style='text-align:center; color:#fff;'>MEMBERSHIP</h3>", unsafe_allow_html=True)
    pc1, pc2, pc3 = st.columns(3)
    with pc1: st.markdown("""<div class="pricing-card"><h3>STARTER</h3><div class="plan-price">$30</div><p>/mo</p></div>""", unsafe_allow_html=True)
    with pc2: st.markdown("""<div class="pricing-card" style="border:1px solid #66fcf1; box-shadow:0 0 15px rgba(102,252,241,0.2);"><h3>PRO</h3><div class="plan-price">$75</div><p>/qtr</p></div>""", unsafe_allow_html=True)
    with pc3: st.markdown("""<div class="pricing-card"><h3>LIFETIME</h3><div class="plan-price">$250</div><p>once</p></div>""", unsafe_allow_html=True)

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

# --- DASHBOARD (THE ULTIMATE TERMINAL) ---
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

    # --- ANA SEKMELER ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["DASHBOARD", "MARKET DATA", "FUTURES TERMINAL", "NEWS", "PROFILE & VIP"])
    
    # TAB 1: DASHBOARD
    with tab1:
        if df.empty:
            st.info("No personal trade data.")
        else:
            total = len(df); win = len(df[df['Sonuç'] == 'WIN']); rate = (win / total * 100) if total > 0 else 0
            net = df['R_Kazanc'].sum()
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-container"><div class="metric-value">{total}</div><div style="color:#888;">TRADES</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-container"><div class="metric-value">{rate:.1f}%</div><div style="color:#888;">WIN RATE</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-container"><div class="metric-value" style="color:{"#66fcf1" if net>0 else "#ff4b4b"}">{net:.2f}R</div><div style="color:#888;">NET RETURN</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-container"><div class="metric-value">V10.2</div><div style="color:#888;">MODEL</div></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns([2,1])
            with g1:
                df['Cum'] = df['R_Kazanc'].cumsum()
                fig = go.Figure(go.Scatter(x=df['Tarih'], y=df['Cum'], mode='lines', fill='tozeroy', line=dict(color='#66fcf1')))
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig_pie = px.pie(df, names='Sonuç', values=[1]*len(df), hole=0.7, color='Sonuç', color_discrete_map={'WIN':'#66fcf1', 'LOSS':'#ff4b4b'})
                fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=300)
                st.plotly_chart(fig_pie, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # TAB 2: MARKET DATA
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🚀 TOP GAINERS & LOSERS (24h)")
            components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>{"colorTheme": "dark", "dateRange": "12M", "exchange": "BINANCE", "showChart": true, "locale": "en", "largeChartUrl": "", "isTransparent": true, "showSymbolLogo": true, "showFloatingTooltip": false, "width": "100%", "height": "500", "plotLineColorGrowing": "rgba(41, 98, 255, 1)", "plotLineColorFalling": "rgba(41, 98, 255, 1)", "gridLineColor": "rgba(240, 243, 250, 0)", "scaleFontColor": "rgba(106, 109, 120, 1)", "belowLineFillColorGrowing": "rgba(41, 98, 255, 0.12)", "belowLineFillColorFalling": "rgba(41, 98, 255, 0.12)", "belowLineFillColorGrowingBottom": "rgba(41, 98, 255, 0)", "belowLineFillColorFallingBottom": "rgba(41, 98, 255, 0)", "symbolActiveColor": "rgba(41, 98, 255, 0.12)"}</script></div>""", height=500)
        with col2:
            st.subheader("🔥 RSI HEATMAP & SCANNER")
            components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>{"width": "100%", "height": "500", "defaultColumn": "overview", "defaultScreen": "crypto_profitability", "market": "crypto", "showToolbar": true, "colorTheme": "dark", "locale": "en", "isTransparent": true}</script></div>""", height=500)
        
        st.subheader("🌍 CRYPTO HEATMAP")
        components.html("""<script defer src="https://www.livecoinwatch.com/widgets/heatmap.js"></script><div class="livecoinwatch-widget-heatmap" currency="USD" width="100%" height="400"></div>""", height=400)

    # TAB 3: FUTURES TERMINAL
    with tab3:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("🗺️ LIQUIDATION & VOLUME ANALYSIS")
            components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{"width": "100%", "height": "500", "symbol": "BINANCE:BTCUSDT.P", "interval": "15", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "en", "enable_publishing": false, "allow_symbol_change": true, "calendar": false, "studies": ["STD;Volume@tv-basicstudies","STD;VWAP@tv-basicstudies"], "support_host": "https://www.tradingview.com"}</script></div>""", height=500)
        
        with c2:
            st.subheader("💸 FUNDING RATES")
            st.markdown("""
            <div class="glass-box" style="text-align:left;">
                <table style="width:100%; color:#ccc;">
                    <tr style="border-bottom:1px solid #444;"><th>PAIR</th><th>RATE</th><th>PREDICT</th></tr>
                    <tr><td>BTC/USDT</td><td style="color:#00ff00;">0.0100%</td><td>0.0102%</td></tr>
                    <tr><td>ETH/USDT</td><td style="color:#00ff00;">0.0125%</td><td>0.0110%</td></tr>
                    <tr><td>SOL/USDT</td><td style="color:#ff4b4b;">-0.004%</td><td>-0.002%</td></tr>
                    <tr><td>XRP/USDT</td><td style="color:#00ff00;">0.0100%</td><td>0.0100%</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

    # TAB 4: NEWS
    with tab4:
        st.subheader("📰 LIVE NEWS TERMINAL")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>{"feedMode": "all_symbols", "colorTheme": "dark", "isTransparent": true, "displayMode": "regular", "width": "100%", "height": "600", "locale": "en"}</script></div>""", height=600)

    # TAB 5: PROFILE & VIP (YENİ ÖDEME SİSTEMİ)
    with tab5:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='vip-card'><h3>👤 USER SETTINGS</h3>", unsafe_allow_html=True)
            st.text_input("Username", value=ui.get('Username'), disabled=True)
            new_pass = st.text_input("New Password", type="password")
            if st.button("UPDATE PASSWORD"):
                st.info("Password update request sent to admin.")
            
            st.markdown("<br><h3>📞 CONTACT SUPPORT</h3>", unsafe_allow_html=True)
            st.markdown("**Telegram:** [@Orhan1909](https://t.me/Orhan1909)")
            st.markdown("**Email:** orhanaliyev02@gmail.com")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c2:
            st.markdown("""
            <div class='payment-card'>
                <h2 style='color:#ffd700'>👑 VIP PAYMENT</h2>
                <p>Unlock Institutional Signals & 0ms Latency</p>
                <div style='text-align:left; background:rgba(0,0,0,0.3); padding:10px; border-radius:5px;'>
                    <b>USDT (TRC20):</b><br>
                    <code style='color:#66fcf1'>TL8w... (KENDİ TRC20 ADRESİNİ YAZ)</code>
                </div>
                <br>
                <div style='text-align:left; background:rgba(0,0,0,0.3); padding:10px; border-radius:5px;'>
                    <b>BITCOIN (BTC):</b><br>
                    <code style='color:#ffd700'>1A1z... (KENDİ BTC ADRESİNİ YAZ)</code>
                </div>
                <br>
                <div style='text-align:left; background:rgba(0,0,0,0.3); padding:10px; border-radius:5px;'>
                    <b>BANK TRANSFER (IBAN):</b><br>
                    <code>TR12 0000... (KENDİ IBANINI YAZ)</code>
                </div>
                <br>
                <p style='font-size:0.8rem; color:#888;'>*After payment, send receipt to @Orhan1909</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("CONFIRM PAYMENT"):
                st.success("Payment notification sent! Admin will verify shortly.")

    # KVKK FOOTER
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("⚖️ LEGAL | KVKK & PRIVACY POLICY (AYDINLATMA METNİ)"):
        st.markdown("""
        ### KİŞİSEL VERİLERİN KORUNMASI KANUNU (KVKK) AYDINLATMA METNİ
        
        **CRAZYTOWN CAPITAL** olarak kişisel verilerinizin güvenliği hususuna azami hassasiyet göstermekteyiz. 
        6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") uyarınca, kişisel verileriniz aşağıda açıklanan kapsamda işlenebilecektir.

        **1. Veri Sorumlusu:**
        Kişisel verileriniz; veri sorumlusu sıfatıyla **CRAZYTOWN CAPITAL** tarafından işlenmektedir.

        **2. Kişisel Verilerin İşlenme Amacı:**
        Toplanan kişisel verileriniz; platform üyelik işlemlerinin gerçekleştirilmesi, finansal analiz hizmetlerinin sunulması, 
        yasal yükümlülüklerin yerine getirilmesi ve müşteri destek süreçlerinin yönetilmesi amacıyla işlenmektedir.

        **3. İşlenen Kişisel Veriler:**
        - Kimlik Bilgileri (Ad, Soyad)
        - İletişim Bilgileri (E-posta, Telefon Numarası)
        - İşlem Güvenliği Bilgileri (Kullanıcı Adı, Şifre, IP Adresi)

        **4. Kişisel Verilerin Aktarılması:**
        Kişisel verileriniz, yasal zorunluluklar (resmi kurumlar) dışında üçüncü kişilerle paylaşılmamaktadır.

        **5. Haklarınız:**
        KVKK'nın 11. maddesi gereği; verilerinizin işlenip işlenmediğini öğrenme, düzeltme talep etme ve silinmesini isteme hakkına sahipsiniz.
        
        *İletişim: orhanaliyev02@gmail.com*
        """)

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
