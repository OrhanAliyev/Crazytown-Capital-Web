import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import time
import plotly.graph_objects as go
import random

# ==========================================
# 1. AYARLAR & SESSION
# ==========================================
st.set_page_config(
    page_title="Crazytown Capital | Ultimate",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Session State (Hata Önleyici)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = "Misafir"
if 'page' not in st.session_state: st.session_state.page = "Login"

# ==========================================
# 2. CSS TASARIMI (FULL ESTETİK)
# ==========================================
st.markdown("""
    <style>
        /* GENEL */
        div[class^="viewerBadge_container"], .viewerBadge_container__1QSob, #MainMenu, header, footer {display: none !important;}
        .stApp > header {display: none !important;}
        .block-container {padding-top: 0rem; padding-bottom: 3rem;}
        .stApp {background-color: #0b0c10; background: radial-gradient(circle at center, #0f1115 0%, #000000 100%); color: #c5c6c7;}
        
        /* TICKER */
        .ticker-wrap { width: 100%; background-color: #000; border-bottom: 1px solid #333; height: 35px; line-height: 35px; overflow: hidden; white-space: nowrap; position: fixed; top: 0; left: 0; z-index: 99;}
        .ticker-item { display: inline-block; padding: 0 2rem; color: #66fcf1; font-weight: bold; font-size: 0.9rem; font-family: monospace; }
        
        /* METRIC KARTLARI (DASHBOARD) */
        .metric-box {
            background: rgba(30, 35, 40, 0.9);
            border: 1px solid #444;
            border-left: 4px solid #66fcf1;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }
        .metric-val { font-size: 1.8rem; font-weight: bold; color: white; }
        .metric-label { font-size: 0.9rem; color: #888; }
        
        /* ANALİZ KARTI */
        .tool-card {
            background: rgba(30, 35, 40, 0.9);
            border: 1px solid #444;
            border-left: 6px solid #66fcf1;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        /* RAPOR KUTUSU */
        .analysis-box {
            background: rgba(255, 255, 255, 0.04);
            border-left: 4px solid #ffd700;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .report-header { color: #ffd700; font-weight: bold; font-size: 1.1rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; margin-bottom: 12px; display:block;}
        .report-text { color: #ddd; font-size: 0.95rem; margin-bottom: 6px; line-height: 1.6; }
        
        /* TABLO & GİRİŞ */
        .login-box { border: 1px solid #66fcf1; padding: 40px; border-radius: 15px; background: rgba(20,20,30,0.95); text-align: center; margin-top: 80px; max-width: 500px; margin-left: auto; margin-right: auto;}
        .stTextInput input { background-color: #15161a !important; color: white !important; border: 1px solid #333 !important; border-radius: 5px; }
        .stButton button { background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: 800 !important; width: 100%; border-radius: 6px; transition: 0.3s; }
        
        /* TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; margin-top: 20px; border-bottom: 1px solid #333; }
        .stTabs [data-baseweb="tab"] { height: 50px; color: #888; font-weight: 600; font-size: 1rem; }
        .stTabs [aria-selected="true"] { color: #66fcf1 !important; border-bottom: 3px solid #66fcf1 !important; background: rgba(102,252,241,0.05); }
    </style>
""", unsafe_allow_html=True)

# HABER BANDI
st.markdown("""<div class="ticker-wrap"><span class="ticker-item">BTC: $98,450 (+2.4%)</span><span class="ticker-item">ETH: $3,200 (+1.1%)</span><span class="ticker-item">SOL: $145 (-0.5%)</span><span class="ticker-item">CRAZYTOWN CAPITAL V19.1 SYSTEM ONLINE</span></div>""", unsafe_allow_html=True)

# ==========================================
# 3. VERİ MOTORU (SAĞLAM)
# ==========================================
@st.cache_data(ttl=15)
def get_crypto_data(symbol):
    symbol = symbol.upper().strip().replace("USDT", "")
    try:
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
    except: return None
    return None

def analyze_market(data):
    closes = data['closes']; volumes = data['volumes']; price = data['price']
    s = pd.Series(closes)
    # RSI
    delta = s.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    curr_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    # SMA
    sma7 = s.rolling(7).mean().iloc[-1]
    sma25 = s.rolling(25).mean().iloc[-1]
    # Beluga
    curr_vol = volumes[-1]
    avg_vol = sum(volumes[-20:]) / 20
    vol_ratio = (curr_vol / avg_vol) * 100 if avg_vol > 0 else 0
    beluga = "YÜKSEK 🐋" if vol_ratio > 130 else "NORMAL 🌊"
    
    score = 50
    reasons = []
    if sma7 > sma25: trend="BOĞA"; t_cls="tag-bull"; score+=20; reasons.append(f"Fiyat (${price:,.2f}) ortalamaların üzerinde.")
    else: trend="AYI"; t_cls="tag-bear"; score-=20; reasons.append(f"Fiyat (${price:,.2f}) baskı altında.")
    
    if curr_rsi < 30: score+=25; reasons.append("RSI Dipte (Alım Fırsatı).")
    elif curr_rsi > 70: score-=25; reasons.append("RSI Tepede (Düzeltme Riski).")
    
    score = max(0, min(100, score))
    
    if score >= 80: decision="GÜÇLÜ AL 🚀"; col="#00ff00"
    elif score >= 60: decision="ALIM FIRSATI ✅"; col="#66fcf1"
    elif score <= 20: decision="GÜÇLÜ SAT 📉"; col="#ff4b4b"
    else: decision="BEKLE ✋"; col="#ccc"
    
    scalp = "AL" if curr_rsi < 35 else "SAT" if curr_rsi > 65 else "NÖTR"
    swing = "TUT" if sma7 > sma25 else "NAKİT"
    hold = "EKLE" if score > 65 else "KORU"
    
    return {
        "symbol": data['symbol'], "price": price, "change": data['change'],
        "rsi": curr_rsi, "trend": trend, "t_cls": t_cls, "beluga": beluga,
        "score": score, "decision": decision, "col": col, "reasons": reasons,
        "scalp": scalp, "swing": swing, "hold": hold, "sup": price*0.95, "res": price*1.05
    }

# ==========================================
# 4. SAYFA YÖNETİMİ
# ==========================================
def go_home(): st.session_state.page = "Home"; st.rerun()
def go_login(): st.session_state.page = "Login"; st.rerun()
def go_register(): st.session_state.page = "Register"; st.rerun()

# --- GİRİŞ ---
def show_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<div class='login-box'><h1 style='color:#66fcf1;'>CRAZYTOWN</h1><p style='color:#888;'>PRO ANALİZ TERMİNALİ</p></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        col_x, col_y, col_z = st.columns([1,2,1])
        with col_y:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("GİRİŞ YAP"):
                st.session_state.logged_in = True
                st.session_state.user = u if u else "Misafir"
                go_home()
            if st.button("KAYIT OL"): go_register()

def show_register():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<div class='login-box'><h2>💎 KAYIT OL</h2></div>", unsafe_allow_html=True)
        st.text_input("Kullanıcı Adı")
        st.text_input("Şifre", type="password")
        if st.button("OLUŞTUR"):
            st.success("Başarılı!"); time.sleep(1); go_login()
        if st.button("GERİ"): go_login()

# --- DASHBOARD ---
def show_dashboard():
    c1, c2 = st.columns([4, 1])
    with c1: st.markdown(f"### 👋 Hoşgeldin, <span style='color:#66fcf1'>{st.session_state.user}</span>", unsafe_allow_html=True)
    with c2: 
        if st.button("🔒 ÇIKIŞ YAP"): st.session_state.logged_in = False; go_login()
            
    # Ticker Tape
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=50)

    # SEKMELER
    tab_dash, tab_analiz, tab_piyasa, tab_akademi, tab_vip = st.tabs(["🏠 DASHBOARD", "⚡ ANALİZ", "📊 PİYASA", "🎓 AKADEMİ", "👑 VIP"])
    
    # --- TAB 1: KİŞİSEL DASHBOARD (GERİ GELDİ!) ---
    with tab_dash:
        st.markdown("<br>", unsafe_allow_html=True)
        # Metrikler
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown("""<div class="metric-box"><div class="metric-val">$12,450</div><div class="metric-label">TOPLAM BAKİYE</div></div>""", unsafe_allow_html=True)
        m2.markdown("""<div class="metric-box"><div class="metric-val" style="color:#00ff00">%68.5</div><div class="metric-label">KAZANMA ORANI</div></div>""", unsafe_allow_html=True)
        m3.markdown("""<div class="metric-box"><div class="metric-val" style="color:#66fcf1">142</div><div class="metric-label">TOPLAM İŞLEM</div></div>""", unsafe_allow_html=True)
        m4.markdown("""<div class="metric-box"><div class="metric-val" style="color:#ffd700">PRO</div><div class="metric-label">ÜYELİK PLANI</div></div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns([2, 1])
        with g1:
            st.markdown("### 📈 Bakiye Büyümesi (Simülasyon)")
            # Fake Data for Chart
            chart_data = pd.DataFrame({'Ay': ['Oca','Şub','Mar','Nis','May'], 'Kazanç': [10000, 10500, 10200, 11500, 12450]})
            fig = go.Figure(data=go.Scatter(x=chart_data['Ay'], y=chart_data['Kazanç'], mode='lines+markers', line=dict(color='#66fcf1', width=3)))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.markdown("### 📋 Son İşlemler")
            st.dataframe(pd.DataFrame({
                'Coin': ['BTC', 'ETH', 'SOL', 'PEPE'],
                'Yön': ['LONG', 'SHORT', 'LONG', 'LONG'],
                'Durum': ['✅ WIN', '❌ LOSS', '✅ WIN', '✅ WIN'],
                'Kar': ['$450', '-$120', '$320', '$850']
            }), use_container_width=True, hide_index=True)

    # --- TAB 2: ANALİZ MOTORU ---
    with tab_analiz:
        st.markdown("<br>", unsafe_allow_html=True)
        query = st.text_input("COIN ARA (Sembol Girin: BTC, ETH...)", value="").upper().strip()
        
        if query:
            if st.button("🚀 ANALİZİ BAŞLAT"):
                with st.spinner("Yapay zeka analiz ediyor..."):
                    raw = get_crypto_data(query)
                    if raw:
                        r = analyze_market(raw)
                        
                        # ANA KART
                        st.markdown(f"""
                        <div class="tool-card" style="border-left-color: {r['col']};">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:1.6rem; font-weight:bold; color:white;">{r['symbol']} / USDT</span>
                                <span style="font-size:1.6rem; color:white;">${r['price']:,.4f}</span>
                            </div>
                            <p style="color:{'#00ff00' if r['change']>0 else '#ff4b4b'}">24s Değişim: %{r['change']:.2f}</p>
                            <hr style="border-color:#444;">
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
                                <div><small style="color:#888;">GENEL TREND</small><br><span class="{r['t_cls']}">{r['trend']}</span></div>
                                <div><small style="color:#888;">BELUGA ENDEKSİ</small><br><span style="color:#66fcf1; font-weight:bold;">{r['beluga']}</span></div>
                                <div><small style="color:#888;">RSI GÜCÜ</small><br><strong style="color:white;">{r['rsi']:.1f}</strong></div>
                                <div><small style="color:#888;">GÜVEN SKORU</small><br><strong style="color:{r['col']};">{r['score']}/100</strong></div>
                            </div>
                            <div style="background:#333; height:8px; width:100%; border-radius:5px; margin-top:15px;">
                                <div style="background:linear-gradient(90deg, #ff4b4b, #ffd700, #00ff00); height:100%; width:{r['score']}%; border-radius:5px;"></div>
                            </div>
                            <h1 style="text-align:center; color:{r['col']}; margin-top:20px;">{r['decision']}</h1>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # DETAY RAPORU
                        st.markdown(f"""
                        <div class="analysis-box">
                            <span class="report-header">📋 CRAZYTOWN STRATEJİ RAPORU</span>
                            <p class="report-text"><b>⏱️ ZAMAN DİLİMİ:</b> SCALP: {r['scalp']} | SWING: {r['swing']} | HOLD: {r['hold']}</p>
                            <hr style="border-color:#444;">
                            <p class="report-text"><b>🔍 NEDENLER:</b></p>
                            {''.join([f'<p class="report-text">• {x}</p>' for x in r['reasons']])}
                            <hr style="border-color:#444;">
                            <p class="report-text"><b>🎯 HEDEFLER:</b> Destek: <span style="color:#00ff00">${r['sup']:,.4f}</span> | Direnç: <span style="color:#ff4b4b">${r['res']:,.4f}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.write("")
                        components.html(f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{{"width": "100%", "height": "500", "symbol": "BINANCE:{r['symbol']}USDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI"], "support_host": "https://www.tradingview.com"}}</script></div>""", height=500)
                    else:
                        st.error("Veri bulunamadı. Geçerli sembol girin (Örn: BTC).")

    # --- TAB 3: PİYASA ---
    with tab_piyasa:
        components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>{"colorTheme": "dark", "dateRange": "12M", "exchange": "BINANCE", "showChart": true, "locale": "tr", "largeChartUrl": "", "isTransparent": true, "showSymbolLogo": true, "width": "100%", "height": "500"}</script></div>""", height=500)

    # --- TAB 4: AKADEMİ ---
    with tab_akademi:
        c1, c2 = st.columns(2)
        with c1: st.markdown("""<div class="tool-card"><h3>📘 Teknik Analiz</h3><p>Destek, direnç ve indikatörleri öğrenin.</p></div>""", unsafe_allow_html=True)
        with c2: st.markdown("""<div class="tool-card"><h3>🧠 Psikoloji</h3><p>FOMO yönetimi ve risk analizi.</p></div>""", unsafe_allow_html=True)

    # --- TAB 5: VIP ---
    with tab_vip:
        st.markdown("<h2 style='text-align:center;'>👑 VIP PAKETLER</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown("""<div class="tool-card" style="text-align:center;"><h3>AYLIK</h3><h1>$30</h1></div>""", unsafe_allow_html=True)
        c2.markdown("""<div class="tool-card" style="text-align:center; border-color:#ffd700;"><h3>YILLIK</h3><h1>$250</h1></div>""", unsafe_allow_html=True)
        c3.markdown("""<div class="tool-card" style="text-align:center;"><h3>LIFETIME</h3><h1>$500</h1></div>""", unsafe_allow_html=True)

# ==========================================
# 5. UYGULAMA BAŞLATICI
# ==========================================
if st.session_state.logged_in:
    show_dashboard()
elif st.session_state.page == "Register":
    show_register()
else:
    show_login()
