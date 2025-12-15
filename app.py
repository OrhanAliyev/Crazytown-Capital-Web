import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
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

# --- CSS: PORTAL TASARIMI ---
st.markdown("""
    <style>
        /* GİZLİLİK */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer, .stDeployButton, [data-testid="stToolbar"] {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 0rem !important; padding-bottom: 2rem !important; z-index: 2; position: relative;}

        /* ARKA PLAN */
        .stApp {
            background: #0b0c10;
            background: linear-gradient(to bottom, #0f1115, #000000);
            color: #c5c6c7;
            font-family: 'Inter', sans-serif;
        }

        /* GİRİŞ EKRANI KUTUSU */
        .login-box {
            background: rgba(31, 40, 51, 0.9);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 15px;
            border: 1px solid #66fcf1;
            box-shadow: 0 0 20px rgba(102, 252, 241, 0.2);
            text-align: center;
            max-width: 400px;
            margin: 100px auto;
        }
        
        /* INPUT ALANLARI */
        .stTextInput input {
            background-color: #1f2833 !important;
            color: #fff !important;
            border: 1px solid #45a29e !important;
            border-radius: 5px !important;
        }
        
        /* BUTONLAR */
        .stButton button {
            background-color: #66fcf1 !important;
            color: #0b0c10 !important;
            font-weight: bold !important;
            border: none !important;
            border-radius: 5px !important;
            width: 100% !important;
            padding: 10px !important;
            transition: all 0.3s ease !important;
        }
        .stButton button:hover {
            background-color: #45a29e !important;
            box-shadow: 0 0 10px #66fcf1 !important;
            color: #fff !important;
        }

        /* ELMAS ANIMASYONU (ARKA PLAN) */
        .area {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; overflow: hidden; pointer-events: none;
        }
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

        @keyframes animate {
            0%{ transform: translateY(0) rotate(45deg); opacity: 0; }
            50%{ opacity: 0.5; }
            100%{ transform: translateY(-1000px) rotate(720deg); opacity: 0; }
        }

        /* DİĞER BİLEŞENLER */
        .metric-container, .pricing-card, .status-bar, .promo-banner, .vip-card {
            background: rgba(31, 40, 51, 0.85); backdrop-filter: blur(5px);
            border: 1px solid #2d3845; border-radius: 8px; z-index: 2;
        }
        .vip-card { padding: 20px; border-left: 4px solid #66fcf1; margin-bottom: 20px; }
        .status-bar { display: flex; gap: 15px; justify-content: center; margin-bottom: 10px; padding: 8px; color: #66fcf1; font-size: 0.8rem; }
        .metric-value { font-size: 2rem; font-weight: 700; color: #fff; }
        .plan-price { font-size: 2.5rem; color: #fff; font-weight: 700; }
        .custom-btn { display: inline-block; padding: 12px 30px; background-color: #66fcf1; color: #0b0c10; border-radius: 4px; text-decoration: none; font-weight: 600; width: 100%; text-align: center; }
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- ANIMASYON ---
st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 2. VERİ VE OTURUM YÖNETİMİ
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
# 3. GİRİŞ EKRANI (LOGIN PAGE)
# ==========================================
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    
    with c2:
        st.markdown("""
        <div style="text-align: center;">
            <h1 style="color: #fff; font-size: 3rem; text-shadow: 0 0 10px #66fcf1;">CRAZYTOWN</h1>
            <p style="color: #66fcf1; letter-spacing: 3px; margin-top: -15px;">ACCESS CONTROL SYSTEM</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Giriş Formu
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("SECURE LOGIN")
            
            if submitted:
                # --- DEMO KULLANICI KONTROLÜ ---
                if username == "admin" and password == "password123":
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = {"name": "Orhan Aliyev", "plan": "LIFETIME ACCESS", "expiry": "Unlimited"}
                    st.success("Access Granted. Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Access Denied. Invalid Credentials.")

        # VIP Sorgulama (Giriş Yapmadan)
        st.markdown("<br><hr style='border-color: #1f2833;'><br>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align:center; color:#888;'>VIP STATUS CHECK</h4>", unsafe_allow_html=True)
        
        email_check = st.text_input("Enter Email / ID to check status", placeholder="e.g. user@email.com")
        if st.button("CHECK STATUS"):
            if email_check:
                # Buraya gerçek veri tabanı bağlanabilir. Şimdilik simülasyon:
                if "admin" in email_check or "orhan" in email_check:
                    st.markdown(f"""
                    <div class="vip-card" style="border-color: #00ff00;">
                        <h3 style="color:#00ff00; margin:0;">✅ ACTIVE MEMBER</h3>
                        <p style="color:#fff;">Plan: <b>LIFETIME PRO</b></p>
                        <p style="color:#888;">Next Billing: Never</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="vip-card" style="border-color: #ff4b4b;">
                        <h3 style="color:#ff4b4b; margin:0;">❌ NOT FOUND / EXPIRED</h3>
                        <p style="color:#fff;">ID: {email_check}</p>
                        <p style="color:#888;">Please contact support to renew.</p>
                    </div>
                    """, unsafe_allow_html=True)

# ==========================================
# 4. ANA DASHBOARD (Giriş Başarılıysa)
# ==========================================
def main_dashboard():
    df = load_data()
    
    # Kullanıcı Profili (Sağ Üst)
    u_info = st.session_state['user_info']
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(31,40,51,0.5); padding:10px 20px; border-radius:8px; border:1px solid #2d3845; margin-bottom:10px;">
        <div style="color:#66fcf1; font-weight:bold;">🟢 SYSTEM ONLINE</div>
        <div style="text-align:right;">
            <span style="color:#fff; font-weight:bold;">{u_info.get('name', 'User')}</span><br>
            <span style="color:#00ff00; font-size:0.8rem;">{u_info.get('plan', 'Member')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Ticker Tape
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}, {"description": "USDT.D", "proName": "CRYPTOCAP:USDT.D"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    st.write("")
    st.markdown("<h1 style='text-align: center; font-size: 3rem; color: #FFFFFF; text-shadow: 0 0 10px #66fcf1; z-index: 5;'>CRAZYTOWN CAPITAL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #66fcf1; margin-top: -15px; letter-spacing: 2px; font-size: 0.9rem; z-index: 5;'>INSTITUTIONAL GRADE ALGORITHMS</p>", unsafe_allow_html=True)
    st.write("")

    tab1, tab2, tab3 = st.tabs(["DASHBOARD & INTEL", "MEMBERSHIP", "TOOLS & SETTINGS"])

    # --- TAB 1: DASHBOARD ---
    with tab1:
        if df.empty:
            st.info("📡 Connecting to secure servers...")
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
        with col1: st.markdown("""<div class="pricing-card"><div class="plan-name">STARTER</div><div class="plan-price">$30<span style="font-size:1rem;color:#888">/mo</span></div><div class="feature-list">✓ Telegram Access<br>✓ 15m Setups<br>✓ FVG Targets</div><a href="https://t.me/Orhan1909" target="_blank" class="custom-btn custom-btn-outline">SELECT</a></div>""", unsafe_allow_html=True)
        with col2: st.markdown("""<div class="pricing-card" style="border-color:#66fcf1"><div class="plan-name">PROFESSIONAL</div><div class="plan-price">$75<span style="font-size:1rem;color:#888">/qtr</span></div><div class="feature-list">✓ <b>All Features</b><br>✓ Real-time Signals<br>✓ USDT.D Analysis</div><a href="https://t.me/Orhan1909" target="_blank" class="custom-btn">POPULAR</a></div>""", unsafe_allow_html=True)
        with col3: st.markdown("""<div class="pricing-card"><div class="plan-name">LIFETIME</div><div class="plan-price">$250<span style="font-size:1rem;color:#888">/once</span></div><div class="feature-list">✓ <b>Lifetime Access</b><br>✓ Bot Support<br>✓ Private Group</div><a href="https://t.me/Orhan1909" target="_blank" class="custom-btn custom-btn-outline">CONTACT</a></div>""", unsafe_allow_html=True)

    # --- TAB 3: TOOLS & SETTINGS ---
    with tab3:
        st.write("")
        
        # Tools
        st.subheader("🧮 TRADING TOOLS")
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
        
        # Profile Settings
        st.subheader("⚙️ PROFILE SETTINGS")
        with st.expander("Change Password"):
            st.text_input("New Password", type="password")
            st.button("Update Password")
        
        if st.button("LOGOUT", type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()

        st.divider()
        co1, co2 = st.columns(2)
        with co1: st.markdown("""### 📨 Telegram<br><a href="https://t.me/Orhan1909" class="custom-btn">OPEN CHAT</a>""", unsafe_allow_html=True)
        with co2: st.markdown("""### 📧 Email<br><div style="background:#1f2833; padding:12px; border-radius:4px; text-align:center;">orhanaliyev02@gmail.com</div>""", unsafe_allow_html=True)

# ==========================================
# 5. UYGULAMA AKIŞI
# ==========================================
if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
