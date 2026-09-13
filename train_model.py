"""
Model Training & Evaluation Script
Trains an easy, explainable Random Forest Classifier to predict 5-day market trend direction.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

from data_loader import get_stock_data

PROJECT_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(PROJECT_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

FEATURE_COLS = ["RSI", "SMA_Ratio", "MACD_Hist", "Volatility", "Daily_Return"]

def train_stock_model(tickers=["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]):
    print("==================================================")
    print("TRAINING RANDOM FOREST TREND PREDICTOR")
    print("==================================================")

    frames = []
    for t in tickers:
        try:
            df = get_stock_data(t, period="3y")
            frames.append(df)
        except Exception as e:
            print(f"Skipping {t}: {e}")

    if not frames:
        df_aapl = get_stock_data("AAPL", period="3y")
        frames = [df_aapl]

    combined_df = pd.concat(frames)
    print(f"Total dataset size: {len(combined_df)} historical trading rows across {len(frames)} tickers.")

    X = combined_df[FEATURE_COLS]
    y = combined_df["Target"]

    # Chronological train/test split (80% past train, 20% recent test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # Train Random Forest Classifier
    # 100 Decision Trees voting on trend direction
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42
    )
    clf.fit(X_train, y_train)

    # Evaluation
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print("\nModel Evaluation Results (Test Set):")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")

    # Feature Importance
    importances = dict(sorted(zip(FEATURE_COLS, [round(float(x), 4) for x in clf.feature_importances_]), key=lambda x: x[1], reverse=True))
    print("\nFeature Importances:", importances)

    metrics = {
        "model_type": "Random Forest Classifier (100 Trees)",
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "feature_importances": importances
    }

    # Save artifacts
    model_path = os.path.join(MODELS_DIR, "stock_rf_model.joblib")
    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    joblib.dump(clf, model_path)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nModel saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")
    return clf, metrics

if __name__ == "__main__":
    train_stock_model()
