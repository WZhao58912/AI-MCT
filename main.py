from data.okx_client import fetch_ohlcv
from features.indicators import add_indicators
from reports.market_summary import generate_summary
from reports.chart import plot_candlestick

def run():
    symbol = "PENGU-USDT-SWAP"
    timeframes = ["15m", "1H", "4H"]

    for tf in timeframes:
        df = fetch_ohlcv(symbol, tf, 200)
        df = add_indicators(df)

        print(f"\n===== {symbol} {tf} =====")
        print(generate_summary(df))

        chart_path = plot_candlestick(df, symbol, tf)
        print(f"图表已保存: {chart_path}")

if __name__ == "__main__":
    run()
