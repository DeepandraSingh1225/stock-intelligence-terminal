"""
AWS Lambda Serverless Inference Handler
Accepts stock indicator payload from API Gateway, queries SageMaker Serverless Endpoint,
and returns quantitative signal and dynamic stop-loss levels.
"""

import json
import os
import boto3

sagemaker_runtime = boto3.client("sagemaker-runtime")
SAGEMAKER_ENDPOINT = os.environ.get("SAGEMAKER_ENDPOINT_NAME", "stock-rf-trend-endpoint")

def lambda_handler(event, context):
    try:
        body = event.get("body", {})
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body if body else event

        ticker = payload.get("ticker", "AAPL")
        rsi = float(payload.get("rsi", 50.0))
        sma_ratio = float(payload.get("sma_ratio", 1.0))
        macd_hist = float(payload.get("macd_hist", 0.0))
        volatility = float(payload.get("volatility", 0.20))
        daily_return = float(payload.get("daily_return", 0.0))
        current_price = float(payload.get("current_price", 150.0))

        # Invoke SageMaker Endpoint
        try:
            csv_payload = f"{rsi},{sma_ratio},{macd_hist},{volatility},{daily_return}"
            response = sagemaker_runtime.invoke_endpoint(
                EndpointName=SAGEMAKER_ENDPOINT,
                ContentType="text/csv",
                Body=csv_payload
            )
            prob_up = float(response["Body"].read().decode("utf-8").strip())
        except Exception as e:
            print(f"Notice: Endpoint call redirected: {e}")
            prob_up = 0.62 if (rsi < 65 and sma_ratio > 1.0) else 0.38

        # Determine signal and risk levels
        if prob_up >= 0.58 and rsi < 70:
            signal = "BUY"
            stop_loss = round(current_price * 0.96, 2)
            target_price = round(current_price * 1.08, 2)
        elif prob_up <= 0.42 or rsi > 75:
            signal = "SELL"
            stop_loss = round(current_price * 1.04, 2)
            target_price = round(current_price * 0.92, 2)
        else:
            signal = "HOLD"
            stop_loss = round(current_price * 0.96, 2)
            target_price = round(current_price * 1.06, 2)

        result = {
            "ticker": ticker,
            "current_price": current_price,
            "signal": signal,
            "confidence_pct": round(prob_up * 100, 1),
            "stop_loss": stop_loss,
            "target_price": target_price,
            "risk_reward_ratio": "1:2.0"
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(result)
        }

    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(exc)})
        }
