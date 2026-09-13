"""
Data Loader & Technical Indicator Pipeline
Fetches historical stock market data using yfinance and computes technical indicators.
Includes offline local caching, timezone normalization, and synthetic fallback.
"""

import os
import numpy as np
import pandas as pd
import yfinance as yf

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates standard Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def compute_macd(series: pd.Series) -> (pd.Series, pd.Series):
    """Calculates MACD (12, 26, 9)."""
    exp12 = series.ewm(span=12, adjust=False).mean()
    exp26 = series.ewm(span=26, adjust=False).mean()
    macd = exp12 - exp26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def generate_fallback_stock_data(ticker: str, days: int = 400) -> pd.DataFrame:
    """Generates realistic daily price series if offline."""
    np.random.seed(abs(hash(ticker)) % 10000)
    # Use bdate_range with normalize
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    n = len(dates)
    
    base_price = 150.0 if "AAPL" in ticker else (2500.0 if "RELIANCE" in ticker else 500.0)
    daily_returns = np.random.normal(0.0006, 0.018, size=n)
    price_series = base_price * np.exp(np.cumsum(daily_returns))
    
    high = price_series * np.random.uniform(1.002, 1.02, size=n)
    low = price_series * np.random.uniform(0.98, 0.998, size=n)
    open_p = price_series * np.random.uniform(0.995, 1.005, size=n)
    volume = np.random.randint(1000000, 50000000, size=n)

    df = pd.DataFrame({
        "Date": dates,
        "Open": np.round(open_p, 2),
        "High": np.round(high, 2),
        "Low": np.round(low, 2),
        "Close": np.round(price_series, 2),
        "Volume": volume
    }).set_index("Date")
    return df

def get_stock_data(ticker: str = "AAPL", period: str = "2y", use_cache: bool = True) -> pd.DataFrame:
    """
    Retrieves stock data via yfinance with local caching, timezone stripping, and offline fallback.
    """
    clean_ticker = ticker.strip().upper()
    cache_path = os.path.join(DATA_DIR, f"{clean_ticker}.csv")

    df = None
    if use_cache and os.path.exists(cache_path):
        try:
            df = pd.read_csv(cache_path, index_col=0)
            df.index = pd.to_datetime(df.index, utc=True).tz_convert(None).normalize()
        except Exception:
            df = None

    if df is None or len(df) < 50:
        try:
            print(f"Fetching live market data for {clean_ticker} from Yahoo Finance...")
            stock = yf.Ticker(clean_ticker)
            raw = stock.history(period=period)

            # Flatten MultiIndex columns if present
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = [col[0] for col in raw.columns]

            if raw is not None and not raw.empty and len(raw) > 30:
                raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(None).normalize()
                raw.index.name = "Date"
                df = raw
                df.to_csv(cache_path)
            else:
                raise ValueError(f"Empty data returned for {clean_ticker}")
        except Exception as e:
            print(f"Notice: Network/API fetch failed ({e}). Loading fallback data for {clean_ticker}...")
            df = generate_fallback_stock_data(clean_ticker)
            df.to_csv(cache_path)

    # Clean index
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(None).normalize()
    df.index.name = "Date"

    # Ensure numeric columns
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Calculate Technical Indicators
    close = df["Close"]
    df["SMA_20"] = close.rolling(window=20).mean()
    df["SMA_50"] = close.rolling(window=50).mean()
    df["RSI"] = compute_rsi(close, 14)
    macd, signal = compute_macd(close)
    df["MACD"] = macd
    df["MACD_Signal"] = signal
    df["MACD_Hist"] = macd - signal

    # 20-Day Price Volatility (annualized)
    df["Daily_Return"] = close.pct_change()
    df["Volatility"] = df["Daily_Return"].rolling(window=20).std() * np.sqrt(252)

    # Momentum Ratio: Price vs SMA_50
    df["SMA_Ratio"] = close / (df["SMA_50"] + 1e-9)

    # Forward 5-day direction target
    future_return = close.shift(-5) / close - 1.0
    df["Target"] = (future_return > 0.005).astype(int)

    # Fill NaNs for rolling indicators
    df["SMA_20"] = df["SMA_20"].bfill()
    df["SMA_50"] = df["SMA_50"].bfill()
    df["Volatility"] = df["Volatility"].fillna(0.20)
    df["Daily_Return"] = df["Daily_Return"].fillna(0.0)
    df["SMA_Ratio"] = df["SMA_Ratio"].fillna(1.0)
    df["MACD_Hist"] = df["MACD_Hist"].fillna(0.0)

    return df

if __name__ == "__main__":
    test_df = get_stock_data("AAPL")
    print(f"Loaded {len(test_df)} trading days for AAPL.")
    print("Columns:", list(test_df.columns))
