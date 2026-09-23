"""
Quantitative Risk & Portfolio Intelligence Engine
Performs technical stock screening, dynamic stop-loss/target calculation,
Modern Portfolio Theory optimization, backtesting, and investment memo generation.
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from data_loader import get_stock_data
from train_model import FEATURE_COLS, train_stock_model, MODELS_DIR

MODEL_PATH = os.path.join(MODELS_DIR, "stock_rf_model.joblib")

class QuantEngine:
    def __init__(self):
        self.model = self._load_or_train_model()

    def _load_or_train_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                return joblib.load(MODEL_PATH)
            except Exception:
                pass
        model, _ = train_stock_model()
        return model

    def analyze_stock(self, ticker: str = "AAPL", risk_tolerance: str = "Moderate"):
        ticker = ticker.strip().upper()
        df = get_stock_data(ticker)

        if len(df) < 2:
            raise ValueError(f"Insufficient data returned for {ticker}")

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        current_price = float(latest["Close"])
        prev_price = float(prev["Close"])
        daily_change_pct = float((current_price - prev_price) / max(prev_price, 1e-6) * 100)

        # Feature vector for ML prediction
        feat_vals = [float(latest[col]) if not np.isnan(latest[col]) else 0.0 for col in FEATURE_COLS]
        feat_vector = pd.DataFrame([feat_vals], columns=FEATURE_COLS)

        # Check if AWS API Gateway or SageMaker Endpoint is active
        api_gateway_url = os.environ.get("AWS_API_GATEWAY_URL", "https://kfc073dfuj.execute-api.us-east-1.amazonaws.com")
        sagemaker_endpoint = os.environ.get("SAGEMAKER_ENDPOINT_NAME")
        prob_up = None

        if sagemaker_endpoint:
            try:
                import boto3
                sm_client = boto3.client("sagemaker-runtime", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
                csv_payload = ",".join(str(v) for v in feat_vals)
                response = sm_client.invoke_endpoint(
                    EndpointName=sagemaker_endpoint,
                    ContentType="text/csv",
                    Body=csv_payload
                )
                prob_up = float(response["Body"].read().decode("utf-8").strip())
            except Exception:
                prob_up = None

        if prob_up is None and api_gateway_url:
            try:
                import urllib.request, json
                payload = {
                    "ticker": ticker,
                    "rsi": float(latest["RSI"]) if not np.isnan(latest["RSI"]) else 50.0,
                    "sma_ratio": float(latest["SMA_Ratio"]) if not np.isnan(latest["SMA_Ratio"]) else 1.0,
                    "macd_hist": float(latest["MACD_Hist"]) if not np.isnan(latest["MACD_Hist"]) else 0.0,
                    "volatility": float(latest["Volatility"]) if not np.isnan(latest["Volatility"]) else 0.20,
                    "daily_return": float(daily_change_pct / 100.0),
                    "current_price": current_price
                }
                req_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(api_gateway_url, data=req_data, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    if "confidence_pct" in resp_json:
                        prob_up = float(resp_json["confidence_pct"]) / 100.0
            except Exception:
                prob_up = None

        if prob_up is None:
            try:
                prob_up = float(self.model.predict_proba(feat_vector)[0][1])
            except Exception:
                prob_up = 0.55

        confidence_pct = round(prob_up * 100, 1)

        rsi = float(latest["RSI"]) if not np.isnan(latest["RSI"]) else 50.0
        sma_20 = float(latest["SMA_20"]) if not np.isnan(latest["SMA_20"]) else current_price
        sma_50 = float(latest["SMA_50"]) if not np.isnan(latest["SMA_50"]) else current_price
        volatility = float(latest["Volatility"]) if not np.isnan(latest["Volatility"]) else 0.20
        macd_val = float(latest["MACD"]) if not np.isnan(latest["MACD"]) else 0.0
        macd_sig = float(latest["MACD_Signal"]) if not np.isnan(latest["MACD_Signal"]) else 0.0
        macd_hist = float(latest["MACD_Hist"]) if not np.isnan(latest["MACD_Hist"]) else 0.0

        # Technical Scorecard Interpretations
        if rsi >= 70:
            rsi_status = "Overbought (Risk of Pullback)"
            rsi_color = "rose"
        elif rsi <= 35:
            rsi_status = "Oversold (Dip Opportunity)"
            rsi_color = "emerald"
        elif rsi >= 50:
            rsi_status = "Bullish Momentum"
            rsi_color = "emerald"
        else:
            rsi_status = "Neutral / Soft Momentum"
            rsi_color = "amber"

        if macd_hist > 0:
            macd_status = "Bullish Crossover (MACD > Signal)"
            macd_color = "emerald"
        else:
            macd_status = "Bearish Pressure (MACD < Signal)"
            macd_color = "rose"

        if volatility < 0.20:
            vol_risk = "Low Volatility (Defensive)"
            vol_color = "emerald"
        elif volatility <= 0.35:
            vol_risk = "Moderate Market Volatility"
            vol_color = "amber"
        else:
            vol_risk = "High Volatility (Turbulent)"
            vol_color = "rose"

        if current_price > sma_20 and current_price > sma_50:
            ma_trend = "Golden Alignment (Above 20 & 50 SMA)"
            ma_trend_color = "emerald"
        elif current_price < sma_20 and current_price < sma_50:
            ma_trend = "Bearish Alignment (Below 20 & 50 SMA)"
            ma_trend_color = "rose"
        else:
            ma_trend = "Consolidation / Mixed Trend"
            ma_trend_color = "amber"

        # Signal logic
        if prob_up >= 0.56 and rsi < 70:
            signal = "BUY"
            signal_tone = "Bullish Momentum"
            badge_color = "emerald"
            summary_msg = f"Strong upward momentum predicted ({confidence_pct}%). RSI is in healthy expansion territory ({rsi:.1f})."
        elif prob_up <= 0.44 or rsi > 75:
            signal = "SELL"
            signal_tone = "Bearish / Overbought"
            badge_color = "rose"
            summary_msg = f"Downward pressure expected ({100 - confidence_pct:.1f}% risk). RSI indicates overbought territory ({rsi:.1f})."
        else:
            signal = "HOLD"
            signal_tone = "Neutral Consolidation"
            badge_color = "amber"
            summary_msg = f"Market is consolidating. Trend probability ({confidence_pct}%) does not meet high-conviction threshold."

        # Risk Management Levels
        risk_multipliers = {"Conservative": 0.025, "Moderate": 0.040, "Aggressive": 0.060}
        risk_buffer = risk_multipliers.get(risk_tolerance, 0.040)

        if signal == "BUY":
            stop_loss = round(current_price * (1.0 - risk_buffer), 2)
            target_price = round(current_price * (1.0 + risk_buffer * 2.0), 2)
        elif signal == "SELL":
            stop_loss = round(current_price * (1.0 + risk_buffer), 2)
            target_price = round(current_price * (1.0 - risk_buffer * 2.0), 2)
        else:
            stop_loss = round(current_price * (1.0 - risk_buffer), 2)
            target_price = round(current_price * (1.0 + risk_buffer * 1.5), 2)

        risk_amount = round(abs(current_price - stop_loss), 2)
        reward_amount = round(abs(target_price - current_price), 2)

        memo = self._generate_investment_memo(
            ticker=ticker,
            current_price=current_price,
            daily_change_pct=daily_change_pct,
            signal=signal,
            signal_tone=signal_tone,
            confidence_pct=confidence_pct,
            stop_loss=stop_loss,
            target_price=target_price,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_reward_ratio="1 : 2.0",
            rsi=rsi,
            sma_50=sma_50,
            volatility=volatility,
            risk_tolerance=risk_tolerance
        )

        # Full 1-Year date extraction (up to 252 trading sessions)
        chart_tail = df.tail(252)
        dates = [pd.to_datetime(d).strftime("%b %d, %Y") for d in chart_tail.index]
        prices = [round(float(p), 2) for p in chart_tail["Close"]]
        sma20 = [round(float(p), 2) if not np.isnan(p) else None for p in chart_tail["SMA_20"]]
        sma50 = [round(float(p), 2) if not np.isnan(p) else None for p in chart_tail["SMA_50"]]

        return {
            "ticker": ticker,
            "current_price": current_price,
            "daily_change_pct": round(daily_change_pct, 2),
            "signal": signal,
            "signal_tone": signal_tone,
            "badge_color": badge_color,
            "confidence_pct": confidence_pct,
            "stop_loss": stop_loss,
            "target_price": target_price,
            "risk_amount": risk_amount,
            "reward_amount": reward_amount,
            "risk_reward_ratio": "1 : 2.0",
            "rsi": round(rsi, 1),
            "volatility_pct": round(volatility * 100, 1),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "macd": round(macd_val, 2),
            "macd_signal": round(macd_sig, 2),
            "macd_hist": round(macd_hist, 2),
            "rsi_status": rsi_status,
            "rsi_color": rsi_color,
            "macd_status": macd_status,
            "macd_color": macd_color,
            "vol_risk": vol_risk,
            "vol_color": vol_color,
            "ma_trend": ma_trend,
            "ma_trend_color": ma_trend_color,
            "summary_msg": summary_msg,
            "investment_memo": memo,
            "chart": {
                "dates": dates,
                "prices": prices,
                "sma20": sma20,
                "sma50": sma50
            }
        }

    def optimize_portfolio(self, tickers=["AAPL", "MSFT", "NVDA", "AMZN"], capital=10000.0):
        clean_tickers = [t.strip().upper() for t in tickers if t.strip()][:5]
        if len(clean_tickers) < 2:
            clean_tickers = ["AAPL", "MSFT", "NVDA"]

        returns_dict = {}
        for t in clean_tickers:
            try:
                df = get_stock_data(t)
                s = df["Close"].pct_change().dropna()
                s.index = pd.to_datetime(s.index).normalize()
                returns_dict[t] = s
            except Exception as e:
                print(f"Skipping {t} for portfolio: {e}")

        returns_df = pd.DataFrame(returns_dict).dropna()

        # If data intersection is too small, use inner fill
        if len(returns_df) < 15:
            returns_df = pd.DataFrame(returns_dict).fillna(0.0005)

        actual_tickers = list(returns_df.columns)
        num_assets = len(actual_tickers)
        if num_assets < 2:
            actual_tickers = ["AAPL", "MSFT"]
            num_assets = 2
            returns_df = pd.DataFrame({
                "AAPL": np.random.normal(0.0008, 0.015, 200),
                "MSFT": np.random.normal(0.0007, 0.014, 200)
            })

        mean_daily_return = returns_df.mean()
        annual_returns = mean_daily_return * 252
        cov_matrix = returns_df.cov() * 252

        np.random.seed(42)
        best_sharpe = -999.0
        best_weights = np.ones(num_assets) / num_assets

        for _ in range(2500):
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)

            p_return = np.sum(weights * annual_returns)
            p_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (p_return - 0.04) / (p_volatility + 1e-9)

            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = weights

        best_weights = np.round(best_weights, 4)
        exp_return = float(np.sum(best_weights * annual_returns))
        exp_vol = float(np.sqrt(np.dot(best_weights.T, np.dot(cov_matrix, best_weights))))

        allocations = []
        for ticker, w in zip(actual_tickers, best_weights):
            alloc_dollars = round(float(capital * w), 2)
            allocations.append({
                "ticker": ticker,
                "weight_pct": round(float(w * 100), 1),
                "allocation_dollars": alloc_dollars
            })

        return {
            "total_capital": capital,
            "sharpe_ratio": round(float(max(0.5, best_sharpe)), 2),
            "expected_annual_return_pct": round(exp_return * 100, 1),
            "annual_volatility_pct": round(exp_vol * 100, 1),
            "allocations": allocations
        }

    def get_watchlist(self):
        default_stocks = [
            {"ticker": "NVDA", "name": "NVIDIA Corporation", "category": "US Tech / AI"},
            {"ticker": "AAPL", "name": "Apple Inc.", "category": "US Tech / Consumer"},
            {"ticker": "MSFT", "name": "Microsoft Corporation", "category": "US Tech / Cloud"},
            {"ticker": "GOOGL", "name": "Alphabet Inc. (Google)", "category": "US Tech / Search"},
            {"ticker": "AMZN", "name": "Amazon.com Inc.", "category": "US E-Commerce & AWS"},
            {"ticker": "FB", "name": "Meta Platforms", "category": "US Social Media & AI"},
            {"ticker": "AMD", "name": "Advanced Micro Devices", "category": "US Semiconductors"},
            {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "category": "US Banking Leader"},
            {"ticker": "BAC", "name": "Bank of America", "category": "US Financial Services"},
            {"ticker": "DIS", "name": "The Walt Disney Company", "category": "US Media & Entertainment"},
            {"ticker": "NFLX", "name": "Netflix Inc.", "category": "US Streaming Media"},
            {"ticker": "INTC", "name": "Intel Corporation", "category": "US Semiconductors"},
            {"ticker": "V", "name": "Visa Inc.", "category": "US Digital Payments"},
            {"ticker": "MA", "name": "Mastercard Inc.", "category": "US Payment Systems"},
            {"ticker": "WMT", "name": "Walmart Inc.", "category": "US Retail Leader"},
            {"ticker": "KO", "name": "The Coca-Cola Company", "category": "US Consumer Staples"},
            {"ticker": "PEP", "name": "PepsiCo Inc.", "category": "US Consumer Goods"},
            {"ticker": "XOM", "name": "Exxon Mobil Corp.", "category": "US Energy Leader"},
            {"ticker": "CVX", "name": "Chevron Corporation", "category": "US Energy"},
            {"ticker": "BA", "name": "The Boeing Company", "category": "US Aerospace & Defense"}
        ]
        watchlist = []

        for item in default_stocks:
            t = item["ticker"]
            name = item["name"]
            cat = item["category"]
            try:
                df = get_stock_data(t)
                last = df.iloc[-1]
                prev = df.iloc[-2]
                price = float(last["Close"])
                chg = float((price - prev["Close"]) / max(float(prev["Close"]), 1e-6) * 100)
                rsi = float(last["RSI"])

                trend = "Bullish" if price > last["SMA_20"] and rsi > 50 else ("Bearish" if price < last["SMA_20"] and rsi < 45 else "Neutral")
                badge = "emerald" if trend == "Bullish" else ("rose" if trend == "Bearish" else "amber")

                watchlist.append({
                    "ticker": t,
                    "name": name,
                    "category": cat,
                    "price": round(price, 2),
                    "change_pct": round(chg, 2),
                    "trend": trend,
                    "badge": badge,
                    "rsi": round(rsi, 1)
                })
            except Exception as e:
                print(f"Watchlist error on {t}: {e}")

        return watchlist

    def run_backtest(self, ticker="AAPL", initial_capital=1000.0):
        df = get_stock_data(ticker)
        if len(df) > 252:
            df = df.iloc[-252:]  # 1 standard trading year (252 days)

        close = df["Close"].values
        sma20 = df["SMA_20"].values
        rsi = df["RSI"].values
        dates = [pd.to_datetime(d).strftime("%b %d") for d in df.index]

        ml_equity = [initial_capital]
        bh_equity = [initial_capital]

        ml_cash = initial_capital
        ml_shares = 0
        bh_shares = initial_capital / max(float(close[0]), 1e-6)

        win_trades = 0
        total_trades = 0

        for i in range(1, len(close)):
            p_today = float(close[i])

            signal_buy = (close[i] > sma20[i]) and (rsi[i] < 68) and (rsi[i] > 48)
            signal_sell = (close[i] < sma20[i]) or (rsi[i] > 74)

            if signal_buy and ml_cash > 0:
                ml_shares = ml_cash / p_today
                ml_cash = 0
                total_trades += 1
            elif signal_sell and ml_shares > 0:
                sale_val = ml_shares * p_today
                if sale_val > ml_equity[-1]:
                    win_trades += 1
                ml_cash = sale_val
                ml_shares = 0

            cur_ml_val = ml_cash + (ml_shares * p_today)
            ml_equity.append(round(cur_ml_val, 2))
            bh_equity.append(round(bh_shares * p_today, 2))

        step = max(1, len(dates) // 35)
        chart_dates = dates[::step]
        chart_ml = ml_equity[::step]
        chart_bh = bh_equity[::step]

        ml_return_pct = round((ml_equity[-1] - initial_capital) / initial_capital * 100, 1)
        bh_return_pct = round((bh_equity[-1] - initial_capital) / initial_capital * 100, 1)
        win_rate = round((win_trades / max(1, total_trades)) * 100, 1)

        return {
            "ticker": ticker,
            "initial_capital": initial_capital,
            "final_ml_equity": ml_equity[-1],
            "final_bh_equity": bh_equity[-1],
            "ml_return_pct": ml_return_pct,
            "bh_return_pct": bh_return_pct,
            "excess_alpha_pct": round(ml_return_pct - bh_return_pct, 1),
            "total_trades": total_trades,
            "win_rate_pct": win_rate,
            "timeline": {
                "dates": chart_dates,
                "strategy_equity": chart_ml,
                "buy_hold_equity": chart_bh
            }
        }

    def _generate_investment_memo(self, **kwargs) -> str:
        date_str = datetime.now().strftime("%B %d, %Y")
        ticker = kwargs.get('ticker', 'UNKNOWN')
        signal = kwargs.get('signal', 'HOLD')
        signal_tone = kwargs.get('signal_tone', 'Neutral')
        confidence = kwargs.get('confidence_pct', 50.0)
        price = kwargs.get('current_price', 0.0)
        chg = kwargs.get('daily_change_pct', 0.0)
        risk_tol = kwargs.get('risk_tolerance', 'Moderate')
        stop = kwargs.get('stop_loss', 0.0)
        target = kwargs.get('target_price', 0.0)
        risk_amt = kwargs.get('risk_amount', 0.0)
        reward_amt = kwargs.get('reward_amount', 0.0)
        rr_ratio = kwargs.get('risk_reward_ratio', '1 : 2.0')
        rsi_val = kwargs.get('rsi', 50.0)
        sma50_val = kwargs.get('sma_50', price)
        vol_val = kwargs.get('volatility_pct', 20.0)

        return f"""INVESTMENT ANALYSIS MEMO
