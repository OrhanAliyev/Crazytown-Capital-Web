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
        
        /* ANALİZ KARTI ÖZEL */
        .tool-card { text-align: left; border-left: 4px solid #66fcf1; transition: transform 0.3s ease; position:relative; overflow:hidden;}
        .tool-card:hover { transform: translateX(5px); border-color: #ffd700; }
        .tool-title { font-weight: bold; color: #fff; font-size: 1.2rem; display: flex; justify-content: space-between; align-items:center; }
        
        .status-bullish { color: #00ff00; background: rgba(0,255,0,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight:bold;}
        .status-bearish { color: #ff4b4b; background: rgba(255,75,75,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight:bold;}
        .status-neutral { color: #ccc; background: rgba(200,200,200,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight:bold;}

        /* ARAMA ÇUBUĞU */
        .search-container { margin-bottom: 20px; }
        .stTextInput label { color: #66fcf1 !important; font-weight: bold; }

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
# 2. GELİŞMİŞ ANALİZ MOTORU (SEARCH ENGINE)
# ==========================================

@st.cache_data(ttl=10)
def get_live_market_data(symbol):
    # Kullanıcı ne yazarsa yazsın (örn: 'doge', 'DOGE', 'DoGe') -> 'DOGE' yap
    symbol = symbol.upper()
    try:
        # Binance API
        pair = f"{symbol}USDT"
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1h&limit=50"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'q_vol', 'num_trades', 'tb_base_vol', 'tb_quote_vol', 'ignore'])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df
    except:
        return pd.DataFrame()
    return pd.DataFrame()

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

def analyze_coin(symbol):
    df = get_live_market_data(symbol)
    if df.empty:
        return None # Hata durumu
    
    rsi, sma_s, sma_l, vol = calculate_signals(df)
    current_price = df['close'].iloc[-1]
    
    # 1. TREND ANALİZİ
    if sma_s > sma_l: trend = "BOĞA (YÜKSELİŞ) 🟢"
    else: trend = "AYI (DÜŞÜŞ) 🔴"
    
    # 2. HACİM ANALİZİ
    whale_alert = "YÜKSEK 🐋" if vol > 130 else "NORMAL 🌊"
    
    # 3. GÜVEN SKORU HESAPLAMA (AI SCORE)
    score = 50 # Başlangıç nötr
    
    # Trend Puanı
    if sma_s > sma_l: score += 20
    else: score -= 20
    
    # RSI Puanı
    if rsi < 30: score += 25 # Aşırı satım, dönüş ihtimali
    elif rsi > 70: score -= 25 # Aşırı alım, düşüş ihtimali
    
    # Hacim Puanı
    if vol > 150: score += 10 # Hacim onayı
    
    # Skor Sınırları (0-100)
    score = max(0, min(100, score))
    
    # 4. KARAR
    if score >= 75: decision = "GÜÇLÜ AL 🚀"
    elif score >= 60: decision = "ALIM FIRSATI ✅"
    elif score <= 25: decision = "GÜÇLÜ SAT 📉"
    elif score <= 40: decision = "SATIŞ BASKISI 🔻"
    else: decision = "BEKLE / NÖTR ✋"
    
    return {
        "price": current_price,
        "rsi": rsi,
        "trend": trend,
        "whale": whale_alert,
        "vol_pct": vol,
        "score": score,
        "decision": decision
    }

# ==========================================
# 3. KULLANICI SİSTEMİ (DEMO)
# ==========================================
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
    title = "KAYIT OL" if mode == "Register" else "GİRİŞ YAP"
    st.markdown(f'<div class="hero-title" style="font-size:2.5rem;">{title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.form("auth"):
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if mode == "Register": n = st.text_input("Ad Soyad")
        if st.form_submit_button("ONAYLA"):
            if mode == "Register":
                st.success("Hesap Oluşturuldu!"); time.sleep(1); go_to("Login")
            else:
                if u == "admin" and p == "password123":
                    st.session_state.logged_in = True; st.session_state.user_info = {"Name": "Orhan Aliyev", "Plan": "ADMIN"}; st.rerun()
                else:
                    st.session_state.logged_in = True; st.session_state.user_info = {"Name": u, "Plan": "Free"}; st.success("Hoşgeldiniz"); time.sleep(1); st.rerun()
    if st.button("Ana Sayfaya Dön"): go_to("Home")
    st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD ---
def show_dashboard():
    ui = st.session_state.user_info
    
    st.markdown(f"""
    <div class="status-bar">
        <span><span style="height:8px;width:8px;background:#00ff00;border-radius:50%;display:inline-block;"></span> <b>SİSTEM AKTİF</b></span>
        <span>|</span>
        <span>VERİ: <b>CANLI (BINANCE)</b></span>
        <span>|</span>
        <span>KULLANICI: <b>{ui.get('Name')}</b></span>
    </div>
    """, unsafe_allow_html=True)

    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=50)

    st.write("")
    if st.button("🔒 ÇIKIŞ YAP"): st.session_state.logged_in = False; go_to("Home")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ PRO ARAÇLAR (ARA & BUL)", "📊 PİYASA VERİLERİ", "🎓 AKADEMİ", "🧮 HESAP MAKİNESİ", "👑 VIP OFİS"])
    
    # TAB 1: PRO ARAÇLAR (ARAMA MOTORU)
    with tab1:
        st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;"><h3 style="margin:0;">⚡ YAPAY ZEKA ANALİZ MOTORU</h3><span style="color:#888;">{datetime.now().strftime('%H:%M')}</span></div>""", unsafe_allow_html=True)
        
        # --- ARAMA ÇUBUĞU ---
        st.markdown("<div class='search-container'>", unsafe_allow_html=True)
        search_query = st.text_input("COIN ARA (Örn: BTC, ETH, DOGE, PEPE, AVAX)", placeholder="Sembol girin ve Enter'a basın...").upper()
        st.markdown("</div>", unsafe_allow_html=True)

        if search_query:
            with st.spinner(f"{search_query} için Binance verileri taranıyor..."):
                data = analyze_coin(search_query)
                
            if data:
                # Dinamik Renkler
                card_border = "#00ff00" if data['score'] >= 60 else "#ff4b4b" if data['score'] <= 40 else "#ffd700"
                trend_col = "status-bullish" if "BOĞA" in data['trend'] else "status-bearish" if "AYI" in data['trend'] else "status-neutral"
                whale_col = "status-bullish" if "YÜKSEK" in data['whale'] else "status-neutral"
                
                st.markdown(f"""
                <div class="tool-card" style="border-left-color: {card_border}; border-width: 0 0 0 6px;">
                    <div class="tool-title">
                        <span>{search_query} / USDT</span>
                        <span style="font-size:1.5rem;">${data['price']:,.4f}</span>
                    </div>
                    <hr style="border-color:rgba(255,255,255,0.1);">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        <div>
                            <p style="color:#ccc; margin:0; font-size:0.9rem;">Piyasa Yönü</p>
                            <span class="{trend_col}">{data['trend']}</span>
                        </div>
                        <div>
                            <p style="color:#ccc; margin:0; font-size:0.9rem;">Balina Aktivitesi</p>
                            <span class="{whale_col}">{data['whale']}</span>
                        </div>
                        <div>
                            <p style="color:#ccc; margin:0; font-size:0.9rem;">RSI (Güç Endeksi)</p>
                            <b style="color:#fff;">{data['rsi']:.2f}</b>
                        </div>
                        <div>
                            <p style="color:#ccc; margin:0; font-size:0.9rem;">Hacim Artışı</p>
                            <b style="color:#fff;">%{data['vol_pct']:.0f}</b>
                        </div>
                    </div>
                    <br>
                    <p style="color:#ccc; margin:0; font-size:0.9rem;">Yapay Zeka Güven Skoru:</p>
                    <div style="background:#333; height:10px; width:100%; border-radius:5px; margin-bottom:10px;">
                        <div style="background:linear-gradient(90deg, #ff4b4b, #ffd700, #00ff00); height:100%; width:{data['score']}%; border-radius:5px;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#fff; font-weight:bold; font-size:1.2rem;">KARAR: <span style="color:{card_border}">{data['decision']}</span></span>
                        <span style="color:#888;">Skor: {data['score']}/100</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Sinyal Güçlüyse Telegram Butonu Göster
                if data['score'] >= 75 or data['score'] <= 25:
                    st.write("")
                    st.markdown(f"""<a href="https://t.me/share/url?url=CRAZYTOWN ANALİZ: {search_query} - Karar: {data['decision']} (Fiyat: {data['price']})" target="_blank" style="text-decoration:none;"><button style="background:#0088cc; color:white; width:100%; padding:10px; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">✈️ TELEGRAM'A SİNYAL GÖNDER</button></a>""", unsafe_allow_html=True)
                
                # TradingView Grafiği (Dinamik)
                st.write("")
                components.html(f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{{"width": "100%", "height": "500", "symbol": "BINANCE:{search_query}USDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI"], "support_host": "https://www.tradingview.com"}}</script></div>""", height=500)

            else:
                st.error("Coin bulunamadı veya listelenmiyor. Lütfen doğru sembolü girin (Örn: BTC, ETH).")
        
        else:
            st.info("👆 Analiz etmek için yukarıdaki kutuya bir coin ismi yazın.")
            # Varsayılan olarak BTC ve ETH kartlarını göster (Boş kalmasın)
            c1, c2 = st.columns(2)
            btc_d = analyze_coin("BTC")
            eth_d = analyze_coin("ETH")
            
            if btc_d:
                with c1:
                    trend_col = "status-bullish" if "BOĞA" in btc_d['trend'] else "status-bearish"
                    st.markdown(f"""<div class="tool-card"><div class="tool-title">BITCOIN (BTC)</div><p style="color:#ccc;">Fiyat: ${btc_d['price']:,.2f}<br>Yön: <span class="{trend_col}">{btc_d['trend']}</span><br>Karar: <b>{btc_d['decision']}</b></p></div>""", unsafe_allow_html=True)
            if eth_d:
                with c2:
                    trend_col = "status-bullish" if "BOĞA" in eth_d['trend'] else "status-bearish"
                    st.markdown(f"""<div class="tool-card"><div class="tool-title">ETHEREUM (ETH)</div><p style="color:#ccc;">Fiyat: ${eth_d['price']:,.2f}<br>Yön: <span class="{trend_col}">{eth_d['trend']}</span><br>Karar: <b>{eth_d['decision']}</b></p></div>""", unsafe_allow_html=True)

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
