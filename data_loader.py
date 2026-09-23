"""
Data Loader & Technical Indicator Pipeline
Dataset: Kaggle S&P 500 Unified Dataset (all_stocks_5yr.csv)
505 companies, 5 years of daily trading data.
"""

import os
import numpy as np
import pandas as pd

# Path to the master Kaggle dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "all_stocks_5yr.csv")

# Global in-memory cache to load CSV once for high performance
_MASTER_DF = None

def get_master_dataframe() -> pd.DataFrame:
    """Loads and caches the master S&P 500 dataset in memory."""
    global _MASTER_DF
    if _MASTER_DF is None:
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Master dataset not found at {DATA_PATH}")
        _MASTER_DF = pd.read_csv(DATA_PATH)
    return _MASTER_DF

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculates Relative Strength Index (RSI).
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss over 14 trading days.
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    
    rs = gain / (loss + 1e-9)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)

def compute_macd(series: pd.Series):
    """
    Calculates Moving Average Convergence Divergence (MACD).
    MACD Line = 12-day EMA - 26-day EMA
    Signal Line = 9-day EMA of MACD Line
    Histogram = MACD Line - Signal Line
    """
    ema_12 = series.ewm(span=12, adjust=False).mean()
    ema_26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

def get_stock_data(ticker: str = "AAPL") -> pd.DataFrame:
    """
    Extracts historical OHLCV data for a specific ticker from the master dataset,
    and computes standard technical indicators for machine learning and quantitative analysis.
    """
    clean_ticker = ticker.strip().upper()
    # Common ticker aliases (e.g., Meta was traded as FB in 2013-2018)
    aliases = {"META": "FB", "GOOG": "GOOGL"}
    clean_ticker = aliases.get(clean_ticker, clean_ticker)

    df_master = get_master_dataframe()

    # 1. Filter rows for requested company
    stock_df = df_master[df_master["Name"] == clean_ticker].copy()

    if stock_df.empty or len(stock_df) < 50:
        # Fallback to AAPL if ticker not found or too few rows
        print(f"Ticker '{clean_ticker}' not found in S&P 500 dataset. Defaulting to AAPL.")
        stock_df = df_master[df_master["Name"] == "AAPL"].copy()

    # 2. Standardize column names
    stock_df = stock_df.rename(columns={
        "date": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume"
    })

    # 3. Format Date index
    stock_df["Date"] = pd.to_datetime(stock_df["Date"])
    stock_df = stock_df.sort_values("Date").set_index("Date")

    # 4. Ensure numeric types
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        stock_df[col] = pd.to_numeric(stock_df[col], errors="coerce")
    stock_df = stock_df.ffill().bfill()

    close = stock_df["Close"]

    # 5. Simple Moving Averages (20-day and 50-day)
    stock_df["SMA_20"] = close.rolling(window=20).mean().bfill()
    stock_df["SMA_50"] = close.rolling(window=50).mean().bfill()
    stock_df["SMA_Ratio"] = (close / (stock_df["SMA_50"] + 1e-9)).fillna(1.0)

    # 6. Relative Strength Index (14-day momentum)
    stock_df["RSI"] = compute_rsi(close, period=14)

    # 7. MACD Momentum
    macd, signal, hist = compute_macd(close)
    stock_df["MACD"] = macd
    stock_df["MACD_Signal"] = signal
    stock_df["MACD_Hist"] = hist.fillna(0.0)

    # 8. Daily Return & 20-Day Annualized Volatility
    # Volatility = Standard Deviation of Daily Returns * sqrt(252 trading days)
    stock_df["Daily_Return"] = close.pct_change().fillna(0.0)
    stock_df["Volatility"] = (stock_df["Daily_Return"].rolling(window=20).std() * np.sqrt(252)).fillna(0.20)

    # 9. Machine Learning Target (Binary Classification)
    # Target = 1 if price rises by > 0.5% over next 5 trading days, else 0
    future_return = close.shift(-5) / close - 1.0
    stock_df["Target"] = (future_return > 0.005).astype(int)

    return stock_df

def get_available_tickers() -> list:
    """Returns sorted list of all 505 tickers available in the master S&P 500 dataset."""
    df_master = get_master_dataframe()
    return sorted(df_master["Name"].dropna().unique().tolist())

if __name__ == "__main__":
    df = get_stock_data("AAPL")
    print("=" * 60)
    print("KAGGLE S&P 500 DATASET VERIFICATION")
    print("=" * 60)
    print(f"Loaded {len(df)} daily trading rows for AAPL.")
    print("Date Range:", df.index.min().strftime('%Y-%m-%d'), "to", df.index.max().strftime('%Y-%m-%d'))
    print("Available Columns:", list(df.columns))
    print(f"Total Unique Tickers in Dataset: {len(get_available_tickers())}")
    print("\nSample Row:")
    print(df[["Close", "SMA_20", "SMA_50", "RSI", "MACD_Hist", "Volatility", "Target"]].tail(1))
