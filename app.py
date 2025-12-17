import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import time

# ==========================================
# 1. AYARLAR & CSS
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TASARIMI (HATA DÜZELTİLDİ) ---
st.markdown("""
    <style>
        /* GENEL */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 0rem; padding-bottom: 3rem;}
        .stApp {background-color: #0b0c10; background: radial-gradient(circle at center, #0f1115 0%, #000000 100%); color: #c5c6c7;}
        
        /* HABER BANDI */
        .ticker-wrap { width: 100%; background-color: #000; border-bottom: 1px solid #333; height: 30px; line-height: 30px; overflow: hidden; white-space: nowrap; position: fixed; top: 0; left: 0; z-index: 99;}
        .ticker-item { display: inline-block; padding: 0 2rem; color: #66fcf1; font-weight: bold; font-size: 0.8rem; }
        
        /* GİRİŞ EKRANI */
        .login-box { border: 1px solid #66fcf1; padding: 40px; border-radius: 10px; background: rgba(20,20,30,0.9); box-shadow: 0 0 20px rgba(102,252,241,0.2); text-align: center; margin-top: 50px;}
        
        /* ANALİZ KARTI */
        .tool-card {
            background: rgba(20, 25, 30, 0.9);
            border: 1px solid #333;
            border-left: 5px solid #66fcf1;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        
        /* DETAY RAPORU */
        .analysis-box {
            background: rgba(255, 255, 255, 0.03);
            border-left: 4px solid #ffd700;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .report-title { color: #ffd700; font-weight: bold; font-size: 1.1rem; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 5px; display:block;}
        .report-text { color: #ccc; font-size: 0.95rem; margin-bottom: 5px; line-height: 1.5; }
        
        /* RENKLER & ETİKETLER */
        .tag-bull { color: #00ff00; font-weight: bold; background: rgba(0,255,0,0.1); padding: 2px 6px; border-radius: 4px;}
        .tag-bear { color: #ff4b4b; font-weight: bold; background: rgba(255,0,0,0.1); padding: 2px 6px; border-radius: 4px;}
        .tag-neutral { color: #ccc; font-weight: bold; background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px;}
        
        /* INPUT & BUTTON */
        .stTextInput input { background-color: #15161a !important; color: white !important; border: 1px solid #333 !important; }
        .stButton button { background-color: #66fcf1 !important; color: black !important; font-weight: bold !important; width: 100%; border-radius: 5px; transition: 0.3s; }
        .stButton button:hover { box-shadow: 0 0 10px #66fcf1; color: white !important; background-color: #45a29e !important; }
        
        /* TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; margin-top: 40px; border-bottom: 1px solid #333; }
        .stTabs [data-baseweb="tab"] { height: 50px; color: #888; font-weight: 600; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 2px solid #66fcf1 !important; }
    </style>
""", unsafe_allow_html=True)

# HABER BANDI
st.markdown("""<div class="ticker-wrap"><span class="ticker-item">BTC: $98,450 (+2.4%)</span><span class="ticker-item">ETH: $3,200 (+1.1%)</span><span class="ticker-item">SOL: $145 (-0.5%)</span><span class="ticker-item">FED FAİZ KARARI BEKLENİYOR...</span><span class="ticker-item">CRAZYTOWN CAPITAL V16.0 (ULTIMATE) AKTİF</span></div>""", unsafe_allow_html=True)

# ==========================================
# 2. GÜÇLÜ VERİ MOTORU (BINANCE API)
# ==========================================
@st.cache_data(ttl=15)
def get_crypto_data(symbol):
    symbol = symbol.upper().strip().replace("USDT", "")
    try:
        # Binance API (En Hızlısı)
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50"
        r = requests.get(url, timeout=3)
        
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame(data, columns=['t','o','h','l','c','v','x','x','x','x','x','x'])
            closes = df['c'].astype(float).tolist()
            volumes = df['v'].astype(float).tolist()
            
            curr_price = closes[-1]
            prev_price = closes[0] # 50 saat önceki fiyat (yaklaşık 2 gün)
            change = ((curr_price - closes[-24]) / closes[-24]) * 100 if len(closes) > 24 else 0 # 24 saatlik değişim
            
            return {"symbol": symbol, "price": curr_price, "change": change, "closes": closes, "volumes": volumes}
    except:
        return None
    return None