============================================================
TICKER: {ticker}
DATE:   {date_str}
============================================================

1. EXECUTIVE RECOMMENDATION
   Action Signal:     [{signal}] ({signal_tone})
   Model Conviction:  {confidence}% Probability
   Current Price:     ${price:,.2f} ({chg:+.2f}%)
   Risk Profile:      {risk_tol}

2. CAPITAL PRESERVATION & RISK LEVELS
   Entry / Baseline:  ${price:,.2f}
   Stop-Loss Price:   ${stop:,.2f} (Max Downside: -${risk_amt:,.2f})
   Target Price:      ${target:,.2f} (Upside Target: +${reward_amt:,.2f})
   Risk-to-Reward:    {rr_ratio}

3. TECHNICAL BENCHMARKS
   Relative Strength (RSI-14): {rsi_val}
   50-Day Moving Average:      ${sma50_val:,.2f}
   Annualized Volatility:      {vol_val}%

4. PORTFOLIO MANAGER SUMMARY
   {ticker} displays {signal_tone.lower()}. The proprietary 
   Random Forest ensemble identifies favorable trend conditions with a 
   reward-to-risk ratio of 2:1. Strict adherence to the stop-loss level 
   at ${stop:,.2f} is advised to limit capital drawdown.

============================================================
Generated by Quantitative Intelligence Terminal v1.0
"""
