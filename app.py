import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import time

# ==========================================
# 1. AYARLAR & SESSION (ÇÖKME ÖNLEYİCİ)
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Ultimate",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- KRİTİK DÜZELTME: Session State İlk Tanımlama ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"Name": "Misafir"}
if 'page' not in st.session_state: st.session_state.page = "Login"

# ==========================================
# 2. CSS TASARIMI (FULL ESTETİK GERİ GELDİ)
# ==========================================
st.markdown("""
    <style>
        /* GENEL */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 0rem; padding-bottom: 3rem;}
        .stApp {background-color: #0b0c10; background: radial-gradient(circle at center, #0f1115 0%, #000000 100%); color: #c5c6c7;}
        
        /* HABER BANDI (TICKER) */
        .ticker-wrap { width: 100%; background-color: #000; border-bottom: 1px solid #333; height: 35px; line-height: 35px; overflow: hidden; white-space: nowrap; position: fixed; top: 0; left: 0; z-index: 99;}
        .ticker-item { display: inline-block; padding: 0 2rem; color: #66fcf1; font-weight: bold; font-size: 0.9rem; font-family: monospace; }
        
        /* ARKA PLAN ANİMASYONU */
        .area { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; overflow: hidden; }
        .circles { position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: hidden; }
        .circles li { position: absolute; display: block; list-style: none; width: 20px; height: 20px; background: rgba(102, 252, 241, 0.05); animation: animate 25s linear infinite; bottom: -150px; border: 1px solid rgba(102, 252, 241, 0.1); transform: rotate(45deg); }
        .circles li:nth-child(1){ left: 25%; width: 80px; height: 80px; animation-delay: 0s; }
        .circles li:nth-child(2){ left: 10%; width: 20px; height: 20px; animation-delay: 2s; animation-duration: 12s; }
        .circles li:nth-child(3){ left: 70%; width: 20px; height: 20px; animation-delay: 4s; }
        @keyframes animate { 0%{ transform: translateY(0) rotate(45deg); opacity: 0; } 50%{ opacity: 0.5; } 100%{ transform: translateY(-1000px) rotate(720deg); opacity: 0; } }

        /* GİRİŞ KUTUSU */
        .login-box { border: 1px solid #66fcf1; padding: 40px; border-radius: 15px; background: rgba(20,20,30,0.95); box-shadow: 0 0 30px rgba(102,252,241,0.15); text-align: center; margin-top: 80px; max-width: 500px; margin-left: auto; margin-right: auto;}
        
        /* ANALİZ KARTI (GLASSMORPHISM) */
        .tool-card {
            background: rgba(30, 35, 40, 0.9);
            border: 1px solid #444;
            border-left: 6px solid #66fcf1;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        /* DETAY RAPORU KUTUSU */
        .analysis-box {
            background: rgba(255, 255, 255, 0.04);
            border-left: 4px solid #ffd700;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .report-header { color: #ffd700; font-weight: bold; font-size: 1.1rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; margin-bottom: 12px; display:block; letter-spacing: 1px;}
        .report-text { color: #ddd; font-size: 0.95rem; margin-bottom: 6px; line-height: 1.6; }
        
        /* RENKLER VE ETİKETLER */
        .tag-bull { color: #00ff00; font-weight: bold; background: rgba(0,255,0,0.15); padding: 3px 8px; border-radius: 4px;}
        .tag-bear { color: #ff4b4b; font-weight: bold; background: rgba(255,0,0,0.15); padding: 3px 8px; border-radius: 4px;}
        .tag-neutral { color: #ccc; font-weight: bold; background: rgba(255,255,255,0.1); padding: 3px 8px; border-radius: 4px;}
        
        /* FORM ELEMANLARI */
        .stTextInput input { background-color: #15161a !important; color: white !important; border: 1px solid #333 !important; border-radius: 5px; }
        .stButton button { background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: 800 !important; width: 100%; border-radius: 6px; padding: 12px; transition: 0.3s; }
        .stButton button:hover { box-shadow: 0 0 15px #66fcf1; transform: scale(1.02); }
        
        /* TAB YAPISI */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; margin-top: 40px; border-bottom: 1px solid #333; }
        .stTabs [data-baseweb="tab"] { height: 50px; color: #888; font-weight: 600; font-size: 1rem; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 3px solid #66fcf1 !important; background: rgba(102,252,241,0.05); }
    </style>
""", unsafe_allow_html=True)

