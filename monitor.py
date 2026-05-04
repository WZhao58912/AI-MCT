import time
from datetime import datetime

from data.okx_client import fetch_ohlcv
from features.indicators import add_indicators
from features.structure import (
    detect_ema_structure,
    detect_volume,
    detect_wick,
    detect_range,
)
from reports.market_summary import generate_summary
from reports.chart import plot_candlestick


SYMBOL = "PENGU-USDT-SWAP"
TIMEFRAMES = ["15m", "1H", "4H"]
INTERVAL_SECONDS = 5 * 60


def detect_alerts(df, timeframe):
    alerts = []

    ema_state = detect_ema_structure(df)
    volume_state = detect_volume(df)
    wick_state = detect_wick(df)
    range_state = detect_range(df)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # 1. 放量提醒
    if volume_state == "volume_spike":
        alerts.append(f"[{timeframe}] 放量K线：当前成交量明显高于均值")

    # 2. 长上影 / 长下影
    if wick_state == "long_upper_wick":
        alerts.append(f"[{timeframe}] 长上影：上方抛压明显，注意假突破/派发")
    elif wick_state == "long_lower_wick":
        alerts.append(f"[{timeframe}] 长下影：下方承接明显，注意假跌破/反抽")

    # 3. EMA结构变化
    prev_ema_state = detect_ema_structure(df.iloc[:-1])

    if prev_ema_state != ema_state:
        alerts.append(
            f"[{timeframe}] EMA结构切换：{prev_ema_state} → {ema_state}"
        )

    # 4. 跌破/站回 EMA20
    if prev["close"] >= prev["ema20"] and last["close"] < last["ema20"]:
        alerts.append(f"[{timeframe}] 跌破 EMA20：短线结构转弱")

    if prev["close"] <= prev["ema20"] and last["close"] > last["ema20"]:
        alerts.append(f"[{timeframe}] 站回 EMA20：短线结构转强")

    # 5. 区间压缩提醒
    if range_state == "range" and ema_state == "compression":
        alerts.append(f"[{timeframe}] 区间压缩：可能接近方向选择")

    return alerts


def read_market_once(symbol=SYMBOL):
    all_alerts = []

    print("=" * 80)
    print(f"Market Scan: {symbol}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    for tf in TIMEFRAMES:
        try:
            df = fetch_ohlcv(symbol, tf, 200)
            df = add_indicators(df)

            print(f"\n===== {symbol} {tf} =====")
            print(generate_summary(df))

            chart_path = plot_candlestick(df, symbol, tf)
            print(f"图表已保存: {chart_path}")

            alerts = detect_alerts(df, tf)
            all_alerts.extend(alerts)

        except Exception as e:
            print(f"[ERROR] {tf}: {e}")

    print("\n===== Alerts =====")
    if all_alerts:
        for alert in all_alerts:
            print("⚠️", alert)
    else:
        print("暂无显著市场提醒")

    print("=" * 80)


def run_monitor():
    while True:
        read_market_once(SYMBOL)
        print(f"\n等待 {INTERVAL_SECONDS // 60} 分钟后继续扫描...\n")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run_monitor()