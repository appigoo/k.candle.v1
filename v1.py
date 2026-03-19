import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import requests
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
import pytz

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="交易信號監控系統",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

:root {
    --bg: #111827;
    --surface: #1a2235;
    --card: #1e2d45;
    --border: #2e4270;
    --accent-green: #00ff88;
    --accent-red: #ff4d6a;
    --accent-blue: #60aeff;
    --accent-yellow: #ffe066;
    --text: #eaf2ff;
    --text-dim: #9ab8d8;
    --glow-green: 0 0 12px rgba(0,255,136,0.4);
    --glow-red: 0 0 12px rgba(255,59,92,0.4);
    --glow-blue: 0 0 12px rgba(77,159,255,0.4);
}

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Force all text elements bright */
p, span, label, div, li, a {
    color: var(--text);
}

.stApp { background-color: var(--bg); }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* Header */
.main-header {
    text-align: center;
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.main-header h1 {
    font-family: 'Share Tech Mono', monospace;
    font-size: 2rem;
    letter-spacing: 0.15em;
    color: var(--accent-green);
    text-shadow: var(--glow-green);
    margin: 0;
}
.main-header p {
    color: var(--text-dim);
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    margin: 0.3rem 0 0;
}

/* Cards */
.signal-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
    position: relative;
    overflow: hidden;
}
.signal-card.buy { border-left: 3px solid var(--accent-green); }
.signal-card.sell { border-left: 3px solid var(--accent-red); }

.signal-card .ticker {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.3rem;
    font-weight: 700;
    color: white;
}
.signal-card .badge-buy {
    background: rgba(0,255,136,0.15);
    color: var(--accent-green);
    border: 1px solid var(--accent-green);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    font-family: 'Share Tech Mono', monospace;
}
.signal-card .badge-sell {
    background: rgba(255,59,92,0.15);
    color: var(--accent-red);
    border: 1px solid var(--accent-red);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    font-family: 'Share Tech Mono', monospace;
}
.signal-card .meta {
    color: #b8d0ec;
    font-size: 0.85rem;
    margin-top: 0.4rem;
}
.signal-card .price {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.1rem;
    color: var(--accent-yellow);
}

