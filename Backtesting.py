import pandas as pd
import backtrader as bt
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

class PandasFeed(bt.feeds.PandasData):
    params = (('datetime', 0), ('open', 1), ('high', 2),
              ('low', 3), ('close', 4), ('volume', 5), ('openinterest', -1))

class SMAMACDStrategy(bt.Strategy):
    def __init__(self):
        self.sma20 = bt.indicators.SMA(self.data.close, period=20)
        self.sma50 = bt.indicators.SMA(self.data.close, period=50)
        self.macd = bt.indicators.MACD(self.data.close)
        self.macd_line = self.macd.macd
        self.signal_line = self.macd.signal
        self.win_count = 0
        self.loss_count = 0

    def notify_trade(self, trade):
        if trade.isclosed:
            if trade.pnl > 0:
                self.win_count += 1
            elif trade.pnl < 0:
                self.loss_count += 1

    def next(self):
        if len(self) < 50:
            return
        if not self.position:
            if self.sma20[0] > self.sma50[0] and self.sma20[-1] <= self.sma50[-1] and self.macd_line[0] > self.signal_line[0]:
                size = int(self.broker.get_cash() / self.data.close[0])
                self.buy(size=size)
        else:
            if self.sma20[0] < self.sma50[0] and self.sma20[-1] >= self.sma50[-1] and self.macd_line[0] < self.signal_line[0]:
                self.close()

class PerformanceAnalyzer(bt.Analyzer):
    def __init__(self):
        self.values = []

    def next(self):
        self.values.append(self.strategy.broker.get_value())

    def get_analysis(self):
        returns_series = pd.Series(self.values).pct_change().dropna()
        mean = returns_series.mean()
        std = returns_series.std()
        sharpe = (mean / std) * (252**0.5) if std != 0 else 0
        return {
            'final_value': self.values[-1],
            'initial_value': self.values[0],
            'percent_change': ((self.values[-1] - self.values[0]) / self.values[0]) * 100,
            'sharpe': sharpe
        }

tickers = ['SPY', 'AAPL', 'NVDA', 'MSFT', 'IBM', 'DIS', 'HOOD']
performance_summary = {}

for symbol in tickers:
    filename = f'{symbol}_10yr.csv'
    if not os.path.exists(filename):
        print(f"❌ {symbol} data not found.")
        continue

    df = pd.read_csv(filename, skiprows=3, names=[
        'Date', 'Close', 'High', 'Low', 'Open', 'Volume'])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[df['Date'] >= datetime.now() - timedelta(days=365 * 10)]
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

    cerebro = bt.Cerebro()
    cerebro.addstrategy(SMAMACDStrategy)
    datafeed = PandasFeed(dataname=df)
    cerebro.adddata(datafeed)
    cerebro.broker.set_cash(1000)
    cerebro.addanalyzer(PerformanceAnalyzer, _name='performance')
    results = cerebro.run()
    strategy = results[0]
    perf = strategy.analyzers.performance.get_analysis()

    trades = strategy.win_count + strategy.loss_count
    win_ratio = (strategy.win_count / trades) * 100 if trades else 0
    days = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
    years = days / 365
    annualized_return = ((perf['final_value'] / perf['initial_value']) ** (1 / years) - 1) * 100

    print(f"\n📊 {symbol} Results:")
    print(f"   Final Value: ${perf['final_value']:.2f}")
    print(f"   % Capital Increase: {perf['percent_change']:.2f}%")
    print(f"   Win Ratio: {win_ratio:.2f}%")
    print(f"   Sharpe Ratio: {perf['sharpe']:.4f}")
    performance_summary[symbol] = annualized_return

plt.figure(figsize=(10, 6))
bars = plt.bar(performance_summary.keys(), performance_summary.values(),
               color='teal', edgecolor='black')
plt.axhline(0, color='gray', linestyle='--')
plt.title('📈 Annualized Return by Ticker')
plt.ylabel('Annualized Return (%)')
plt.xlabel('Ticker')

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5,
             f'{yval:.2f}%', ha='center', va='bottom')

plt.tight_layout()
plt.show()
