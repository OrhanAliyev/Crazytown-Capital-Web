import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
from datetime import datetime
import time

# ==========================================
# 1. AYARLAR VE CSS (V1400 STABLE)
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS STYLES
st.markdown("""
    <style>
        /* TEMEL AYARLAR */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 0rem; padding-bottom: 3rem; max-width: 100%;}
        .stApp {background-color: #0b0c10; background: radial-gradient(circle at center, #0f1115 0%, #000000 100%); color: #c5c6c7; font-family: 'Inter', sans-serif;}
        
        /* HABER BANDI */
        .ticker-wrap { width: 100%; background-color: #000; border-bottom: 1px solid #333; height: 30px; line-height: 30px; overflow: hidden; white-space: nowrap;}
        .ticker-item { display: inline-block; padding: 0 2rem; color: #66fcf1; font-weight: bold; font-size: 0.8rem; }
        
        /* KART TASARIMLARI */
        .tool-card {
            background: rgba(20, 25, 30, 0.9);
            border: 1px solid #333;
            border-left: 4px solid #66fcf1;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        .tool-title { font-size: 1.3rem; font-weight: bold; color: #fff; margin-bottom: 5px; display: flex; justify-content: space-between; }
        .sub-text { font-size: 0.9rem; color: #888; margin-bottom: 15px; }
        
        /* DETAY KUTUSU */
        .analysis-box {
            background: rgba(255,255,255,0.03);
            border-left: 4px solid #ffd700;
            padding: 15px;
            margin-top: 15px;
            border-radius: 5px;
        }
        .section-title { color: #66fcf1; font-weight: bold; font-size: 0.9rem; margin-top: 10px; display: block;}
        .text-content { color: #ccc; font-size: 0.9rem; margin: 3px 0; }
        
        /* TABLO */
        .strategy-table { width: 100%; margin-top: 5px; }
        .strategy-table td { padding: 5px; border-bottom: 1px solid #333; color: #ddd; font-size: 0.85rem; }
        
        /* INPUT VE BUTON */
        .stTextInput input { background-color: #15161a !important; color: white !important; border: 1px solid #333 !important; }
        .stButton button { background-color: #66fcf1 !important; color: black !important; font-weight: bold !important; width: 100%; border-radius: 5px; }
        
        /* RENKLER */
        .green { color: #00ff00; }
        .red { color: #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# HABER BANDI
st.markdown("""
<div class="ticker-wrap">
    <span class="ticker-item">BTC: $98,450 (+2.4%)</span>
    <span class="ticker-item">ETH: $3,200 (+1.1%)</span>
    <span class="ticker-item">SOL: $145 (-0.5%)</span>
    <span class="ticker-item">CRAZYTOWN CAPITAL SİSTEM AKTİF</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. VERİ MOTORU (SADE VE GÜÇLÜ)
# ==========================================

POPULAR = {
    'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'XRP': 'ripple', 
    'DOGE': 'dogecoin', 'AVAX': 'avalanche-2', 'PEPE': 'pepe', 'SHIB': 'shiba-inu'
}

@st.cache_data(ttl=60)
def get_coin_list():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/coins/list", timeout=3)
        return r.json() if r.status_code == 200 else []
    except: return []

@st.cache_data(ttl=20)
def get_market_data(coin_id):
    # CoinGecko
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?tickers=false&market_data=true&sparkline=true"
        r = requests.get(url, timeout=3)
        if r.status_code == 200: return r.json()
    except: pass
    return None

@st.cache_data(ttl=15)
def get_binance_price(symbol):
    # Binance Backup
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50"
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            df = pd.DataFrame(r.json(), columns=['t','o','h','l','c','v','x','x','x','x','x','x'])
            return df['c'].astype(float).tolist()
    except: return []
    return []

def calculate_indicators(prices):
    if not prices or len(prices) < 20: return 50, 0, 0
    s = pd.Series(prices)
    # RSI
    delta = s.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    # SMA
    sma7 = s.rolling(7).mean().iloc[-1]
    sma25 = s.rolling(25).mean().iloc[-1]
    return current_rsi, sma7, sma25

def analyze(query):
    query = query.upper().strip()
    coin_id = POPULAR.get(query)
    symbol = query
    
    # ID Bulma
    if not coin_id:
        lst = get_coin_list()
        for c in lst:
            if c['symbol'].upper() == query: coin_id = c['id']; break
    
    price_data = []
    current_price = 0
    change_24h = 0
    name = symbol
    
    # Veri Çekme
    if coin_id:
        data = get_market_data(coin_id)
        if data:
            md = data.get('market_data', {})
            current_price = md.get('current_price', {}).get('usd', 0)
            change_24h = md.get('price_change_percentage_24h', 0)
            price_data = md.get('sparkline_7d', {}).get('price', [])
            name = data.get('name')
            
    if not price_data:
        bp = get_binance_price(symbol)
        if bp:
            price_data = bp
            current_price = bp[-1]
            change_24h = ((bp[-1] - bp[0]) / bp[0]) * 100
    
    if not price_data: return None

    # Hesaplama
    rsi, sma7, sma25 = calculate_indicators(price_data)
    
    # Puanlama
    score = 50
    
    # Trend
    if sma7 > sma25: 
        trend = "BOĞA 🟢"; score += 20
        trend_msg = "Fiyat ortalamaların üzerinde, yön yukarı."
    else: 
        trend = "AYI 🔴"; score -= 20
        trend_msg = "Fiyat baskı altında, yön aşağı."
        
    # RSI
    if rsi < 30: 
        score += 30; rsi_msg = "Aşırı SATIM (Dip Sinyali)"
    elif rsi > 70: 
        score -= 30; rsi_msg = "Aşırı ALIM (Düzeltme Riski)"
    else: 
        if rsi > 50: score += 5
        else: score -= 5
        rsi_msg = "Nötr Bölge"
        
    # Beluga (Hacim)
    if abs(change_24h) > 5:
        beluga = "YÜKSEK 🐋"; score += 10 if change_24h > 0 else -10
    else:
        beluga = "NORMAL 🌊"
        
    score = max(0, min(100, score))
    
    # Karar
    if score >= 80: decision = "GÜÇLÜ AL 🚀"
    elif score >= 60: decision = "ALIM FIRSATI ✅"
    elif score <= 20: decision = "GÜÇLÜ SAT 📉"
    elif score <= 40: decision = "SATIŞ BASKISI 🔻"
    else: decision = "BEKLE ✋"
    
    # Strateji
    scalp = "AL" if rsi < 35 else "SAT" if rsi > 65 else "NÖTR"
    swing = "TUT" if sma7 > sma25 else "NAKİT"
    
    return {
        "name": name, "symbol": symbol, "price": current_price, "change": change_24h,
        "rsi": rsi, "trend": trend, "beluga": beluga, "score": score, "decision": decision,
        "trend_msg": trend_msg, "rsi_msg": rsi_msg, "scalp": scalp, "swing": swing,
        "supp": current_price*0.9, "res": current_price*1.1
    }

# ==========================================
# 3. SAYFALAR
# ==========================================
if 'auth' not in st.session_state: st.session_state.auth = False

def main_app():
    c1, c2 = st.columns([3,1])
    with c1: st.title("CRAZYTOWN CAPITAL PRO")
    with c2: 
        if st.button("ÇIKIŞ YAP"): st.session_state.auth = False; st.rerun()
    
    # ARAMA BÖLÜMÜ
    st.markdown("### ⚡ ANALİZ MOTORU")
    query = st.text_input("COIN ARA", placeholder="Örn: BTC, ETH, PEPE, RESOLV...")
    
    if query:
        with st.spinner("Veriler taranıyor..."):
            d = analyze(query)
        
        if d:
            # HTML GÖSTERİMİ (DÜZELTİLMİŞ)
            border_col = "#00ff00" if d['score'] >= 60 else "#ff4b4b" if d['score'] <= 40 else "#ffd700"
            
            st.markdown(f"""
            <div class="tool-card" style="border-left-color: {border_col};">
                <div class="tool-title">
                    <span>{d['name']} ({d['symbol']})</span>
                    <span>${d['price']:,.4f}</span>
                </div>
                <div style="color:{'#00ff00' if d['change']>0 else '#ff4b4b'}; margin-bottom:10px;">
                    24s Değişim: %{d['change']:.2f}
                </div>
                
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:15px;">
                    <div>
                        <span style="color:#888; font-size:0.8rem;">GENEL TREND</span><br>
                        <span style="font-weight:bold; font-size:1rem;">{d['trend']}</span>
                    </div>
                    <div>
                        <span style="color:#888; font-size:0.8rem;">BELUGA ENDEKSİ</span><br>
                        <span style="font-weight:bold; font-size:1rem; color:#66fcf1;">{d['beluga']}</span>
                    </div>
                    <div>
                        <span style="color:#888; font-size:0.8rem;">RSI (14)</span><br>
                        <span style="font-weight:bold; font-size:1rem; color:white;">{d['rsi']:.1f}</span>
                    </div>
                    <div>
                        <span style="color:#888; font-size:0.8rem;">GÜVEN SKORU</span><br>
                        <span style="font-weight:bold; font-size:1rem; color:{border_col};">{d['score']}/100</span>
                    </div>
                </div>
                
                <hr style="border-color:#333; margin:15px 0;">
                
                <div style="text-align:center;">
                    <span style="color:#888;">YAPAY ZEKA KARARI</span><br>
                    <span style="font-size:1.5rem; font-weight:bold; color:{border_col};">{d['decision']}</span>
                </div>
            </div>
            
            <div class="analysis-box">
                <span class="section-title">📋 CRAZYTOWN STRATEJİ RAPORU</span>
                
                <span class="section-title">⏱️ ZAMAN DİLİMİ ÖNERİLERİ:</span>
                <table class="strategy-table">
                    <tr><td>⚡ SCALP (15dk)</td><td style="color:#fff;">{d['scalp']}</td></tr>
                    <tr><td>🌊 SWING (Günlük)</td><td style="color:#fff;">{d['swing']}</td></tr>
                </table>
                
                <span class="section-title">🔍 TEKNİK DETAYLAR:</span>
                <p class="text-content">• {d['trend_msg']}</p>
                <p class="text-content">• {d['rsi_msg']}</p>
                
                <span class="section-title">🎯 HEDEF SEVİYELER:</span>
                <p class="text-content">🛡️ Destek (Giriş): <b style="color:white">${d['supp']:,.4f}</b></p>
                <p class="text-content">🚫 Direnç (Satış): <b style="color:white">${d['res']:,.4f}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            # GRAFİK
            st.write("")
            components.html(f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{{"width": "100%", "height": "500", "symbol": "BINANCE:{d['symbol']}USDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI"], "support_host": "https://www.tradingview.com"}}</script></div>""", height=500)
            
        else:
            st.error("Veri bulunamadı. Lütfen coinin ismini doğru yazdığınızdan emin olun.")

def login_page():
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><h2 style='text-align:center;'>GİRİŞ YAP</h2>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("GİRİŞ"):
            st.session_state.auth = True; st.session_state.user_info = {"Name": u}; st.rerun()

# ROUTER
if st.session_state.auth: main_app()
else: login_page()