/* Pro Mode Toggle area */
.pro-box {
    background: linear-gradient(135deg, #0f1a35, #1a1035);
    border: 1px solid #2a3060;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}
.pro-title {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.9rem;
    color: var(--accent-blue);
    letter-spacing: 0.1em;
    margin-bottom: 0.6rem;
}

/* Status bar */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-dim);
}
.dot-active { color: var(--accent-green); animation: blink 1.2s infinite; }
.dot-inactive { color: var(--text-dim); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* Metric cards */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    text-align: center;
}
.metric-card .label {
    font-size: 0.72rem;
    color: var(--text-dim);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.metric-card .value {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.4rem;
    margin-top: 0.2rem;
}

/* Streamlit element overrides */
.stButton > button {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    letter-spacing: 0.08em;
    border-radius: 6px;
    border: none;
    transition: all 0.2s;
}
.stTextInput input, .stSelectbox select, .stMultiSelect div {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
}
.stToggle label { color: var(--text) !important; }

div[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
}

.section-title {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: #9ab8d8;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin-bottom: 0.8rem;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ─────────────────────────────────────────────────────────
for key, default in {
    "monitoring": False,
    "signals_log": [],
    "last_signal_time": defaultdict(lambda: None),
    "pro_filter": False,
    "pro_rsi": False,
    "pro_cooldown": False,
    "scan_count": 0,
    "signal_count": 0,
    "buy_count": 0,
    "sell_count": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Telegram ──────────────────────────────────────────────────────────────────
def send_telegram(msg: str):
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        st.session_state.signals_log.append({"type": "error", "msg": f"Telegram 錯誤: {e}"})

# ─── Signal Detection ───────────────────────────────────────────────────────────
def stars(n):
    return "★" * n + "☆" * (5 - n)

def detect_signals(ticker: str, interval: str, pro_filter: bool, pro_rsi: bool, pro_cooldown: bool):
    interval_map = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"60m","4h":"1h","1d":"1d","1w":"1wk","1mo":"1mo"}
    period_map   = {"1m":"1d","5m":"5d","15m":"5d","30m":"5d","1h":"30d","4h":"60d","1d":"6mo","1w":"1y","1mo":"5y"}
    yf_interval  = interval_map.get(interval, "60m")
    yf_period    = period_map.get(interval, "30d")

    # 4h workaround: download 60m and resample
    if interval == "4h":
        df = yf.download(ticker, period="60d", interval="60m", auto_adjust=True, progress=False)
        if df.empty: return []
        df = df.resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
    else:
        df = yf.download(ticker, period=yf_period, interval=yf_interval, auto_adjust=True, progress=False)

    if df is None or len(df) < 20:
        return []

    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df = df.dropna()

    close  = df["Close"]
    open_  = df["Open"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]

    # ── Indicators ──────────────────────────────────────────────────────────────
    rsi_series = ta.momentum.RSIIndicator(close=close, window=14).rsi()
    rsi_val    = float(rsi_series.iloc[-1]) if rsi_series is not None else 50.0

    body      = close - open_
    body_abs  = body.abs()
    upper_wick = high - close.where(close > open_, open_)
    lower_wick = close.where(close < open_, open_) - low

    # Volume vs avg of previous 5 bars
    vol_avg5      = volume.iloc[-6:-1].mean()
    vol_curr      = float(volume.iloc[-1])
    vol_pct       = ((vol_curr - vol_avg5) / vol_avg5 * 100) if vol_avg5 > 0 else 0
    vol_suffix    = f"+{vol_pct:.0f}%" if vol_pct >= 0 else f"{vol_pct:.0f}%"
    vol_ok        = vol_pct >= 80 if pro_filter else True

    current_price = float(close.iloc[-1])

    def is_green(i=-1): return float(close.iloc[i]) > float(open_.iloc[i])
    def is_red(i=-1):   return float(close.iloc[i]) < float(open_.iloc[i])
    def body_size(i=-1):return float(body_abs.iloc[i])
    def avg_body():     return float(body_abs.iloc[-6:-1].mean())

    signals = []

    def add(name, direction, rating, pattern_ok):
        if not pattern_ok: return
        if pro_filter and rating < 4: return
        if not vol_ok: return
        if pro_rsi:
            if direction == "BUY"  and rsi_val >= 35: return
            if direction == "SELL" and rsi_val <= 65: return

        # Cooldown check
        key = f"{ticker}_{direction}"
        if pro_cooldown and st.session_state.last_signal_time[key] is not None:
            elapsed_bars = 3  # conceptual; use time-based approximation
            mins_per_bar = {"1m":1,"5m":5,"15m":15,"30m":30,"1h":60,"4h":240,"1d":1440,"1w":10080,"1mo":43200}
            mpb = mins_per_bar.get(interval, 60)
            cooldown_mins = mpb * 3
            since_last = (datetime.now() - st.session_state.last_signal_time[key]).total_seconds() / 60
            if since_last < cooldown_mins:
                return

        signals.append({
            "ticker": ticker,
            "name": name,
            "direction": direction,
            "rating": rating,
            "price": current_price,
            "interval": interval,
            "vol_pct": vol_suffix,
            "rsi": rsi_val,
            "time": datetime.now(),
        })
        st.session_state.last_signal_time[f"{ticker}_{direction}"] = datetime.now()

    # ── BUY Patterns ─────────────────────────────────────────────────────────────
    # Hammer (single candle) – small body, long lower wick
    hammer = (lower_wick.iloc[-1] >= 2 * body_abs.iloc[-1] and
              upper_wick.iloc[-1] <= 0.3 * body_abs.iloc[-1] and
              body_abs.iloc[-1] > 0)
    # Bullish Engulfing
    bull_eng = (is_red(-2) and is_green(-1) and
                float(open_.iloc[-1]) < float(close.iloc[-2]) and
                float(close.iloc[-1]) > float(open_.iloc[-2]))

    add("鎚子線形態", "BUY", 5,
        bull_eng and hammer)

    add("看漲吞沒 + 上升竿", "BUY", 4,
        bull_eng and body_size(-1) > avg_body() * 1.5)

    # Bullish Spike + Hammer
    bull_spike = body_size(-2) > avg_body() * 1.8 and is_green(-2)
    add("看漲急升 + 鎚子線", "BUY", 4,
        bull_spike and hammer)

    # Double Bottom (simplified: two recent lows close in price, then bounce)
    if len(df) >= 20:
        lows = low.iloc[-20:]
        idx1 = lows.idxmin()
        remaining = lows.drop(idx1)
        if not remaining.empty:
            idx2 = remaining.idxmin()
            low1, low2 = float(lows[idx1]), float(remaining[idx2])
            double_btm = abs(low1 - low2) / max(low1, low2) < 0.02 and is_green(-1)
            add("雙底形態", "BUY", 4, double_btm)

    # Inverse H&S (simplified: 3 troughs with middle lowest)
    if len(df) >= 15:
        w = low.iloc[-15:]
        t1 = float(w.iloc[2])
        t2 = float(w.iloc[7])   # head
        t3 = float(w.iloc[12])
        inv_hs = t2 < t1 and t2 < t3 and abs(t1 - t3) / max(t1, t3) < 0.03 and is_green(-1)
        add("逆頭肩形態", "BUY", 4, inv_hs)

    # Wolfe Wave (price making lower lows then reversal — simplified)
    if len(df) >= 10:
        ww = close.iloc[-10:]
        wolfe = (float(ww.iloc[0]) > float(ww.iloc[2]) > float(ww.iloc[4]) and
                 float(close.iloc[-1]) > float(ww.iloc[-2]))
        add("沃爾夫浪形態", "BUY", 4, wolfe)

    # ── SELL Patterns ─────────────────────────────────────────────────────────────
    # Shooting Star
    shoot = (upper_wick.iloc[-1] >= 2 * body_abs.iloc[-1] and
             lower_wick.iloc[-1] <= 0.3 * body_abs.iloc[-1] and
             body_abs.iloc[-1] > 0)
    bear_eng = (is_green(-2) and is_red(-1) and
                float(open_.iloc[-1]) > float(close.iloc[-2]) and
                float(close.iloc[-1]) < float(open_.iloc[-2]))

    add("流星線形態", "SELL", 5,
        bear_eng and shoot)

    # Three Black Crows
    three_crows = all(is_red(-i) and body_size(-i) > avg_body() for i in [1, 2, 3])
    add("看跌吞沒 + 三隻烏鴉", "SELL", 4,
        bear_eng and three_crows)

    # Bearish Spike + 3 Bap
    bear_spike = body_size(-2) > avg_body() * 1.8 and is_red(-2)
    three_bap  = all(is_red(-i) for i in [1, 2, 3])
    add("看跌急跌 + 三缺口", "SELL", 3,
        bear_spike and three_bap)

    # Head & Shoulders
    if len(df) >= 15:
        w = high.iloc[-15:]
        h1 = float(w.iloc[2])
        h2 = float(w.iloc[7])   # head
        h3 = float(w.iloc[12])
        hs = h2 > h1 and h2 > h3 and abs(h1 - h3) / max(h1, h3) < 0.03 and is_red(-1)
        add("頭肩頂形態", "SELL", 3, hs)

    # Evening Star
    eve_star = (is_green(-3) and
                body_size(-2) < avg_body() * 0.4 and
                is_red(-1) and
                float(close.iloc[-1]) < float(open_.iloc[-3]))
    add("黃昏之星形態", "SELL", 3, eve_star)

    # Descending Triangle
    if len(df) >= 15:
        highs15 = high.iloc[-15:]
        desc_tri = (float(highs15.iloc[-1]) < float(highs15.iloc[0]) and
                    float(low.iloc[-3:].min()) < float(low.iloc[-6:-3].min()) and
                    is_red(-1))
        add("下降三角形", "SELL", 3, desc_tri)

    return signals

# ─── Format Telegram Message ───────────────────────────────────────────────────
def format_message(sig, pro_rsi, pro_cooldown):
    direction_zh = "買入 📈" if sig["direction"] == "BUY" else "賣出 📉"
    icon = "🟢" if sig["direction"] == "BUY" else "🔴"
    interval_zh = {
        "1m":"1分鐘","5m":"5分鐘","15m":"15分鐘","30m":"30分鐘",
        "1h":"1小時","4h":"4小時","1d":"1天","1w":"1週","1mo":"1個月"
    }.get(sig["interval"], sig["interval"])

    lines = [
        f"🚨 <b>交易信號警報</b> 🚨",
        f"",
        f"{icon} <b>股票：{sig['ticker']}</b>",
        f"🎯 信號：【{direction_zh}】{sig['name']}",
        f"⭐ 評級：{stars(sig['rating'])}",
        f"💰 當前價格：${sig['price']:.2f}",
        f"⏱️ 時間週期：{interval_zh}",
        f"📊 成交量：較前5根K線均量 {sig['vol_pct']}",
    ]
    if pro_rsi:
        rsi_note = "（超賣確認）" if sig["direction"] == "BUY" else "（超買確認）"
        lines.append(f"📉 RSI：{sig['rsi']:.1f} {rsi_note}")

    if pro_cooldown and st.session_state.last_signal_time.get(f"{sig['ticker']}_{sig['direction']}"):
        last = st.session_state.last_signal_time[f"{sig['ticker']}_{sig['direction']}"]
        elapsed = datetime.now() - last
        h = int(elapsed.total_seconds() // 3600)
        m = int((elapsed.total_seconds() % 3600) // 60)
        if h > 0:
            elapsed_str = f"{h}小時{m}分鐘前"
        else:
            elapsed_str = f"{m}分鐘前"
        lines.append(f"🕐 距上次信號：{elapsed_str}")

    lines += ["", "⚠️ <i>本通知僅供參考，投資需謹慎</i>"]
    return "\n".join(lines)

# ─── Scan Once ─────────────────────────────────────────────────────────────────
def run_scan(tickers, interval, pro_filter, pro_rsi, pro_cooldown):
    new_signals = []
    for t in tickers:
        t = t.strip().upper()
        if not t: continue
        try:
            sigs = detect_signals(t, interval, pro_filter, pro_rsi, pro_cooldown)
            for sig in sigs:
                new_signals.append(sig)
                msg = format_message(sig, pro_rsi, pro_cooldown)
                send_telegram(msg)
                if sig["direction"] == "BUY":
                    st.session_state.buy_count += 1
                else:
                    st.session_state.sell_count += 1
                st.session_state.signal_count += 1
        except Exception as e:
            pass
    st.session_state.scan_count += 1
    st.session_state.signals_log = (new_signals + st.session_state.signals_log)[:50]

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">📡 監控設定</div>', unsafe_allow_html=True)

    tickers_input = st.text_input(
        "股票代碼（逗號分隔）",
        value="TSLA,AAPL,NVDA,MSFT,AMZN",
        help="例：TSLA,AAPL,NVDA"
    )
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    interval = st.selectbox(
        "時間週期",
        options=["1m","5m","15m","30m","1h","4h","1d","1w","1mo"],
        index=4,
        format_func=lambda x: {
            "1m":"1分鐘","5m":"5分鐘","15m":"15分鐘","30m":"30分鐘",
            "1h":"1小時","4h":"4小時","1d":"1天","1w":"1週","1mo":"1個月"
        }[x]
    )

    refresh_sec = st.slider("掃描間隔（秒）", min_value=30, max_value=600, value=120, step=30)

    st.markdown('<div class="section-title">⚡ 專業模式</div>', unsafe_allow_html=True)

    # One-click professional mode button
    if st.button("⚡ 一鍵啟用專業模式", use_container_width=True):
        st.session_state.pro_filter   = True
        st.session_state.pro_rsi      = True
        st.session_state.pro_cooldown = True
        st.rerun()

    col_r, col_g = st.columns([1,3])
    with col_r:
        st.markdown("①")
    with col_g:
        st.session_state.pro_filter = st.toggle(
            "高評級過濾",
            value=st.session_state.pro_filter,
            help="只顯示 ⭐⭐⭐⭐ 以上信號，且成交量需超均量 +80%"
        )

    col_r, col_g = st.columns([1,3])
    with col_r:
        st.markdown("②")
    with col_g:
        st.session_state.pro_rsi = st.toggle(
            "RSI 確認",
            value=st.session_state.pro_rsi,
            help="買入 RSI < 35，賣出 RSI > 65；通知加入 RSI 數值"
        )

    col_r, col_g = st.columns([1,3])
    with col_r:
        st.markdown("③")
    with col_g:
        st.session_state.pro_cooldown = st.toggle(
            "冷卻期防重複",
            value=st.session_state.pro_cooldown,
            help="同股票同方向冷卻 3 根K線，通知加入距上次信號時間"
        )

    st.markdown("---")

    # Status indicator
    active_count = sum([st.session_state.pro_filter, st.session_state.pro_rsi, st.session_state.pro_cooldown])
    if active_count == 3:
        st.markdown("🟢 **專業模式**：全部啟用")
    elif active_count > 0:
        st.markdown(f"🟡 **半專業模式**：{active_count}/3 啟用")
    else:
        st.markdown("⚪ **標準模式**")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ 開始監控" if not st.session_state.monitoring else "⏹ 停止監控",
                     use_container_width=True,
                     type="primary" if not st.session_state.monitoring else "secondary"):
            st.session_state.monitoring = not st.session_state.monitoring
            st.rerun()
    with col2:
        if st.button("🗑 清除記錄", use_container_width=True):
            st.session_state.signals_log = []
            st.session_state.scan_count = 0
            st.session_state.signal_count = 0
            st.session_state.buy_count = 0
            st.session_state.sell_count = 0
            st.rerun()

    if st.button("🔍 立即掃描一次", use_container_width=True):
        with st.spinner("掃描中..."):
            run_scan(tickers, interval, st.session_state.pro_filter,
                     st.session_state.pro_rsi, st.session_state.pro_cooldown)
        st.rerun()

# ─── MAIN AREA ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📡 交易信號監控系統</h1>
    <p>TECHNICAL SIGNAL MONITOR · REAL-TIME ALERTS</p>
</div>
""", unsafe_allow_html=True)

# Metrics row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("掃描次數", st.session_state.scan_count)
with m2:
    st.metric("總信號數", st.session_state.signal_count)
with m3:
    st.metric("🟢 買入信號", st.session_state.buy_count)
with m4:
    st.metric("🔴 賣出信號", st.session_state.sell_count)

# Status bar
status_dot = "🟢" if st.session_state.monitoring else "⚫"
status_txt = "監控中" if st.session_state.monitoring else "已停止"
st.markdown(f"""
<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1rem;
     background:#1a2235;border:1px solid #2e4270;border-radius:6px;padding:0.5rem 1rem;
     font-family:'Share Tech Mono',monospace;font-size:0.82rem;color:#b8d0ec;">
    {status_dot} 狀態：{status_txt} &nbsp;|&nbsp;
    監控股票：{', '.join(tickers)} &nbsp;|&nbsp;
    週期：{interval} &nbsp;|&nbsp;
    掃描間隔：{refresh_sec}秒
</div>
""", unsafe_allow_html=True)

# Signal Log
st.markdown('<div class="section-title">📋 信號記錄</div>', unsafe_allow_html=True)

if not st.session_state.signals_log:
    st.markdown("""
    <div style="text-align:center;padding:3rem;color:#9ab8d8;
         background:#1a2235;border:1px dashed #2e4270;border-radius:8px;">
        <div style="font-size:2rem;margin-bottom:0.5rem;">📭</div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.85rem;color:#b8d0ec;">
            尚無信號記錄<br>點擊「立即掃描一次」或開始監控
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for sig in st.session_state.signals_log:
        if isinstance(sig, dict) and "direction" in sig:
            css_class = "buy" if sig["direction"] == "BUY" else "sell"
            badge_class = "badge-buy" if sig["direction"] == "BUY" else "badge-sell"
            direction_zh = "買入" if sig["direction"] == "BUY" else "賣出"
            time_str = sig["time"].strftime("%H:%M:%S") if "time" in sig else ""

            rsi_html = ""
            if st.session_state.pro_rsi:
                rsi_html = f'<span style="color:#4d9fff;margin-left:1rem;">RSI: {sig["rsi"]:.1f}</span>'

            st.markdown(f"""
            <div class="signal-card {css_class}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span class="ticker">{sig['ticker']}</span>
                        <span class="{badge_class}" style="margin-left:0.6rem;">{direction_zh}</span>
                        <span style="margin-left:0.5rem;font-size:0.9rem;">{"★"*sig['rating']}{"☆"*(5-sig['rating'])}</span>
                    </div>
                    <span class="price">${sig['price']:.2f}</span>
                </div>
                <div class="meta" style="margin-top:0.35rem;">
                    🎯 {sig['name']} &nbsp;|&nbsp;
                    ⏱ {sig['interval']} &nbsp;|&nbsp;
                    📊 均量 {sig['vol_pct']}
                    {rsi_html}
                    <span style="float:right;color:#7090b0;">{time_str}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─── Auto Refresh Loop ─────────────────────────────────────────────────────────
if st.session_state.monitoring:
    with st.spinner(f"等待下次掃描（{refresh_sec}秒）..."):
        time.sleep(refresh_sec)
    run_scan(tickers, interval, st.session_state.pro_filter,
             st.session_state.pro_rsi, st.session_state.pro_cooldown)
    st.rerun()