# HABER BANDI VE ANİMASYON
st.markdown("""<div class="ticker-wrap"><span class="ticker-item">BTC: $98,450 (+2.4%)</span><span class="ticker-item">ETH: $3,200 (+1.1%)</span><span class="ticker-item">SOL: $145 (-0.5%)</span><span class="ticker-item">FED FAİZ KARARI BEKLENİYOR...</span><span class="ticker-item">CRAZYTOWN CAPITAL V19.0 (RESURRECTION) AKTİF</span></div>""", unsafe_allow_html=True)
st.markdown("""<div class="area"><ul class="circles"><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div>""", unsafe_allow_html=True)

# ==========================================
# 3. VERİ & ANALİZ MOTORU
# ==========================================
@st.cache_data(ttl=15)
def get_crypto_data(symbol):
    symbol = symbol.upper().strip().replace("USDT", "")
    try:
        # Binance API (En Hızlı ve Güvenilir)
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50"
        r = requests.get(url, timeout=3)
        
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame(data, columns=['t','o','h','l','c','v','x','x','x','x','x','x'])
            closes = df['c'].astype(float).tolist()
            volumes = df['v'].astype(float).tolist()
            
            curr_price = closes[-1]
            change = ((curr_price - closes[-24]) / closes[-24]) * 100 if len(closes) > 24 else 0
            
            return {"symbol": symbol, "price": curr_price, "change": change, "closes": closes, "volumes": volumes}
    except:
        return None
    return None

def analyze_market(data):
    closes = data['closes']
    volumes = data['volumes']
    price = data['price']
    
    # 1. Teknik Hesaplamalar
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
    
    # 2. BELUGA (Balina) Analizi
    curr_vol = volumes[-1]
    avg_vol = sum(volumes[-20:]) / 20
    vol_ratio = (curr_vol / avg_vol) * 100 if avg_vol > 0 else 0
    
    if vol_ratio > 150: beluga = "ÇOK YÜKSEK 🐋"; beluga_score = 15
    elif vol_ratio > 120: beluga = "YÜKSEK 🐟"; beluga_score = 10
    else: beluga = "NORMAL 🌊"; beluga_score = 0
    
    # 3. Puanlama & Mantık
    score = 50
    reasons = []
    
    # Trend
    if sma7 > sma25: 
        trend = "BOĞA (YÜKSELİŞ)"; trend_cls = "tag-bull"
        score += 20
        reasons.append(f"Fiyat (${price:,.2f}), kısa vadeli ortalamaların üzerinde. Trend pozitif.")
    else: 
        trend = "AYI (DÜŞÜŞ)"; trend_cls = "tag-bear"
        score -= 20
        reasons.append(f"Fiyat (${price:,.2f}), ortalamaların altında baskılanıyor.")
        
    # RSI
    if current_rsi < 30: 
        score += 25
        reasons.append(f"RSI ({current_rsi:.1f}) Aşırı SATIM bölgesinde. Tepki yükselişi gelebilir.")
    elif current_rsi > 70: 
        score -= 25
        reasons.append(f"RSI ({current_rsi:.1f}) Aşırı ALIM bölgesinde. Düzeltme riski var.")
    else:
        reasons.append(f"RSI ({current_rsi:.1f}) nötr bölgede seyrediyor.")
        
    # Beluga Puanı
    if beluga_score > 0:
        score += beluga_score
        reasons.append(f"Anlık hacim ortalamanın üzerinde (%{vol_ratio:.0f}). Balina aktivitesi tespit edildi.")
        
    score = max(0, min(100, score))
    
    # Karar Metni
    if score >= 80: decision = "GÜÇLÜ AL 🚀"; color = "#00ff00"
    elif score >= 60: decision = "ALIM FIRSATI ✅"; color = "#66fcf1"
    elif score <= 20: decision = "GÜÇLÜ SAT 📉"; color = "#ff4b4b"
    elif score <= 40: decision = "SATIŞ BASKISI 🔻"; color = "#ff9900"
    else: decision = "BEKLE / İZLE ✋"; color = "#ccc"
    
    # Strateji Matrisi
    scalp = "AL ✅" if current_rsi < 35 else "SAT 🔻" if current_rsi > 65 else "NÖTR ✋"
    swing = "TUT 🟢" if sma7 > sma25 else "NAKİT 🔴"
    hold = "EKLE 🧺" if score > 65 else "KORU 🛡️"
    
    return {
        "symbol": data['symbol'], "price": price, "change": data['change'],
        "rsi": current_rsi, "trend": trend, "trend_cls": trend_cls,
        "beluga": beluga, "score": score, "decision": decision, "dec_color": color,
        "reasons": reasons, "scalp": scalp, "swing": swing, "hold": hold,
        "sup": price * 0.95, "res": price * 1.05
    }