def analyze_market(data):
    closes = data['closes']
    volumes = data['volumes']
    price = data['price']
    
    # 1. TEKNİK HESAPLAMALAR
    s = pd.Series(closes)
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
    
    # 2. BELUGA (BALİNA) ANALİZİ
    curr_vol = volumes[-1]
    avg_vol = sum(volumes[-20:]) / 20
    vol_ratio = (curr_vol / avg_vol) * 100 if avg_vol > 0 else 0
    
    if vol_ratio > 150: beluga = "ÇOK YÜKSEK 🐋"; beluga_score = 15
    elif vol_ratio > 120: beluga = "YÜKSEK 🐟"; beluga_score = 10
    else: beluga = "NORMAL 🌊"; beluga_score = 0
    
    # 3. PUANLAMA VE KARAR
    score = 50
    reasons = []
    
    # Trend Puanı
    if sma7 > sma25: 
        trend = "BOĞA (YÜKSELİŞ)"; trend_cls = "tag-bull"
        score += 20
        reasons.append(f"Fiyat (${price:,.2f}), 25 günlük ortalamanın üzerinde. Trend sağlıklı.")
    else: 
        trend = "AYI (DÜŞÜŞ)"; trend_cls = "tag-bear"
        score -= 20
        reasons.append(f"Fiyat (${price:,.2f}), ortalamaların altında baskılanıyor.")
        
    # RSI Puanı
    if current_rsi < 30: 
        score += 25
        reasons.append(f"RSI ({current_rsi:.1f}) Aşırı SATIM bölgesinde. Bu bir dip sinyali olabilir.")
    elif current_rsi > 70: 
        score -= 25
        reasons.append(f"RSI ({current_rsi:.1f}) Aşırı ALIM bölgesinde. Düzeltme ihtimali var.")
    else:
        reasons.append(f"RSI ({current_rsi:.1f}) nötr bölgede.")
        
    # Beluga Puanı
    if beluga_score > 0:
        score += beluga_score
        reasons.append(f"Hacim patlaması tespit edildi! Balina aktivitesi mevcut.")
        
    score = max(0, min(100, score))
    
    # Karar Metni
    if score >= 80: decision = "GÜÇLÜ AL 🚀"; color = "#00ff00"
    elif score >= 60: decision = "ALIM FIRSATI ✅"; color = "#66fcf1"
    elif score <= 20: decision = "GÜÇLÜ SAT 📉"; color = "#ff4b4b"
    elif score <= 40: decision = "SATIŞ BASKISI 🔻"; color = "#ff9900"
    else: decision = "BEKLE / İZLE ✋"; color = "#ccc"
    
    # Zaman Dilimi Stratejisi
    scalp = "AL" if current_rsi < 35 else "SAT" if current_rsi > 65 else "NÖTR"
    swing = "TUT" if sma7 > sma25 else "NAKİT"
    
    return {
        "symbol": data['symbol'], "price": price, "change": data['change'],
        "rsi": current_rsi, "trend": trend, "trend_cls": trend_cls,
        "beluga": beluga, "score": score, "decision": decision, "dec_color": color,
        "reasons": reasons, "scalp": scalp, "swing": swing,
        "sup": price * 0.95, "res": price * 1.05
    }

# ==========================================
# 3. SAYFA YÖNETİMİ
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = "Login"

def go_home(): st.session_state.page = "Home"; st.rerun()
def go_login(): st.session_state.page = "Login"; st.rerun()
def go_register(): st.session_state.page = "Register"; st.rerun()

# --- GİRİŞ & KAYIT ---
def show_login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<div class='login-box'><h2>🚀 GİRİŞ YAP</h2>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("SİSTEME GİR"):
            st.session_state.logged_in = True
            st.session_state.user = u
            go_home()
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("KAYIT OL"): go_register()
        st.markdown("</div>", unsafe_allow_html=True)

def show_register():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<div class='login-box'><h2>💎 KAYIT OL</h2>", unsafe_allow_html=True)
        st.text_input("Yeni Kullanıcı Adı")
        st.text_input("Yeni Şifre", type="password")
        if st.button("HESAP OLUŞTUR"):
            st.success("Kayıt Başarılı!")
            time.sleep(1)
            go_login()
        st.button("Geri Dön", on_click=go_login)
        st.markdown("</div>", unsafe_allow_html=True)

