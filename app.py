import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
from datetime import datetime
import time
import random

# ==========================================
# 1. AYARLAR VE CSS
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Canlı Terminal",
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

        /* DİĞERLERİ */
        .stTextInput input { background-color: #15161a !important; color: #fff !important; border: 1px solid #2d3845 !important; border-radius: 5px !important; }
        .stButton button { background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100% !important; padding: 12px !important; transition: all 0.3s ease; }
        .stButton button:hover { background-color: #fff !important; box-shadow: 0 0 15px #66fcf1; transform: translateY(-2px); }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
        .stTabs [data-baseweb="tab"] { height: 50px; color: #888; font-weight: 600; border: none; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important; background: rgba(102,252,241,0.05); }
        
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 2. GERÇEK VERİ MOTORU (MULTI-SOURCE)
# ==========================================

@st.cache_data(ttl=10)
def get_live_market_data(symbol='BTC'):
    # 1. YÖNTEM: BINANCE
    try:
        pair = f"{symbol}USDT"
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1h&limit=50"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'q_vol', 'num_trades', 'tb_base_vol', 'tb_quote_vol', 'ignore'])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df
    except: pass

    # 2. YÖNTEM: KRAKEN (YEDEK)
    try:
        pair_map = {'BTC': 'XBTUSD', 'ETH': 'ETHUSD', 'SOL': 'SOLUSD'}
        pair = pair_map.get(symbol, 'XBTUSD')
        url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=60"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            result_key = list(data['result'].keys())[0]
            ohlc = data['result'][result_key]
            df = pd.DataFrame(ohlc, columns=['timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df.tail(50)
    except: pass

    # 3. YÖNTEM: COINBASE (SON ÇARE)
    try:
        pair = f"{symbol}-USD"
        url = f"https://api.exchange.coinbase.com/products/{pair}/candles?granularity=3600"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=2)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data, columns=['timestamp', 'low', 'high', 'open', 'close', 'volume'])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df.iloc[::-1].tail(50)
    except: return pd.DataFrame()

    return pd.DataFrame()

# Teknik Analiz Hesaplama
def calculate_signals(df):
    if df.empty: return 50, 0, 0, 0
    closes = df['close']
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    sma_short = closes.rolling(window=7).mean().iloc[-1]
    sma_long = closes.rolling(window=25).mean().iloc[-1]
    current_vol = df['volume'].iloc[-1]
    avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
    vol_spike = (current_vol / avg_vol) * 100 if avg_vol > 0 else 0
    return current_rsi, sma_short, sma_long, vol_spike

# Sinyal Oluşturucu (TÜRKÇE)
def generate_pro_signals(symbol):
    df = get_live_market_data(symbol)
    if df.empty:
        return {"price": 0, "rsi": 50, "trend": "BEKLENİYOR...", "whale": "TARANIYOR...", "vol_pct": 0}
    
    rsi, sma_s, sma_l, vol = calculate_signals(df)
    current_price = df['close'].iloc[-1]
    
    # KARAR MEKANİZMASI (TÜRKÇE)
    if sma_s > sma_l: trend = "BOĞA DALGASI 🟢" # Bullish
    else: trend = "AYI DALGASI 🔴" # Bearish
    
    whale_alert = "YÜKSEK 🐋" if vol > 130 else "NORMAL 🌊"
    
    return {
        "price": current_price,
        "rsi": rsi,
        "trend": trend,
        "whale": whale_alert,
        "vol_pct": vol
    }

# ==========================================
# 3. KULLANICI SİSTEMİ
# ==========================================
def register_user(username, password, name):
    return "Success" # Demo

def login_user(username, password):
    return {"Name": "Trader", "Plan": "Free"} # Demo

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'current_page' not in st.session_state: st.session_state.current_page = 'Home'

def go_to(page): st.session_state.current_page = page; st.rerun()

# --- SAYFALAR ---
def show_home():
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=50)
    st.markdown('<div class="hero-title">CRAZYTOWN CAPITAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">YAPAY ZEKA DESTEKLİ TİCARET TERMİNALİ</div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2: 
        if st.button("🚀 GİRİŞ YAP"): go_to("Login")
    with c4: 
        if st.button("💎 KAYIT OL"): go_to("Register")

    st.write("")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="glass-box"><h3>⚡ Market Waves Pro</h3><p>Gerçek Zamanlı Trend Takibi & RSI Analizi</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="glass-box"><h3>🐋 Beluga Nautilus</h3><p>Canlı Balina Hacim Takip Sistemi</p></div>""", unsafe_allow_html=True)

    st.markdown("<br><h3 style='text-align:center; color:#fff;'>ÜYELİK PAKETLERİ</h3>", unsafe_allow_html=True)
    pc1, pc2, pc3 = st.columns(3)
    with pc1: st.markdown("""<div class="pricing-card"><h3>BAŞLANGIÇ</h3><div style="font-size:2rem;color:#fff;">$30</div><p>/ay</p></div>""", unsafe_allow_html=True)
    with pc2: st.markdown("""<div class="pricing-card" style="border:1px solid #66fcf1;"><h3>VIP</h3><div style="font-size:2rem;color:#fff;">$75</div><p>/çeyrek</p></div>""", unsafe_allow_html=True)
    with pc3: st.markdown("""<div class="pricing-card"><h3>ÖMÜR BOYU</h3><div style="font-size:2rem;color:#fff;">$250</div><p>tek sefer</p></div>""", unsafe_allow_html=True)

def show_auth(mode):
    # Başlıkları Türkçeleştir
    title = "KAYIT OL" if mode == "Register" else "GİRİŞ YAP"
    st.markdown(f'<div class="hero-title" style="font-size:2.5rem;">{title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("auth"):
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if mode == "Register": n = st.text_input("Ad Soyad")
        if st.form_submit_button("ONAYLA"):
            if mode == "Register":
                st.success("Hesap Oluşturuldu! Giriş yapabilirsiniz.")
                time.sleep(1); go_to("Login")
            else:
                if u == "admin" and p == "password123":
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"Name": "Orhan Aliyev", "Plan": "ADMIN"}
                    st.rerun()
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"Name": u, "Plan": "Free"}
                    st.success("Hoşgeldiniz"); time.sleep(1); st.rerun()
    if st.button("Ana Sayfaya Dön"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD ---
def show_dashboard():
    # Canlı Verileri Çek
    btc_data = generate_pro_signals('BTC')
    eth_data = generate_pro_signals('ETH')
    ui = st.session_state.user_info
    
    st.markdown(f"""
    <div class="status-bar">
        <span><span style="height:8px;width:8px;background:#00ff00;border-radius:50%;display:inline-block;"></span> <b>SİSTEM AKTİF</b></span>
        <span>|</span>
        <span>VERİ: <b>CANLI (MULTI-SOURCE)</b></span>
        <span>|</span>
        <span>KULLANICI: <b>{ui.get('Name')}</b></span>
    </div>
    """, unsafe_allow_html=True)

    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=50)

    st.write("")
    if st.button("🔒 ÇIKIŞ YAP"): st.session_state.logged_in = False; go_to("Home")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ PRO ARAÇLAR", "📊 PİYASA VERİLERİ", "🎓 AKADEMİ", "🧮 HESAP MAKİNESİ", "👑 VIP OFİS"])
    
    # TAB 1: PRO ARAÇLAR
    with tab1:
        st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;"><h3 style="margin:0;">⚡ CANLI ALGORİTMİK SİNYALLER</h3><span style="color:#888;">Güncelleme: {datetime.now().strftime('%H:%M:%S')}</span></div>""", unsafe_allow_html=True)
        if st.button("🔄 SİNYALLERİ YENİLE"): st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            trend_col = "status-bullish" if "BOĞA" in btc_data['trend'] else "status-bearish" if "AYI" in btc_data['trend'] else "status-neutral"
            whale_col = "status-bullish" if "YÜKSEK" in btc_data['whale'] else "status-neutral"
            
            # AI Karar Mantığı (Türkçe)
            if btc_data['rsi'] < 40 and "BOĞA" in btc_data['trend']: ai_call = "LONG FIRSATI 🚀"
            elif btc_data['rsi'] > 60 and "AYI" in btc_data['trend']: ai_call = "SHORT FIRSATI 📉"
            else: ai_call = "BEKLE ✋"

            st.markdown(f"""
            <div class="tool-card" style="border-left-color: #f2a900;">
                <div class="tool-title">BITCOIN (BTC) <span style="font-size:0.9rem;">${btc_data['price']:,.2f}</span></div>
                <hr style="border-color:rgba(255,255,255,0.1);">
                <p style="color:#ccc; font-size:0.9rem; line-height:1.8;">
                    🌊 <b>Piyasa Dalgaları:</b> <span class="{trend_col}">{btc_data['trend']}</span><br>
                    🐋 <b>Beluga Hacmi:</b> <span class="{whale_col}">{btc_data['whale']} (%{btc_data['vol_pct']:.0f})</span><br>
                    📈 <b>RSI (14):</b> <b style="color:{'#00ff00' if btc_data['rsi']<30 else '#ff4b4b' if btc_data['rsi']>70 else '#fff'}">{btc_data['rsi']:.2f}</b><br>
                    🎯 <b>Yapay Zeka Çağrısı:</b> {ai_call}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            trend_col = "status-bullish" if "BOĞA" in eth_data['trend'] else "status-bearish" if "AYI" in eth_data['trend'] else "status-neutral"
            whale_col = "status-bullish" if "YÜKSEK" in eth_data['whale'] else "status-neutral"
            
            if eth_data['rsi'] < 40 and "BOĞA" in eth_data['trend']: ai_call_eth = "LONG FIRSATI 🚀"
            elif eth_data['rsi'] > 60 and "AYI" in eth_data['trend']: ai_call_eth = "SHORT FIRSATI 📉"
            else: ai_call_eth = "BEKLE ✋"

            st.markdown(f"""
            <div class="tool-card" style="border-left-color: #627eea;">
                <div class="tool-title">ETHEREUM (ETH) <span style="font-size:0.9rem;">${eth_data['price']:,.2f}</span></div>
                <hr style="border-color:rgba(255,255,255,0.1);">
                <p style="color:#ccc; font-size:0.9rem; line-height:1.8;">
                    🌊 <b>Piyasa Dalgaları:</b> <span class="{trend_col}">{eth_data['trend']}</span><br>
                    🐋 <b>Beluga Hacmi:</b> <span class="{whale_col}">{eth_data['whale']} (%{eth_data['vol_pct']:.0f})</span><br>
                    📈 <b>RSI (14):</b> <b style="color:{'#00ff00' if eth_data['rsi']<30 else '#ff4b4b' if eth_data['rsi']>70 else '#fff'}">{eth_data['rsi']:.2f}</b><br>
                    🎯 <b>Yapay Zeka Çağrısı:</b> {ai_call_eth}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.subheader("📈 CANLI GRAFİK")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{"width": "100%", "height": "600", "symbol": "BINANCE:BTCUSDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI", "STD;Stochastic"], "support_host": "https://www.tradingview.com"}</script></div>""", height=600)

    # TAB 2: PİYASA VERİLERİ
    with tab2:
        st.subheader("🚀 YÜKSELENLER & DÜŞENLER")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>{"colorTheme": "dark", "dateRange": "12M", "exchange": "BINANCE", "showChart": true, "locale": "tr", "largeChartUrl": "", "isTransparent": true, "showSymbolLogo": true, "width": "100%", "height": "500"}</script></div>""", height=500)
        st.subheader("📰 HABER AKIŞI")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>{"feedMode": "all_symbols", "colorTheme": "dark", "isTransparent": true, "displayMode": "regular", "width": "100%", "height": "500", "locale": "tr"}</script></div>""", height=500)

    # TAB 3: AKADEMİ
    with tab3:
        st.markdown("### 🎓 YATIRIM EĞİTİMİ")
        c1, c2 = st.columns(2)
        with c1: st.markdown("""<div class="tool-card"><h4>📘 Teknik Analiz 101</h4><p>Mum formasyonları ve destek/direnç öğrenin.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class="tool-card"><h4>🧠 Risk Psikolojisi</h4><p>FOMO yönetimi ve disiplinli işlem stratejileri.</p></div>""", unsafe_allow_html=True)

    # TAB 4: HESAP MAKİNESİ
    with tab4:
        st.subheader("🧮 ROI SİMÜLATÖRÜ")
        caps = st.number_input("Başlangıç Sermayesi ($)", 100, 100000, 1000)
        risk = st.slider("İşlem Başı Risk (%)", 0.5, 5.0, 2.0)
        st.markdown(f"<div class='glass-box'>Potansiyel Bakiye: <b style='color:#66fcf1'>${caps * (1 + (risk/100)*10):,.2f}</b> (10 Başarılı İşlem Sonrası)</div>", unsafe_allow_html=True)

    # TAB 5: VIP OFİS
    with tab5:
        st.markdown("<h2 style='text-align:center; color:#fff;'>ÜYELİĞİNİZİ YÜKSELTİN</h2>", unsafe_allow_html=True)
        st.markdown("""<div class="glass-box" style="text-align:left;"><h3 style="color:#00ff00;">🔥 ÖMÜR BOYU PAKET İÇERİĞİ:</h3><ul style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; color:#fff; list-style:none;"><li>✅ <b>Market Waves Pro</b> (Trend Takipçisi)</li><li>✅ <b>Market Core Pro</b> (Piyasa Yapısı)</li><li>✅ <b>Beluga Nautilus Pro</b> (Balina Hacmi)</li><li>✅ <b>Ultimate MACD</b> Paketi</li><li>✅ <b>Ultimate RSI</b> Paketi</li><li>✅ <b>Premium Uyumsuzluk</b> (Divergence)</li><li>✅ <b>7/24</b> Destek & Güncellemeler</li></ul></div><br>""", unsafe_allow_html=True)

        pc1, pc2, pc3 = st.columns(3)
        with pc1: st.markdown("""<div class="pricing-card"><h3>BAŞLANGIÇ</h3><div style="font-size:2rem;color:#fff;">$30</div><p>/ay</p></div>""", unsafe_allow_html=True)
        with pc2: st.markdown("""<div class="pricing-card" style="border:1px solid #ffd700;"><h3>VIP</h3><div style="font-size:2rem;color:#fff;">$75</div><p>/çeyrek</p></div>""", unsafe_allow_html=True)
        with pc3: st.markdown("""<div class="pricing-card"><h3>ÖMÜR BOYU</h3><div style="font-size:2rem;color:#fff;">$250</div><p>tek sefer</p></div>""", unsafe_allow_html=True)

        st.write("")
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.expander("👤 AYARLAR", expanded=True):
                st.text_input("Kullanıcı Adı", value=ui.get('Username'), disabled=True)
                st.button("ŞİFRE GÜNCELLE")
                st.markdown("**Telegram:** [@Orhan1909](https://t.me/Orhan1909)")

        with c2:
            st.markdown("""<div class='payment-card'><h3 style='color:#ffd700; margin-top:0;'>💳 ÖDEME BİLGİLERİ</h3><div style='text-align:left; background:rgba(0,0,0,0.3); padding:10px; border-radius:5px; margin-bottom:5px;'><b>USDT (TRC20):</b><br><code style='color:#fff;'>TL8w... (SENİN_ADRESİN)</code></div><div style='text-align:left; background:rgba(0,0,0,0.3); padding:10px; border-radius:5px; margin-bottom:5px;'><b>IBAN (Banka):</b><br><code style='color:#fff;'>TR12 0000... (SENİN_IBANIN)</code></div></div>""", unsafe_allow_html=True)
            sel = st.selectbox("Paket Seçimi", ["Başlangıç", "VIP", "Ömür Boyu"])
            tx = st.text_input("İşlem ID (Hash)")
            if st.button("ÖDEMEYİ ONAYLA"): st.success("Bildirim Admin'e iletildi!")

    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("⚖️ YASAL | KVKK & GİZLİLİK POLİTİKASI"):
        st.markdown("### KİŞİSEL VERİLERİN KORUNMASI KANUNU (KVKK) AYDINLATMA METNİ\nCRAZYTOWN CAPITAL olarak...")

# ==========================================
# 5. BAŞLAT
# ==========================================
if st.session_state.logged_in: show_dashboard()
elif st.session_state.current_page == 'Home': show_home()
elif st.session_state.current_page == 'Register': show_auth("Register")
elif st.session_state.current_page == 'Login': show_auth("Login")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
