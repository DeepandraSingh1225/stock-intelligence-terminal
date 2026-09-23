"""
FastAPI Server for Quantitative Stock Intelligence Terminal
Serves static frontend assets and exposes high-performance REST API endpoints
for stock analysis, portfolio optimization, market watchlist, and backtesting.
Interactive Swagger API documentation available at: /docs
"""

import os
import traceback
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from quant_engine import QuantEngine

app = FastAPI(
    title="AeroQuant Financial Intelligence API",
    description="Quantitative Financial Analytics & Machine Learning Inference API",
    version="2.0.0"
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = QuantEngine()

# Pydantic Schemas for Request Validation & Interactive Swagger Docs
class AnalyzeRequest(BaseModel):
    ticker: Optional[str] = "AAPL"
    risk_tolerance: Optional[str] = "Moderate"

class OptimizeRequest(BaseModel):
    tickers: Optional[List[str]] = ["AAPL", "MSFT", "NVDA", "AMZN"]
    capital: Optional[float] = 10000.0

class BacktestRequest(BaseModel):
    ticker: Optional[str] = "AAPL"
    capital: Optional[float] = 1000.0

@app.get("/")
def index():
    """Serves the main quantitative financial terminal UI."""
    return FileResponse("frontend/index.html")

@app.post("/api/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    """Generates AI signal, technical scorecard, and 1:2 risk-reward levels for a stock."""
    try:
        ticker = req.ticker or "AAPL"
        risk_tolerance = req.risk_tolerance or "Moderate"
        return engine.analyze_stock(ticker=ticker, risk_tolerance=risk_tolerance)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize")
def optimize_endpoint(req: OptimizeRequest):
    """Calculates optimal Sharpe Ratio portfolio allocation across assets."""
    try:
        tickers = req.tickers or ["AAPL", "MSFT", "NVDA", "AMZN"]
        capital = float(req.capital or 10000.0)
        return engine.optimize_portfolio(tickers=tickers, capital=capital)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/watchlist")
def watchlist_endpoint():
    """Returns real-time indicators and trend momentum badges for top market leaders."""
    try:
        items = engine.get_watchlist()
        return {"watchlist": items}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backtest")
def backtest_endpoint(req: BacktestRequest):
    """Simulates 1-year historical trading performance vs Buy & Hold benchmark."""
    try:
        ticker = req.ticker or "AAPL"
        capital = float(req.capital or 1000.0)
        return engine.run_backtest(ticker=ticker, initial_capital=capital)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "=" * 65)
    print("Quantitative Stock Intelligence Terminal (FastAPI) Running at:")
    print(f"  * Web Terminal: http://127.0.0.1:{port}")
    print(f"  * Swagger Docs: http://127.0.0.1:{port}/docs")
    print("=" * 65 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
