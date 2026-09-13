"""
Flask API Server for Quantitative Stock Intelligence Terminal
Serves static frontend assets and exposes REST API endpoints for stock analysis,
portfolio optimization, market watchlist, and backtesting.
"""

import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from quant_engine import QuantEngine

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

engine = QuantEngine()

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze_endpoint():
    data = request.json or {}
    ticker = data.get("ticker", "AAPL")
    risk_tolerance = data.get("risk_tolerance", "Moderate")
    try:
        result = engine.analyze_stock(ticker=ticker, risk_tolerance=risk_tolerance)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/optimize", methods=["POST"])
def optimize_endpoint():
    data = request.json or {}
    tickers = data.get("tickers", ["AAPL", "MSFT", "NVDA", "AMZN"])
    capital = float(data.get("capital", 10000.0))
    try:
        result = engine.optimize_portfolio(tickers=tickers, capital=capital)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/watchlist", methods=["GET"])
def watchlist_endpoint():
    try:
        items = engine.get_watchlist()
        return jsonify({"watchlist": items})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/backtest", methods=["POST"])
def backtest_endpoint():
    data = request.json or {}
    ticker = data.get("ticker", "AAPL")
    capital = float(data.get("capital", 1000.0))
    try:
        result = engine.run_backtest(ticker=ticker, initial_capital=capital)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")
    print("\n" + "="*65)
    print("📈 Quantitative Stock Intelligence Terminal Running at:")
    print(f"👉 http://127.0.0.1:{port}")
    print("="*65 + "\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
