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
    page_title="Crazytown Capital | Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 0rem; padding-bottom: 3rem; max-width: 100%; z-index: 2; position: relative;}
        .stApp {background-color: #0b0c10; background: radial-gradient(circle at center, #0f1115 0%, #000000 100%); color: #c5c6c7; font-family: 'Inter', sans-serif;}
        
        .ticker-wrap { width: 100%; overflow: hidden; background-color: #000; border-bottom: 1px solid #333; height: 30px; line-height: 30px; position: fixed; top: 0; left: 0; z-index: 9999; }
        .ticker { display: inline-block; white-space: nowrap; animation: ticker 40s linear infinite; }
        .ticker-item { display: inline-block; padding: 0 2rem; color: #66fcf1; font-size: 0.8rem; font-weight: bold; }
        @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

        .glass-box, .metric-container, .pricing-card, .login-container, .tool-card, .payment-card, .analysis-box {
            background: rgba(20, 25, 30, 0.85) !important; backdrop-filter: blur(15px); border: 1px solid rgba(102, 252, 241, 0.2); border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5); margin-bottom: 20px;
        }
        
        .tool-card { text-align: left; border-left: 4px solid #66fcf1; transition: transform 0.3s ease; position:relative; overflow:hidden;}
        .tool-card:hover { transform: translateX(5px); border-color: #ffd700; }
        .tool-title { font-weight: bold; color: #fff; font-size: 1.2rem; display: flex; justify-content: space-between; align-items:center; }
        
        .analysis-box { text-align: left; background: rgba(255,255,255,0.03) !important; border-left: 4px solid #ffd700; margin-top: 15px; padding: 25px; }
        .analysis-section { margin-bottom: 15px; }
        .analysis-label { color: #66fcf1; font-weight: bold; font-size: 0.9rem; }
        .analysis-text { color: #ddd; font-size: 0.95rem; line-height: 1.6; margin-top: 5px; }
        
        .strategy-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .strategy-table td { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #ccc; font-size: 0.9rem; }
        .strategy-tag { padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }

        .status-bullish { color: #00ff00; background: rgba(0,255,0,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight:bold;}
        .status-bearish { color: #ff4b4b; background: rgba(255,75,75,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight:bold;}
        .status-neutral { color: #ccc; background: rgba(200,200,200,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight:bold;}

        .stTextInput input { background-color: #15161a !important; color: #fff !important; border: 1px solid #2d3845 !important; border-radius: 5px !important; }
        .stButton button { background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100% !important; padding: 12px !important; transition: all 0.3s ease; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; margin-top: 20px;}
        .stTabs [data-baseweb="tab"] { height: 50px; color: #888; font-weight: 600; border: none; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important; background: rgba(102,252,241,0.05); }
        
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""<div class="ticker-wrap"><div class="ticker"><span class="ticker-item">BTC: $98,450 (+2.4%)</span><span class="ticker-item">ETH: $3,200 (+1.1%)</span><span class="ticker-item">CRAZYTOWN CAPITAL V13.2 SİSTEM AKTİF</span></div></div>""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR
# ==========================================
POPULAR_COINS = {'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'XRP': 'ripple', 'DOGE': 'dogecoin', 'AVAX': 'avalanche-2', 'PEPE': 'pepe'}

@st.cache_data(ttl=60)
def get_all_coins_list():
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/coins/list", timeout=3)
        if resp.status_code == 200: return resp.json()
    except: pass
    return []

@st.cache_data(ttl=15)
def get_binance_data(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            df = pd.DataFrame(data, columns=['t', 'o', 'h', 'l', 'c', 'v', 'ct', 'qv', 'nt', 'tbv', 'tqv', 'ig'])
            return df['c'].astype(float).tolist()
    except: pass
    return []

@st.cache_data(ttl=30)
def get_coingecko_data(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=true"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200: return resp.json()
    except: pass
    return None

def calculate_technical_analysis(prices):
    if not prices or len(prices) < 20: return 50, 0, 0
    try:
        s = pd.Series(prices)
        delta = s.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        sma_short = s.rolling(7).mean().iloc[-1]
        sma_long = s.rolling(25).mean().iloc[-1]
        return current_rsi, sma_short, sma_long
    except: return 50, 0, 0

def analyze_any_coin(search_term):
    search_term = search_term.upper().strip()
    coin_id = None
    symbol = search_term
    
    if search_term in POPULAR_COINS: coin_id = POPULAR_COINS[search_term]
    
    if not coin_id:
        all_coins = get_all_coins_list()
        for c in all_coins:
            if c['symbol'].upper() == search_term: coin_id = c['id']; symbol = c['symbol'].upper(); break
    
    if search_term == 'BTC': coin_id = 'bitcoin'
    if search_term == 'ETH': coin_id = 'ethereum'
    
    price_data = []
    current_price = 0
    change_24h = 0
    name = symbol
    source = "Bilinmiyor"

    if coin_id:
        cg_data = get_coingecko_data(coin_id)
        if cg_data:
            try:
                md = cg_data.get('market_data', {})
                current_price = md.get('current_price', {}).get('usd', 0)
                change_24h = md.get('price_change_percentage_24h', 0)
                price_data = md.get('sparkline_7d', {}).get('price', [])
                name = cg_data.get('name')
                source = "CoinGecko"
            except: pass

    if not price_data:
        bin_data = get_binance_data(symbol)
        if bin_data:
            price_data = bin_data
            current_price = price_data[-1]
            try: change_24h = ((current_price - price_data[0])/price_data[0])*100
            except: change_24h = 0
            source = "Binance"

    if not price_data: return None

    rsi, sma_s, sma_l = calculate_technical_analysis(price_data)
    score = 50
    trend_bullish = False
    
    # Trend
    if sma_s > sma_l: 
        trend = "BOĞA 🟢"
        trend_bullish = True
        trend_desc = "Fiyat ortalamaların üzerinde, yön yukarı."
        score += 20
    else: 
        trend = "AYI 🔴"
        trend_desc = "Fiyat baskı altında, yön aşağı."
        score -= 20

    # RSI
    if rsi < 30: score += 30; rsi_desc = "Aşırı Satım (Dip)"
    elif rsi > 70: score -= 30; rsi_desc = "Aşırı Alım (Tepe)"
    else: 
        rsi_desc = "Nötr"
        if rsi > 50: score += 5
        else: score -= 5

    # BELUGA (Hacim/Momentum)
    if abs(change_24h) > 5:
        beluga_status = "YÜKSEK 🐋"
        beluga_col = "status-bullish"
        if change_24h > 0: score += 15
        else: score -= 15
    else:
        beluga_status = "NORMAL 🌊"
        beluga_col = "status-neutral"

    score = max(0, min(100, score))
    
    if score >= 80: decision = "GÜÇLÜ AL 🚀"
    elif score >= 60: decision = "ALIM FIRSATI ✅"
    elif score <= 20: decision = "GÜÇLÜ SAT 📉"
    elif score <= 40: decision = "SATIŞ BASKISI 🔻"
    else: decision = "BEKLE ✋"

    support = current_price * 0.90
    resistance = current_price * 1.10
    
    # Zaman Dilimi
    scalp = "AL ✅" if rsi < 35 else "SAT 🔻" if rsi > 65 else "NÖTR"
    swing = "TUT 🟢" if trend_bullish else "NAKİT 🔴"
    hold = "EKLE 🧺" if score > 60 else "KORU 🛡️"

    return {
        "name": name, "symbol": symbol, "price": current_price, "change_24h": change_24h,
        "rsi": rsi, "trend": trend, "score": score, "decision": decision,
        "support": support, "resistance": resistance,
        "scalp": scalp, "swing": swing, "hold": hold, "source": source,
        "beluga": beluga_status, "beluga_col": beluga_col,
        "trend_desc": trend_desc, "rsi_desc": rsi_desc
    }

# ==========================================
# 3. ARAYÜZ
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'current_page' not in st.session_state: st.session_state.current_page = 'Home'

def go_to(page): st.session_state.current_page = page; st.rerun()

def show_home():
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=50)
    st.markdown('<div class="hero-title" style="margin-top:20px;">CRAZYTOWN CAPITAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">EVRENSEL KRİPTO ANALİZ TERMİNALİ</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2: 
        if st.button("🚀 GİRİŞ YAP"): go_to("Login")
    with c4: 
        if st.button("💎 KAYIT OL"): go_to("Register")
    st.write("")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="glass-box"><h3>⚡ Market Waves Pro</h3><p>Tüm Coinler İçin Yapay Zeka Analizi</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="glass-box"><h3>🐋 Detaylı Raporlama</h3><p>Destek, Direnç ve Zaman Dilimi Stratejileri</p></div>""", unsafe_allow_html=True)

def show_auth(mode):
    st.markdown(f'<div class="hero-title" style="font-size:2.5rem;">{mode}</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("auth"):
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.form_submit_button("ONAYLA"):
            if u == "admin" and p == "password123":
                st.session_state.logged_in = True; st.session_state.user_info = {"Name": "Orhan Aliyev", "Plan": "ADMIN"}; st.rerun()
            else:
                st.session_state.logged_in = True; st.session_state.user_info = {"Name": u, "Plan": "Free"}; st.success("Hoşgeldiniz"); time.sleep(1); st.rerun()
    if st.button("Ana Sayfa"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard():
    ui = st.session_state.user_info
    st.markdown(f"""<div class="status-bar"><span><b>SİSTEM AKTİF</b></span> | <span>USER: <b>{ui.get('Name')}</b></span></div>""", unsafe_allow_html=True)
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=50)
    
    if st.button("🔒 ÇIKIŞ"): st.session_state.logged_in = False; go_to("Home")

    tab1, tab2, tab3 = st.tabs(["⚡ ANALİZ", "📊 PİYASA", "🎓 AKADEMİ"])
    
    with tab1:
        st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;"><h3 style="margin:0;">⚡ EVRENSEL COIN TARAYICISI</h3></div>""", unsafe_allow_html=True)
        search_query = st.text_input("COIN ARA", placeholder="Örn: Resolv, BTC...").strip()
        
        if search_query:
            with st.spinner("Analiz ediliyor..."):
                data = analyze_any_coin(search_query)
            
            if data:
                border = "#00ff00" if data['score']>=60 else "#ff4b4b" if data['score']<=40 else "#ffd700"
                
                # HTML GİRİNTİSİZ - DÜZELTİLDİ
                st.markdown(f"""
<div class="tool-card" style="border-left-color: {border}; border-width: 0 0 0 6px;">
<div class="tool-title">
<span>{data['name']} ({data['symbol']})</span>
<span style="font-size:1.5rem;">${data['price']:,.4f}</span>
</div>
<span style="color:{'#00ff00' if data['change_24h']>0 else '#ff4b4b'}; font-size:0.9rem;">24s Değişim: %{data['change_24h']:.2f}</span>
<hr style="border-color:rgba(255,255,255,0.1);">
<div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
<div><p style="color:#ccc; margin:0; font-size:0.8rem;">Genel Trend</p><span class="status-bullish" style="color:{'#00ff00' if 'BOĞA' in data['trend'] else '#ff4b4b'}">{data['trend']}</span></div>
<div><p style="color:#ccc; margin:0; font-size:0.8rem;">Beluga Balina Endeksi</p><span class="{data['beluga_col']}">{data['beluga']}</span></div>
<div><p style="color:#ccc; margin:0; font-size:0.8rem;">RSI Göstergesi</p><b style="color:#fff;">{data['rsi']:.2f}</b></div>
<div><p style="color:#ccc; margin:0; font-size:0.8rem;">Destek (Giriş)</p><b style="color:#fff;">${data['support']:,.4f}</b></div>
</div>
<br>
<p style="color:#ccc; margin:0; font-size:0.8rem;">Güven Skoru: {data['score']}/100</p>
<div style="background:#333; height:8px; width:100%; border-radius:5px; margin-bottom:10px;">
<div style="background:linear-gradient(90deg, #ff4b4b, #ffd700, #00ff00); height:100%; width:{data['score']}%; border-radius:5px;"></div>
</div>
<div style="text-align:center; margin-top:10px;"><span style="color:#fff; font-weight:bold; font-size:1.3rem;">KARAR: <span style="color:{border}">{data['decision']}</span></span></div>
</div>
""", unsafe_allow_html=True)

                st.write("")
                st.markdown("<div class='analysis-box'>", unsafe_allow_html=True)
                st.markdown("<span class='analysis-header'>📋 CRAZYTOWN INSTITUTIONAL RAPORU</span>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="analysis-section">
                    <span class="analysis-label">⏱️ ZAMAN DİLİMİ STRATEJİSİ:</span>
                    <table class="strategy-table">
                        <tr><td>⚡ SCALP (15dk)</td><td><span class="strategy-tag">{data['scalp']}</span></td></tr>
                        <tr><td>🌊 SWING (Günlük)</td><td><span class="strategy-tag">{data['swing']}</span></td></tr>
                        <tr><td>🏰 HOLD (Uzun)</td><td><span class="strategy-tag">{data['hold']}</span></td></tr>
                    </table>
                </div>
                <div class="analysis-section">
                    <span class="analysis-label">🔍 NEDENLER:</span>
                    <p class="analysis-text">• {data['trend_desc']}</p>
                    <p class="analysis-text">• {data['rsi_desc']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.write("")
                components.html(f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{{"width": "100%", "height": "500", "symbol": "BINANCE:{data['symbol']}USDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI"], "support_host": "https://www.tradingview.com"}}</script></div>""", height=500)
            else:
                st.error("Veri alınamadı. Lütfen tekrar deneyin.")

    with tab2:
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>{"colorTheme": "dark", "dateRange": "12M", "exchange": "BINANCE", "showChart": true, "locale": "tr", "largeChartUrl": "", "isTransparent": true, "showSymbolLogo": true, "width": "100%", "height": "500"}</script></div>""", height=500)

if st.session_state.logged_in: show_dashboard()
elif st.session_state.current_page == 'Home': show_home()
elif st.session_state.current_page == 'Register': show_auth("Register")
elif st.session_state.current_page == 'Login': show_auth("Login")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #45a29e; font-size: 0.8rem;'>© 2025 Crazytown Capital.</p>", unsafe_allow_html=True)
