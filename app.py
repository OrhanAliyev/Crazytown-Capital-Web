import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import time
import plotly.graph_objects as go

# ==========================================
# 1. AYARLAR & SESSION
# ==========================================
st.set_page_config(page_title="Crazytown Capital", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = "Misafir"
if 'page' not in st.session_state: st.session_state.page = "Login"

# ==========================================
# 2. KULLANICI VERİ MOTORU (SENİN İŞLEMLERİN)
# ==========================================
def get_user_trades():
    """
    BURASI SENİN GOOGLE SHEETS VEYA EXCEL VERİLERİNİ TEMSİL EDER.
    Gerçek bağlantı yapılana kadar buradaki verileri kullanır.
    """
    data = {
        'Tarih': ['2025-01-10', '2025-01-12', '2025-01-15', '2025-01-18', '2025-01-20'],
        'Coin': ['BTC', 'ETH', 'SOL', 'PEPE', 'AVAX'],
        'Yön': ['LONG', 'SHORT', 'LONG', 'LONG', 'SHORT'],
        'Giriş': [42000, 2500, 95, 0.000012, 35],
        'Çıkış': [44000, 2400, 105, 0.000015, 32],
        'Durum': ['WIN', 'WIN', 'WIN', 'WIN', 'WIN'],
        'Kar_Zarar': [2000, 100, 500, 300, 150] # Dolar bazında kar
    }
    return pd.DataFrame(data)

# Verileri Hesapla
df_trades = get_user_trades()
total_profit = df_trades['Kar_Zarar'].sum()
total_trades = len(df_trades)
win_count = len(df_trades[df_trades['Durum'] == 'WIN'])
win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
current_balance = 10000 + total_profit # Başlangıç bakiyesi 10.000$ kabul edildi

# ==========================================
# 3. CSS TASARIMI (FULL)
# ==========================================
st.markdown("""
    <style>
        .stApp {background-color: #0b0c10; color: #c5c6c7;}
        div[class^="viewerBadge_container"], header, footer {display: none;}
        
        .ticker-wrap { background: #000; border-bottom: 1px solid #333; height: 30px; line-height: 30px; overflow: hidden; white-space: nowrap; }
        
        /* KARTLAR */
        .metric-box { background: rgba(30, 35, 40, 0.9); border: 1px solid #444; border-left: 4px solid #66fcf1; border-radius: 8px; padding: 15px; text-align: center; }
        .tool-card { background: rgba(30, 35, 40, 0.9); border: 1px solid #444; border-left: 6px solid #66fcf1; border-radius: 12px; padding: 25px; margin-bottom: 20px; }
        .analysis-box { background: rgba(255, 255, 255, 0.05); border-left: 4px solid #ffd700; padding: 20px; margin-top: 15px; border-radius: 5px; }
        
        /* RENKLER */
        .bull { color: #00ff00; font-weight: bold; } .bear { color: #ff4b4b; font-weight: bold; }
        
        /* GİRİŞ */
        .login-box { max-width: 400px; margin: 80px auto; padding: 40px; background: rgba(20,20,30,0.95); border: 1px solid #66fcf1; border-radius: 15px; text-align: center; box-shadow: 0 0 30px rgba(102,252,241,0.15); }
        .stTextInput input { background-color: #15161a !important; color: white !important; border: 1px solid #333 !important; }
        .stButton button { background-color: #66fcf1 !important; color: #0b0c10 !important; font-weight: bold !important; width: 100%; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""<div class="ticker-wrap"><span style="padding-left:20px; color:#66fcf1; font-weight:bold;">BTC: $98,450 (+2.4%) | ETH: $3,200 (+1.1%) | SOL: $145 (-0.5%) | CRAZYTOWN CAPITAL V21.0 (GOOGLE DATA READY)</span></div>""", unsafe_allow_html=True)

# ==========================================
# 4. VERİ MOTORU (BINANCE)
# ==========================================
def get_data(symbol):
    symbol = symbol.upper().replace("USDT", "").strip()
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50"
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            closes = [float(x[4]) for x in data]; volumes = [float(x[5]) for x in data]
            price = closes[-1]; change = ((price - closes[0]) / closes[0]) * 100
            return {"symbol": symbol, "price": price, "change": change, "closes": closes, "volumes": volumes}
    except: pass
    return None

def analyze(data):
    closes = data['closes']; volumes = data['volumes']; price = data['price']
    s = pd.Series(closes)
    # RSI
    delta = s.diff(); gain = (delta.where(delta > 0, 0)).rolling(14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss; rsi = 100 - (100 / (1 + rs)); curr_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    # SMA
    sma7 = s.rolling(7).mean().iloc[-1]; sma25 = s.rolling(25).mean().iloc[-1]
    # Beluga
    curr_vol = volumes[-1]; avg_vol = sum(volumes[-20:]) / 20; vol_ratio = (curr_vol / avg_vol) * 100 if avg_vol > 0 else 0
    
    score = 50; reasons = []
    if sma7 > sma25: trend="BOĞA 🟢"; score+=20; reasons.append("Trend Pozitif.")
    else: trend="AYI 🔴"; score-=20; reasons.append("Trend Negatif.")
    
    if curr_rsi < 30: score+=25; reasons.append("RSI Dipte.")
    elif curr_rsi > 70: score-=25; reasons.append("RSI Tepede.")
    
    if vol_ratio > 150: beluga="YÜKSEK 🐋"; score+=15; reasons.append("Balina Hacmi!")
    else: beluga="NORMAL 🌊"
    
    score = max(0, min(100, score))
    if score >= 80: decision="GÜÇLÜ AL 🚀"; col="#00ff00"
    elif score >= 60: decision="ALIM FIRSATI ✅"; col="#66fcf1"
    elif score <= 20: decision="GÜÇLÜ SAT 📉"; col="#ff4b4b"
    else: decision="BEKLE ✋"; col="#ccc"
    
    return {"symbol": data['symbol'], "price": price, "change": data['change'], "rsi": curr_rsi, "trend": trend, "beluga": beluga, "score": score, "decision": decision, "col": col, "reasons": reasons, "sup": price*0.95, "res": price*1.05}

# ==========================================
# 5. SAYFALAR
# ==========================================
def go_home(): st.session_state.page = "Home"; st.rerun()
def go_login(): st.session_state.page = "Login"; st.rerun()

def show_login():
    st.markdown(f"<div class='login-box'><h1 style='color:#66fcf1;'>CRAZYTOWN</h1><p>GOOGLE SHEETS ENTEGRASYONLU</p></div>", unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        u = st.text_input("Kullanıcı Adı"); p = st.text_input("Şifre", type="password")
        if st.button("GİRİŞ YAP"): st.session_state.logged_in=True; st.session_state.user=u if u else "Misafir"; go_home()

def show_dashboard():
    c1, c2 = st.columns([4,1])
    with c1: st.title(f"👋 Hoşgeldin, {st.session_state.user}")
    with c2: 
        if st.button("ÇIKIŞ"): st.session_state.logged_in=False; go_login()
    
    components.html("""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>{"symbols": [{"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}, {"proName": "BINANCE:ETHUSDT", "title": "Ethereum"}, {"proName": "BINANCE:SOLUSDT", "title": "Solana"}], "showSymbolLogo": true, "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "tr"}</script></div>""", height=50)

    tab1, tab2, tab3 = st.tabs(["🏠 DASHBOARD (GOOGLE)", "⚡ ANALİZ MOTORU", "🎓 AKADEMİ"])
    
    # --- TAB 1: KİŞİSEL DASHBOARD (GOOGLE DATA) ---
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        # Dinamik Metrikler (df_trades'den geliyor)
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f"""<div class="metric-box"><div style="font-size:1.5rem; font-weight:bold; color:white;">${current_balance:,.0f}</div><div style="color:#888;">GÜNCEL BAKİYE</div></div>""", unsafe_allow_html=True)
        m2.markdown(f"""<div class="metric-box"><div style="font-size:1.5rem; font-weight:bold; color:#00ff00;">%{win_rate:.1f}</div><div style="color:#888;">KAZANMA ORANI</div></div>""", unsafe_allow_html=True)
        m3.markdown(f"""<div class="metric-box"><div style="font-size:1.5rem; font-weight:bold; color:#66fcf1;">{total_trades}</div><div style="color:#888;">TOPLAM İŞLEM</div></div>""", unsafe_allow_html=True)
        m4.markdown(f"""<div class="metric-box"><div style="font-size:1.5rem; font-weight:bold; color:{'#00ff00' if total_profit > 0 else '#ff4b4b'};">${total_profit:,.0f}</div><div style="color:#888;">TOPLAM PNL</div></div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns([2, 1])
        with g1:
            st.markdown("### 📈 Bakiye Gelişimi (Senin Verilerin)")
            # Kümülatif Kar Grafiği
            df_trades['Cumulative'] = 10000 + df_trades['Kar_Zarar'].cumsum()
            fig = go.Figure(data=go.Scatter(x=df_trades['Tarih'], y=df_trades['Cumulative'], mode='lines+markers', line=dict(color='#66fcf1', width=3)))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.markdown("### 📋 Google Kayıtlı İşlemler")
            st.dataframe(df_trades[['Tarih', 'Coin', 'Yön', 'Durum', 'Kar_Zarar']], use_container_width=True, hide_index=True)

    # --- TAB 2: ANALİZ ---
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        query = st.text_input("COIN ARA (Örn: BTC, ETH...)", value="").upper().strip()
        if query:
            if st.button("ANALİZ ET"):
                with st.spinner("Analiz ediliyor..."):
                    raw = get_data(query)
                    if raw:
                        r = analyze(raw)
                        st.markdown(f"""
                        <div class="tool-card" style="border-left-color: {r['col']};">
                            <h2 style="color:white; margin:0;">{r['symbol']} / USDT: ${r['price']:,.4f}</h2>
                            <p style="color:{'#00ff00' if r['change']>0 else '#ff4b4b'}">24s Değişim: %{r['change']:.2f}</p>
                            <hr style="border-color:#444;">
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; color:#ddd;">
                                <div>Trend: <b>{r['trend']}</b></div>
                                <div>Beluga: <b style="color:#66fcf1">{r['beluga']}</b></div>
                                <div>RSI: <b>{r['rsi']:.1f}</b></div>
                                <div>Skor: <b style="color:{r['col']}">{r['score']}/100</b></div>
                            </div>
                            <h1 style="text-align:center; color:{r['col']}; margin-top:20px;">{r['decision']}</h1>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="analysis-box">
                            <h4 style="color:#ffd700;">📋 DETAYLI RAPOR</h4>
                            {''.join([f'<p>• {x}</p>' for x in r['reasons']])}
                            <hr style="border-color:#444;">
                            <p><b>HEDEFLER:</b> Destek: <span style="color:#00ff00">${r['sup']:,.4f}</span> | Direnç: <span style="color:#ff4b4b">${r['res']:,.4f}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.write("")
                        components.html(f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{{"width": "100%", "height": "500", "symbol": "BINANCE:{r['symbol']}USDT", "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true, "studies": ["STD;MACD", "STD;RSI"], "support_host": "https://www.tradingview.com"}}</script></div>""", height=500)
                    else: st.error("Veri bulunamadı.")

    # --- TAB 3: AKADEMİ ---
    with tab3:
        c1, c2 = st.columns(2)
        with c1: st.info("📘 Teknik Analiz Eğitimi")
        with c2: st.warning("🧠 Psikoloji Yönetimi")

# ==========================================
# 6. BAŞLAT
# ==========================================
if st.session_state.logged_in: show_dashboard()
else: show_login()