# ==========================================
# 4. SAYFA YÖNETİMİ
# ==========================================
def go_home(): st.session_state.page = "Home"; st.rerun()
def go_login(): st.session_state.page = "Login"; st.rerun()
def go_register(): st.session_state.page = "Register"; st.rerun()

# --- GİRİŞ SAYFASI ---
def show_login():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div class='login-box'>
            <h1 style='color:#66fcf1;'>CRAZYTOWN CAPITAL</h1>
            <p style='color:#888;'>KURUMSAL ANALİZ TERMİNALİ</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı Adı")
        p = st.text_input("Şifre", type="password", placeholder="Şifre")
        
        b1, b2 = st.columns(2)
        with b1:
            if st.button("GİRİŞ YAP"):
                st.session_state.logged_in = True
                st.session_state.user_info = {"Name": u if u else "Misafir"}
                go_home()
        with b2:
            if st.button("KAYIT OL"): go_register()

# --- KAYIT SAYFASI ---
def show_register():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<div class='login-box'><h2>💎 YENİ HESAP</h2></div>", unsafe_allow_html=True)
        st.text_input("Yeni Kullanıcı Adı")
        st.text_input("E-Posta")
        st.text_input("Yeni Şifre", type="password")
        if st.button("HESAP OLUŞTUR"):
            st.success("Kayıt Başarılı! Giriş yapabilirsiniz.")
            time.sleep(1)
            go_login()
        if st.button("Geri Dön"): go_login()