# --- ANA DASHBOARD ---
def show_dashboard():
    # Üst Bar
    c1, c2 = st.columns([3, 1])
    with c1: st.markdown(f"### 👋 Hoşgeldin, {st.session_state.user}")
    with c2: 
        if st.button("ÇIKIŞ YAP"): 
            st.session_state.logged_in = False
            go_login()
            
    # Widget
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=50)

    # Sekmeler
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ PRO ANALİZ", "📊 PİYASA", "🎓 AKADEMİ", "🧮 HESAPLAMA", "👑 VIP OFİS"])
    
    # TAB 1: ANALİZ
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        query = st.text_input("COIN ARA (Örn: BTC, ETH, PEPE, SOL)", value="").upper().strip()
        
        if query:
            if st.button("ANALİZ ET"):
                with st.spinner("Yapay zeka verileri işliyor..."):
                    raw_data = get_crypto_data(query)
                    
                    if raw_data:
                        r = analyze_market(raw_data)
                        
                        # --- ANALİZ KARTI (HTML/CSS FIX) ---
                        st.markdown(f"""
                        <div class="tool-card" style="border-left-color: {r['dec_color']};">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:1.5rem; font-weight:bold; color:white;">{r['symbol']} / USDT</span>
                                <span style="font-size:1.5rem; color:white;">${r['price']:,.4f}</span>
                            </div>
                            <div style="color:{'#00ff00' if r['change']>0 else '#ff4b4b'}; font-size:0.9rem; margin-bottom:15px;">
                                24s Değişim: %{r['change']:.2f}
                            </div>
                            
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                                <div><small style="color:#888;">GENEL TREND</small><br><span class="{r['trend_cls']}">{r['trend']}</span></div>
                                <div><small style="color:#888;">BELUGA ENDEKSİ</small><br><span style="color:#66fcf1; font-weight:bold;">{r['beluga']}</span></div>
                                <div><small style="color:#888;">RSI (GÜÇ)</small><br><strong style="color:white;">{r['rsi']:.2f}</strong></div>
                                <div><small style="color:#888;">GÜVEN SKORU</small><br><strong style="color:{r['dec_color']};">{r['score']}/100</strong></div>
                            </div>
                            
                            <hr style="border-color:#444; margin:15px 0;">
                            
                            <div style="text-align:center;">
                                <small style="color:#888;">YAPAY ZEKA KARARI</small><br>
                                <span style="font-size:1.8rem; font-weight:bold; color:{r['dec_color']};">{r['decision']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # --- DETAY RAPORU ---
                        st.markdown(f"""
                        <div class="analysis-box">
                            <span class="report-title">📋 CRAZYTOWN DETAYLI STRATEJİ RAPORU</span>
                            <p class="report-text"><b>⏱️ ZAMAN DİLİMİ ÖNERİLERİ:</b></p>
                            <p class="report-text">⚡ SCALP (15dk): <b style="color:white">{r['scalp']}</b> | 🌊 SWING (Günlük): <b style="color:white">{r['swing']}</b></p>
                            <br>
                            <p class="report-text"><b>🔍 NEDENLER & GEREKÇELER:</b></p>
                            {''.join([f'<p class="report-text">• {reason}</p>' for reason in r['reasons']])}
                            <br>
                            <p class="report-text"><b>🎯 HEDEF SEVİYELER:</b></p>
                            <p class="report-text">🛡️ Destek (Giriş): <b style="color:#00ff00">${r['sup']:,.4f}</b></p>
                            <p class="report-text">🚫 Direnç (Kar Al): <b style="color:#ff4b4b">${r['res']:,.4f}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # GRAFİK
                        st.write("")
                        components.html(f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{{"width": "100%", "height": "500", "symbol": "BINANCE:{r['symbol']}USDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI"], "support_host": "https://www.tradingview.com"}}</script></div>""", height=500)
                    else:
                        st.error("Veri alınamadı. Lütfen coinin Binance'de listeli olduğundan emin olun (Örn: BTC, ETH, PEPE).")
        else:
            st.info("Analiz etmek istediğiniz coini yukarıya yazın.")

    # TAB 2: PİYASA
    with tab2:
        st.subheader("🔥 Piyasa Sıcaklık Haritası")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-crypto-coins-heatmap.js" async>{"dataSource": "Crypto","blockSize": "market_cap_calc","blockColor": "change","locale": "tr","symbolUrl": "","colorTheme": "dark","hasTopBar": false,"isDataSetEnabled": false,"isZoomEnabled": true,"hasSymbolTooltip": true,"width": "100%","height": 500}</script></div>""", height=500)

    # TAB 3: AKADEMİ
    with tab3:
        c1, c2 = st.columns(2)
        with c1: st.markdown("""<div class="tool-card"><h3>📘 Teknik Analiz 101</h3><p>Destek, direnç ve trend çizgilerini öğrenin.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class="tool-card"><h3>🧠 Yatırım Psikolojisi</h3><p>FOMO ve panik satışından nasıl korunursunuz?</p></div>""", unsafe_allow_html=True)

    # TAB 4: HESAPLAMA
    with tab4:
        st.markdown("### 🧮 Kar/Zarar Hesaplayıcı")
        amount = st.number_input("Yatırım Miktarı ($)", 100)
        risk = st.slider("Risk Oranı (%)", 1, 10, 2)
        st.success(f"Bu işlemde maksimum kayıp: ${amount * (risk/100):.2f}")

    # TAB 5: VIP
    with tab5:
        st.markdown("<h2 style='text-align:center;'>👑 VIP ÜYELİK</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("""<div class="tool-card" style="text-align:center;"><h3>AYLIK</h3><h1>$30</h1><p>Temel Analiz</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class="tool-card" style="text-align:center; border-color:#ffd700;"><h3>YILLIK</h3><h1>$250</h1><p>Pro Analiz + Beluga</p></div>""", unsafe_allow_html=True)
        with c3: st.markdown("""<div class="tool-card" style="text-align:center;"><h3>LIFETIME</h3><h1>$500</h1><p>Her Şey Dahil</p></div>""", unsafe_allow_html=True)

# ==========================================
# 4. UYGULAMA BAŞLATICI
# ==========================================
if st.session_state.logged_in:
    show_dashboard()
elif st.session_state.page == "Register":
    show_register()
else:
    show_login()
