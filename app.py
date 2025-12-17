import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests

# ==========================================
# 1. AYARLAR
# ==========================================
st.set_page_config(page_title="Crazytown Pro", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. CSS TASARIMI (GÖRSEL DÜZELTMELER YAPILDI)
# ==========================================
st.markdown("""
    <style>
    .stApp {background-color: #0b0c10; color: #c5c6c7;}
    div[class^="viewerBadge_container"], header, footer {display: none;}
    
    /* KART TASARIMI */
    .metric-card {
        background: rgba(30, 30, 35, 0.9);
        border: 1px solid #333;
        border-left: 5px solid #66fcf1;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .card-header { font-size: 1.5rem; font-weight: bold; color: white; display: flex; justify-content: space-between; }
    .card-sub { font-size: 1rem; color: #888; margin-bottom: 15px; }
    
    /* ANALİZ KUTUSU */
    .analysis-box {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #ffd700;
        padding: 15px;
        border-radius: 5px;
        margin-top: 15px;
    }
    .section-head { color: #ffd700; font-weight: bold; font-size: 1.1rem; border-bottom: 1px solid #444; padding-bottom: 5px; margin-bottom: 10px; }
    .strategy-row { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding: 5px 0; color: #ddd; }
    
    /* RENKLER */
    .bullish { color: #00ff00; font-weight: bold; }
    .bearish { color: #ff4b4b; font-weight: bold; }
    .neutral { color: #ccc; font-weight: bold; }
    
    /* INPUT */
    .stTextInput input { background-color: #15161a !important; color: white !important; border: 1px solid #333 !important; }
    .stButton button { background-color: #66fcf1 !important; color: black !important; font-weight: bold !important; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. VERİ MOTORU (SADELEŞTİRİLMİŞ)
# ==========================================
def get_crypto_data(symbol):
    symbol = symbol.upper().strip()
    
    # 1. Binance'den Fiyat Geçmişi Çek (En Sağlam Yöntem)
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50"
        r = requests.get(url, timeout=3)
        if r.status_code != 200: return None
        
        data = r.json()
        df = pd.DataFrame(data, columns=['t','o','h','l','c','v','x','x','x','x','x','x'])
        closes = df['c'].astype(float).tolist()
        volumes = df['v'].astype(float).tolist()
        
        current_price = closes[-1]
        prev_price = closes[0]
        change_24h = ((current_price - prev_price) / prev_price) * 100
        
        return {
            "symbol": symbol,
            "price": current_price,
            "change": change_24h,
            "closes": closes,
            "volumes": volumes
        }
    except:
        return None

def analyze_data(data):
    closes = data['closes']
    volumes = data['volumes']
    price = data['price']
    
    # İndikatör Hesapları (Manuel)
    s = pd.Series(closes)
    
    # RSI
    delta = s.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    # SMA (Trend)
    sma7 = s.rolling(7).mean().iloc[-1]
    sma25 = s.rolling(25).mean().iloc[-1]
    
    # Beluga (Hacim)
    curr_vol = volumes[-1]
    avg_vol = sum(volumes[-20:]) / 20
    vol_ratio = (curr_vol / avg_vol) * 100 if avg_vol > 0 else 0
    
    # --- KARAR MEKANİZMASI ---
    score = 50
    reasons = []
    
    # 1. Trend
    if sma7 > sma25: 
        trend = "BOĞA (YÜKSELİŞ) 🟢"
        score += 20
        reasons.append("Fiyat ortalamaların üzerinde.")
    else: 
        trend = "AYI (DÜŞÜŞ) 🔴"
        score -= 20
        reasons.append("Fiyat baskı altında.")
        
    # 2. RSI
    if current_rsi < 30: 
        score += 25; rsi_text = "Aşırı SATIM (Dip Sinyali)"
    elif current_rsi > 70: 
        score -= 25; rsi_text = "Aşırı ALIM (Tepe Sinyali)"
    else: 
        rsi_text = "Nötr Bölge"
        
    # 3. Beluga
    if vol_ratio > 150: 
        beluga = "YÜKSEK (BALİNA) 🐋"
        score += 10
    else: 
        beluga = "NORMAL 🌊"
        
    score = max(0, min(100, score))
    
    # Nihai Karar
    if score >= 75: decision = "GÜÇLÜ AL 🚀"
    elif score >= 60: decision = "ALIM FIRSATI ✅"
    elif score <= 25: decision = "GÜÇLÜ SAT 📉"
    elif score <= 40: decision = "SATIŞ BASKISI 🔻"
    else: decision = "BEKLE ✋"
    
    # Strateji
    scalp = "AL" if current_rsi < 35 else "SAT" if current_rsi > 65 else "NÖTR"
    swing = "TUT" if sma7 > sma25 else "NAKİT"
    
    return {
        "symbol": data['symbol'], "price": price, "change": data['change'],
        "rsi": current_rsi, "trend": trend, "beluga": beluga,
        "score": score, "decision": decision, "rsi_text": rsi_text,
        "scalp": scalp, "swing": swing,
        "sup": price * 0.95, "res": price * 1.05
    }

# ==========================================
# 4. ARAYÜZ
# ==========================================
st.markdown("<h1 style='text-align:center; color:#66fcf1;'>CRAZYTOWN CAPITAL V15</h1>", unsafe_allow_html=True)

# ARAMA KUTUSU
query = st.text_input("COIN ARA (Örn: BTC, ETH, SOL, PEPE)", value="").upper().strip()

if query:
    if st.button("ANALİZ ET"):
        with st.spinner("Veriler çekiliyor..."):
            raw_data = get_crypto_data(query)
            
            if raw_data:
                # Analiz yap
                result = analyze_data(raw_data)
                
                # --- SONUÇ KARTI (HTML HATASI OLMAMASI İÇİN BASİTLEŞTİRİLDİ) ---
                col_style = "#00ff00" if result['score'] >= 60 else "#ff4b4b"
                
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: {col_style};">
                    <div class="card-header">
                        <span>{result['symbol']} / USDT</span>
                        <span>${result['price']:,.4f}</span>
                    </div>
                    <div class="card-sub" style="color:{col_style}">24s Değişim: %{result['change']:.2f}</div>
                    
                    <hr style="border-color:#444;">
                    
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; color:#eee;">
                        <div>Trend: <b>{result['trend']}</b></div>
                        <div>RSI: <b>{result['rsi']:.1f}</b> ({result['rsi_text']})</div>
                        <div>Beluga: <b style="color:#66fcf1">{result['beluga']}</b></div>
                        <div>Güven Skoru: <b style="color:{col_style}">{result['score']}/100</b></div>
                    </div>
                    
                    <div style="text-align:center; margin-top:20px;">
                        <h2 style="color:{col_style}; margin:0;">{result['decision']}</h2>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # --- STRATEJİ RAPORU ---
                st.markdown(f"""
                <div class="analysis-box">
                    <div class="section-head">📋 CRAZYTOWN STRATEJİ RAPORU</div>
                    
                    <div class="strategy-row">
                        <span>⚡ SCALP (Kısa Vade):</span>
                        <span class="bullish">{result['scalp']}</span>
                    </div>
                    <div class="strategy-row">
                        <span>🌊 SWING (Orta Vade):</span>
                        <span class="bullish">{result['swing']}</span>
                    </div>
                    
                    <div class="section-head" style="margin-top:15px;">🎯 HEDEF SEVİYELER</div>
                    <div class="strategy-row">
                        <span>🛡️ Destek (Giriş):</span>
                        <span>${result['sup']:,.4f}</span>
                    </div>
                    <div class="strategy-row">
                        <span>🚫 Direnç (Satış):</span>
                        <span>${result['res']:,.4f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # --- GRAFİK ---
                st.write("")
                components.html(f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{{"width": "100%", "height": "500", "symbol": "BINANCE:{result['symbol']}USDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI"], "support_host": "https://www.tradingview.com"}}</script></div>""", height=500)
                
            else:
                st.error("Coin bulunamadı veya veri çekilemedi. Lütfen 'BTC', 'ETH' gibi geçerli bir sembol girin.")
else:
    st.info("👆 Analiz için yukarıya bir Coin sembolü yazın (Örn: BTC).")
    
    # Varsayılan Widget
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=70)