# --- ANA DASHBOARD ---
def show_dashboard():
    # Üst Bar
    c1, c2 = st.columns([4, 1])
    with c1: st.markdown(f"### 👋 Hoşgeldin, <span style='color:#66fcf1'>{st.session_state.user_info['Name']}</span>", unsafe_allow_html=True)
    with c2: 
        if st.button("🔒 ÇIKIŞ YAP"): 
            st.session_state.logged_in = False
            go_login()
            
    # TradingView Ticker
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=50)

    # Sekmeler
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ PRO ANALİZ", "📊 PİYASA VERİLERİ", "🎓 AKADEMİ", "🧮 HESAP MAKİNESİ", "👑 VIP OFİS"])
    
    # TAB 1: ANALİZ
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        query = st.text_input("COIN ARA (Sembol Girin: BTC, ETH, SOL, PEPE...)", value="").upper().strip()
        
        if query:
            if st.button("🚀 ANALİZ ET"):
                with st.spinner(f"{query} için yapay zeka verileri işliyor..."):
                    raw_data = get_crypto_data(query)
                    
                    if raw_data:
                        r = analyze_market(raw_data)
                        
                        # --- 1. ANA KART ---
                        st.markdown(f"""
                        <div class="tool-card" style="border-left-color: {r['dec_color']};">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:1.6rem; font-weight:bold; color:white;">{r['symbol']} / USDT</span>
                                <span style="font-size:1.6rem; color:white;">${r['price']:,.4f}</span>
                            </div>
                            <div style="color:{'#00ff00' if r['change']>0 else '#ff4b4b'}; font-size:1rem; margin-bottom:20px;">
                                24s Değişim: %{r['change']:.2f}
                            </div>
                            
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
                                <div><small style="color:#888;">GENEL TREND</small><br><span class="{r['trend_cls']}">{r['trend']}</span></div>
                                <div><small style="color:#888;">BELUGA (BALİNA)</small><br><span style="color:#66fcf1; font-weight:bold;">{r['beluga']}</span></div>
                                <div><small style="color:#888;">RSI GÜCÜ</small><br><strong style="color:white;">{r['rsi']:.1f}</strong></div>
                                <div><small style="color:#888;">GÜVEN SKORU</small><br><strong style="color:{r['dec_color']};">{r['score']}/100</strong></div>
                            </div>
                            
                            <div style="background:#333; height:8px; width:100%; border-radius:5px; margin-top:15px;">
                                <div style="background:linear-gradient(90deg, #ff4b4b, #ffd700, #00ff00); height:100%; width:{r['score']}%; border-radius:5px;"></div>
                            </div>
                            
                            <div style="text-align:center; margin-top:20px;">
                                <small style="color:#888;">YAPAY ZEKA KARARI</small><br>
                                <span style="font-size:2rem; font-weight:bold; color:{r['dec_color']};">{r['decision']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # --- 2. DETAYLI RAPOR ---
                        st.markdown(f"""
                        <div class="analysis-box">
                            <span class="report-header">📋 CRAZYTOWN STRATEJİ RAPORU</span>
                            
                            <p class="report-text" style="color:#66fcf1; font-weight:bold;">⏱️ ZAMAN DİLİMİ STRATEJİSİ:</p>
                            <p class="report-text">⚡ <b>KISA VADE (Scalp):</b> {r['scalp']} | 🌊 <b>ORTA VADE (Swing):</b> {r['swing']} | 🏰 <b>UZUN VADE (Hold):</b> {r['hold']}</p>
                            <hr style="border-color:#444;">
                            
                            <p class="report-text" style="color:#66fcf1; font-weight:bold;">🔍 NEDEN BU KARAR VERİLDİ?</p>
                            {''.join([f'<p class="report-text">• {reason}</p>' for reason in r['reasons']])}
                            <hr style="border-color:#444;">
                            
                            <p class="report-text" style="color:#66fcf1; font-weight:bold;">🎯 HEDEF SEVİYELER:</p>
                            <p class="report-text">🛡️ <b>Destek (Alım Bölgesi):</b> <span style="color:#00ff00">${r['sup']:,.4f}</span></p>
                            <p class="report-text">🚫 <b>Direnç (Satış Bölgesi):</b> <span style="color:#ff4b4b">${r['res']:,.4f}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # GRAFİK
                        st.write("")
                        components.html(f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{{"width": "100%", "height": "500", "symbol": "BINANCE:{r['symbol']}USDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI"], "support_host": "https://www.tradingview.com"}}</script></div>""", height=500)
                    else:
                        st.error("Veri alınamadı. Lütfen coinin Binance'de listeli olduğundan emin olun (Örn: BTC, ETH, PEPE).")
        else:
            st.info("👆 Analiz etmek istediğiniz coini yukarıya yazın.")

    # TAB 2: PİYASA
    with tab2:
        st.subheader("🔥 Piyasa Sıcaklık Haritası")
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-crypto-coins-heatmap.js" async>{"dataSource": "Crypto","blockSize": "market_cap_calc","blockColor": "change","locale": "tr","symbolUrl": "","colorTheme": "dark","hasTopBar": false,"isDataSetEnabled": false,"isZoomEnabled": true,"hasSymbolTooltip": true,"width": "100%","height": 500}</script></div>""", height=500)

    # TAB 3: AKADEMİ
    with tab3:
        c1, c2 = st.columns(2)
        with c1: st.markdown("""<div class="tool-card"><h3>📘 Teknik Analiz 101</h3><p>Destek, direnç, RSI ve MACD indikatörlerinin nasıl kullanıldığını öğrenin.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class="tool-card"><h3>🧠 Yatırım Psikolojisi</h3><p>FOMO (Fırsatı Kaçırma Korkusu) ve panik satışından nasıl korunursunuz?</p></div>""", unsafe_allow_html=True)

    # TAB 4: HESAPLAMA
    with tab4:
        st.markdown("### 🧮 Pozisyon Hesaplayıcı")
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Yatırım Miktarı ($)", 100)
            risk = st.slider("Risk Oranı (%)", 1, 10, 2)
        with col2:
            st.markdown(f"""
            <div class="analysis-box">
                <p>Maksimum Kayıp: <b style="color:#ff4b4b">${amount * (risk/100):.2f}</b></p>
                <p>Hedef Kar (1:2): <b style="color:#00ff00">${amount * (risk/100) * 2:.2f}</b></p>
            </div>
            """, unsafe_allow_html=True)

    # TAB 5: VIP
    with tab5:
        st.markdown("<h2 style='text-align:center;'>👑 VIP ÜYELİK PAKETLERİ</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("""<div class="tool-card" style="text-align:center;"><h3>AYLIK</h3><h1>$30</h1><p>Temel Analiz<br>Reklamsız</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class="tool-card" style="text-align:center; border-color:#ffd700;"><h3>YILLIK</h3><h1>$250</h1><p>Pro Analiz<br>Beluga Göstergesi<br>Strateji Raporu</p></div>""", unsafe_allow_html=True)
        with c3: st.markdown("""<div class="tool-card" style="text-align:center;"><h3>LIFETIME</h3><h1>$500</h1><p>Her Şey Dahil<br>Ömür Boyu Erişim</p></div>""", unsafe_allow_html=True)

# ==========================================
# 5. UYGULAMA BAŞLATICI
# ==========================================
if st.session_state.logged_in:
    show_dashboard()
elif st.session_state.page == "Register":
    show_register()
else:
    show_login()
