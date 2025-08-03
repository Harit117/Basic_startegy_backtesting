import yfinance as yf
import pandas as pd

tickers = ["SPY", "AAPL", "NVDA", "MSFT", "IBM", "DIS", "HOOD"]

end_date = pd.Timestamp.today().date()
start_date = end_date - pd.DateOffset(years=10)

for ticker in tickers:
    print(f"Downloading {ticker}...")
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if data.empty:
        print(f"⚠️ No data found for {ticker}")
    else:
        data.to_csv(f"{ticker}_10yr.csv")
        print(f"✅ Saved {ticker}_10yr.csv")
