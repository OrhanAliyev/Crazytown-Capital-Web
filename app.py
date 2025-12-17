import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import time
import ccxt  # GERÇEK KRİPTO VERİSİ İÇİN
import numpy as np

# ==========================================
# 1. AYARLAR VE CSS
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Live Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TASARIMI ---
st.markdown("""
    <style>
        /* GENEL YAPI */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 1rem; padding-bottom: 3rem; max-width: 100%; z-index: 2; position: relative;}

        /* ARKA PLAN */
        .stApp {
            background-color: #0b0c10;
            background: radial-gradient(circle at center, #0f1115 0%, #000000 100%);
            color: #c5c6c7; font-family: 'Inter', sans-serif;
        }

        /* ELMAS ANIMASYONU */
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

        /* CAM KUTULAR */
        .glass-box, .metric-container, .pricing-card, .login-container, .tool-card, .payment-card {
            background: rgba(20, 25, 30, 0.85) !important;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(102, 252, 241, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
        }
        
        .tool-card { text-align: left; border-left: 4px solid #66fcf1; transition: transform 0.3s ease; position:relative; overflow:hidden;}
        .tool-card:hover { transform: translateX(5px); border-color: #ffd700; }
        .tool-title { font-weight: bold; color: #fff; font-size: 1.1rem; display: flex; justify-content: space-between; }
        .status-bullish { color: #00ff00; background: rgba(0,255,0,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;}
        .status-bearish { color: #ff4b4b; background: rgba(255,75,75,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;}
        .status-neutral { color: #ccc; background: rgba(200,200,200,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;}

        /* INPUT VE BUTTON */
        .stTextInput input { background-color: #15161a !important; color: #fff !important; border: 1px solid #2d3845 !important; border-radius: 5px !important; }
        .stButton button { background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100% !important; padding: 12px !important; transition: all 0.3s ease; }
        .stButton button:hover { background-color: #fff !important; box-shadow: 0 0 15px #66fcf1; transform: translateY(-2px); }

        /* TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
        .stTabs [data-baseweb="tab"] { height: 50px; color: #888; font-weight: 600; border: none; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important; background: rgba(102,252,241,0.05); }
        
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 2. GERÇEK VERİ MOTORU (CCXT & LOGIC)
# ==========================================

# Binance'den Canlı Veri Çekme Fonksiyonu
@st.cache_data(ttl=15) # 15 saniyede bir veriyi yeniler
def get_live_market_data(symbol='BTC/USDT'):
    try:
        exchange = ccxt.binance()
        # Son 100 mumu (1 saatlik) çek
        bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        return pd.DataFrame()

# Teknik Analiz Hesaplama Motoru (RSI, SMA)
def calculate_signals(df):
    if df.empty: return None, None, None, None
    
    # Kapanış Fiyatları
    closes = df['close']
    
    # 1. RSI Hesaplama (Manuel, kütüphanesiz)
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    # 2. Market Waves (SMA Kesişimi Simülasyonu)
    sma_short = closes.rolling(window=7).mean().iloc[-1]
    sma_long = closes.rolling(window=25).mean().iloc[-1]
    
    # 3. Beluga (Hacim Analizi)
    current_vol = df['volume'].iloc[-1]
    avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
    vol_spike = (current_vol / avg_vol) * 100 if avg_vol > 0 else 0
    
    return current_rsi, sma_short, sma_long, vol_spike

# ==========================================
# 3. SİNYAL OLUŞTURUCU
# ==========================================
def generate_pro_signals(symbol):
    df = get_live_market_data(symbol)
    if df.empty:
        return {"price": 0, "rsi": 50, "trend": "NEUTRAL", "whale": "LOW"}
    
    rsi, sma_s, sma_l, vol = calculate_signals(df)
    current_price = df['close'].iloc[-1]
    
    # Market Waves Kararı
    if sma_s > sma_l: trend = "BULLISH WAVE 🟢"
    else: trend = "BEARISH WAVE 🔴"
    
    # Beluga Kararı
    whale_alert = "HIGH 🐋" if vol > 150 else "NORMAL 🌊"
    
    return {
        "price": current_price,
        "rsi": rsi,
        "trend": trend,
        "whale": whale_alert,
        "vol_pct": vol
    }

# ==========================================
# 4. KULLANICI SİSTEMİ
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'current_page' not in st.session_state: st.session_state.current_page = 'Home'

def go_to(page): st.session_state.current_page = page; st.rerun()

# --- SAYFALAR ---
def show_home():
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)
    st.markdown('<div class="hero-title">CRAZYTOWN CAPITAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">LIVE MARKET INTELLIGENCE SYSTEM</div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2: 
        if st.button("🚀 LOGIN"): go_to("Login")
    with c4: 
        if st.button("💎 REGISTER"): go_to("Register")

    st.write("")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="glass-box"><h3>⚡ Market Waves Pro</h3><p>Real-time Trend Following & RSI Logic</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="glass-box"><h3>🐋 Beluga Nautilus</h3><p>Live Volume Spike Detection</p></div>""", unsafe_allow_html=True)

    st.markdown("<br><h3 style='text-align:center; color:#fff;'>MEMBERSHIP PLANS</h3>", unsafe_allow_html=True)
    pc1, pc2, pc3 = st.columns(3)
    with pc1: st.markdown("""<div class="pricing-card"><h3>STARTER</h3><div style="font-size:2rem;color:#fff;">$30</div><p>/mo</p></div>""", unsafe_allow_html=True)
    with pc2: st.markdown("""<div class="pricing-card" style="border:1px solid #66fcf1;"><h3>VIP</h3><div style="font-size:2rem;color:#fff;">$75</div><p>/qtr</p></div>""", unsafe_allow_html=True)
    with pc3: st.markdown("""<div class="pricing-card"><h3>LIFETIME</h3><div style="font-size:2rem;color:#fff;">$250</div><p>once</p></div>""", unsafe_allow_html=True)

def show_auth(mode):
    st.markdown(f'<div class="hero-title" style="font-size:2.5rem;">{mode}</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("auth"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("SUBMIT"):
            if mode == "Register":
                st.success("Account Created! Login now.")
                time.sleep(1); go_to("Login")
            else:
                if u == "admin" and p == "password123":
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"Name": "Orhan Aliyev", "Plan": "ADMIN"}
                    st.rerun()
                else: st.error("Invalid Credentials")
    if st.button("Back"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD (LIVE DATA) ---
def show_dashboard():
    # Canlı Verileri Çek (BTC ve ETH için)
    btc_data = generate_pro_signals('BTC/USDT')
    eth_data = generate_pro_signals('ETH/USDT')
    
    ui = st.session_state.user_info
    
    # Status Bar
    st.markdown(f"""
    <div class="status-bar">
        <span><span style="height:8px;width:8px;background:#00ff00;border-radius:50%;display:inline-block;"></span> <b>SYSTEM ONLINE</b></span>
        <span>|</span>
        <span>DATA FEED: <b>BINANCE LIVE</b></span>
        <span>|</span>
        <span>USER: <b>{ui.get('Name')}</b></span>
    </div>
    """, unsafe_allow_html=True)

    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"}</script></div>""", height=50)

    st.write("")
    if st.button("🔒 LOGOUT"): st.session_state.logged_in = False; go_to("Home")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ PRO TOOLS", "📊 MARKET DATA", "🎓 ACADEMY", "🧮 CALCULATORS", "👑 VIP OFFICE"])
    
    # TAB 1: PRO TOOLS (CANLI HESAPLAMA)
    with tab1:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
            <h3 style="margin:0;">⚡ LIVE ALGORITHMIC SIGNALS</h3>
            <span style="color:#888; font-size:0.8rem;">Last Update: {datetime.now().strftime('%H:%M:%S')}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Sinyal Yenileme Butonu
        if st.button("🔄 REFRESH SIGNALS"):
            st.rerun()

        c1, c2 = st.columns(2)
        
        # BTC KARTI
        with c1:
            trend_col = "status-bullish" if "BULLISH" in btc_data['trend'] else "status-bearish"
            whale_col = "status-bullish" if "HIGH" in btc_data['whale'] else "status-neutral"
            
            st.markdown(f"""
            <div class="tool-card" style="border-left-color: #f2a900;">
                <div class="tool-title">BITCOIN (BTC) <span style="font-size:0.9rem;">${btc_data['price']:,.2f}</span></div>
                <hr style="border-color:rgba(255,255,255,0.1);">
                <p style="color:#ccc; font-size:0.9rem; line-height:1.8;">
                    🌊 <b>Market Waves:</b> <span class="{trend_col}">{btc_data['trend']}</span><br>
                    🐋 <b>Beluga Vol:</b> <span class="{whale_col}">{btc_data['whale']} ({btc_data['vol_pct']:.0f}%)</span><br>
                    📈 <b>RSI (14):</b> <b style="color:{'#00ff00' if btc_data['rsi']<30 else '#ff4b4b' if btc_data['rsi']>70 else '#fff'}">{btc_data['rsi']:.2f}</b><br>
                    🎯 <b>AI Call:</b> {"LONG LOOK" if btc_data['rsi'] < 40 and "BULLISH" in btc_data['trend'] else "SHORT LOOK" if btc_data['rsi'] > 60 and "BEARISH" in btc_data['trend'] else "WAIT"}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # ETH KARTI
        with c2:
            trend_col = "status-bullish" if "BULLISH" in eth_data['trend'] else "status-bearish"
            whale_col = "status-bullish" if "HIGH" in eth_data['whale'] else "status-neutral"
            
            st.markdown(f"""
            <div class="tool-card" style="border-left-color: #627eea;">
                <div class="tool-title">ETHEREUM (ETH) <span style="font-size:0.9rem;">${eth_data['price']:,.2f}</span></div>
                <hr style="border-color:rgba(255,255,255,0.1);">
                <p style="color:#ccc; font-size:0.9rem; line-height:1.8;">
                    🌊 <b>Market Waves:</b> <span class="{trend_col}">{eth_data['trend']}</span><br>
                    🐋 <b>Beluga Vol:</b> <span class="{whale_col}">{eth_data['whale']} ({eth_data['vol_pct']:.0f}%)</span><br>
                    📈 <b>RSI (14):</b> <b style="color:{'#00ff00' if eth_data['rsi']<30 else '#ff4b4b' if eth_data['rsi']>70 else '#fff'}">{eth_data['rsi']:.2f}</b><br>
                    🎯 <b>AI Call:</b> {"LONG LOOK" if eth_data['rsi'] < 40 and "BULLISH" in eth_data['trend'] else "SHORT LOOK" if eth_data['rsi'] > 60 and "BEARISH" in eth_data['trend'] else "WAIT"}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.subheader("📈 LIVE CHART WITH INDICATORS")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{"width": "100%", "height": "600", "symbol": "BINANCE:BTCUSDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "en", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI", "STD;Stochastic"], "support_host": "https://www.tradingview.com"}</script></div>""", height=600)

    # TAB 2: MARKET DATA
    with tab2:
        st.subheader("🚀 TOP MOVERS")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>{"colorTheme": "dark", "dateRange": "12M", "exchange": "BINANCE", "showChart": true, "locale": "en", "largeChartUrl": "", "isTransparent": true, "showSymbolLogo": true, "width": "100%", "height": "500"}</script></div>""", height=500)
        st.subheader("📰 NEWS FEED")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>{"feedMode": "all_symbols", "colorTheme": "dark", "isTransparent": true, "displayMode": "regular", "width": "100%", "height": "500", "locale": "en"}</script></div>""", height=500)

    # TAB 3: ACADEMY
    with tab3:
        st.markdown("### 🎓 TRADING EDUCATION")
        c1, c2 = st.columns(2)
        with c1: st.markdown("""<div class="tool-card"><h4>📘 Technical Analysis</h4><p>Master candlestick patterns and support/resistance.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class="tool-card"><h4>🧠 Risk Psychology</h4><p>How to manage FOMO and stick to the plan.</p></div>""", unsafe_allow_html=True)

    # TAB 4: CALCULATORS
    with tab4:
        st.subheader("🧮 ROI SIMULATOR")
        caps = st.number_input("Capital ($)", 100, 100000, 1000)
        risk = st.slider("Risk (%)", 0.5, 5.0, 2.0)
        st.markdown(f"<div class='glass-box'>Potential: <b style='color:#66fcf1'>${caps * (1 + (risk/100)*10):,.2f}</b> (After 10 Wins)</div>", unsafe_allow_html=True)

    # TAB 5: VIP OFFICE
    with tab5:
        st.markdown("<h2 style='text-align:center; color:#fff;'>UPGRADE YOUR ACCESS</h2>", unsafe_allow_html=True)
        
        # INCLUDED TOOLS LİSTESİ
        st.markdown("""
        <div class="glass-box" style="text-align:left;">
            <h3 style="color:#00ff00;">🔥 INCLUDED PREMIUM INDICATORS (LIFETIME):</h3>
            <ul style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; color:#fff; list-style:none;">
                <li>✅ <b>Market Waves Pro</b> (Trend Finder)</li>
                <li>✅ <b>Market Core Pro</b> (Structure)</li>
                <li>✅ <b>Beluga Nautilus Pro</b> (Whale Vol)</li>
                <li>✅ <b>Ultimate MACD</b> Package</li>
                <li>✅ <b>Ultimate RSI</b> Package</li>
                <li>✅ <b>Premium Divergence</b> (Reversal)</li>
                <li>✅ <b>24/7</b> Support & Updates</li>
            </ul>
        </div><br>
        """, unsafe_allow_html=True)

        pc1, pc2, pc3 = st.columns(3)
        with pc1: st.markdown("""<div class="pricing-card"><h3>STARTER</h3><div style="font-size:2rem;color:#fff;">$30</div><p>/mo</p></div>""", unsafe_allow_html=True)
        with pc2: st.markdown("""<div class="pricing-card" style="border:1px solid #ffd700;"><h3>VIP</h3><div style="font-size:2rem;color:#fff;">$75</div><p>/qtr</p></div>""", unsafe_allow_html=True)
        with pc3: st.markdown("""<div class="pricing-card"><h3>LIFETIME</h3><div style="font-size:2rem;color:#fff;">$250</div><p>once</p></div>""", unsafe_allow_html=True)

        st.write("")
        
        # ÖDEME ALANI
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.expander("👤 SETTINGS", expanded=True):
                st.text_input("Username", value=ui.get('Username'), disabled=True)
                st.button("UPDATE PASSWORD")
                st.markdown("**Telegram:** [@Orhan1909](https://t.me/Orhan1909)")

        with c2:
            st.markdown("""
            <div class='payment-card'>
                <h3 style='color:#ffd700; margin-top:0;'>💳 PAYMENT DETAILS</h3>
                <div style='text-align:left; background:rgba(0,0,0,0.3); padding:10px; border-radius:5px; margin-bottom:5px;'><b>USDT (TRC20):</b><br><code style='color:#fff;'>TL8w... (YOUR_ADDR)</code></div>
                <div style='text-align:left; background:rgba(0,0,0,0.3); padding:10px; border-radius:5px; margin-bottom:5px;'><b>IBAN:</b><br><code style='color:#fff;'>TR12 0000... (YOUR_IBAN)</code></div>
            </div>
            """, unsafe_allow_html=True)
            sel = st.selectbox("Plan", ["Starter", "VIP", "Lifetime"])
            tx = st.text_input("TX ID")
            if st.button("CONFIRM PAYMENT"): st.success("Notification sent to Admin!")

    # KVKK
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("⚖️ LEGAL | KVKK & PRIVACY POLICY"):
        st.write("CRAZYTOWN CAPITAL Privacy Policy & KVKK Text...")

# ==========================================
# 5. START
# ==========================================
if st.session_state.logged_in: show_dashboard()
elif st.session_state.current_page == 'Home': show_home()
elif st.session_state.current_page == 'Register': show_auth("Register")
elif st.session_state.current_page == 'Login': show_auth("Login")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
