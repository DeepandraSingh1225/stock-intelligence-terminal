# 🎓 Teacher Viva & Project Defense Guide: AeroQuant

Use these simple, conversational explanations to ace your college presentation and examiner questions.

---

### Q1. What dataset does your project use, and where did you get it?
**Answer:**
> "We use the **Kaggle S&P 500 Historical Stock Dataset** (`all_stocks_5yr.csv`). It contains **5 years of daily trading data across 505 companies** with 619,040 rows. Each row records the standard Open, High, Low, Close, Volume (OHLCV) and company ticker symbol."

---

### Q2. Why did you use a Single Consolidated Master File instead of individual CSV files for each company?
**Answer:**
> "Having hundreds of separate CSV files creates serious real-world engineering issues:
> 1. **Schema Mismatches:** Individual files often have missing dates, different column conventions, or corrupted lines.
> 2. **File Proliferation & High I/O Overhead:** Storing 500 separate files clogs git repositories, S3 buckets, and Docker containers, and requires opening and closing 500 file handles.
> 3. **Speed & Consistency:** A single unified master table guarantees identical column types, enables instantaneous filtered queries (`df[df['Name'] == ticker]`), and allows clean, vectorized feature engineering in Pandas."

---

### Q3. How does the 4-Tier AWS Cloud Architecture work?
**Answer:**
> "Our application follows an industry-standard 4-tier cloud pipeline:
> 1. **Data Lake (Amazon S3):** Stores the Kaggle master dataset (`all_stocks_5yr.csv`) and saved model weights.
> 2. **ML Model Training (Amazon SageMaker):** Automatically launches a Scikit-Learn container in the cloud, trains our 100-tree Random Forest classifier, and saves the serialized model package (`model.tar.gz`).
> 3. **Serverless Inference (AWS Lambda & Amazon API Gateway):** When an investor analyzes a stock, API Gateway passes the indicator payload to an AWS Lambda function (`lambda_function.py`). Lambda runs instant inference with **zero idle server cost**.
> 4. **Web Terminal & Hosting (Amazon EC2):** Our FastAPI application and quantitative engine run on an EC2 instance, providing high-speed ASGI performance and interactive Swagger API documentation (`/docs`) for users."

---

### Q3b. Why did you use FastAPI instead of traditional Flask?
**Answer:**
> "FastAPI offers three major modern advantages over Flask:
> 1. **High Performance:** Built on Starlette and ASGI (Asynchronous Server Gateway Interface), making it significantly faster for concurrent API calls.
> 2. **Data Validation:** Uses Pydantic schemas to automatically validate incoming stock and portfolio request payloads.
> 3. **Automatic Documentation:** It auto-generates interactive Swagger UI documentation at `/docs` without writing any extra code."

---

### Q4. Which Machine Learning model did you use, and why?
**Answer:**
> "I used a **Random Forest Classifier** with 100 decision trees. Each tree analyzes technical indicators (RSI, Moving Average ratio, MACD, and 20-day volatility) and votes on whether the stock will rise or fall over the next 5 days. 
> 
> We chose Random Forest because:
> - It is **explainable** — we can inspect exact feature importances.
> - It resists overfitting via bagging and bootstrap feature sampling.
> - It handles non-linear financial thresholds without requiring complex data normalization."

---

### Q5. Why did you predict trend direction instead of predicting tomorrow's exact stock price?
**Answer:**
> "Under the **Efficient Market Hypothesis (EMH)**, predicting exact tomorrow price numbers (e.g., $182.47) is prone to extreme noise and curve-fitting. Professional quantitative hedge funds do not try to guess exact pennies; instead, they forecast **directional momentum probabilities** (e.g., 62% conviction of an uptrend) and manage capital using strict risk controls like stop-loss levels."

---

### Q6. What are the key technical indicators and how are they calculated?
**Answer:**
> - **RSI (14-day):** A momentum oscillator measuring the speed of price changes:
>   $$\text{RS} = \frac{\text{Average 14-day Gain}}{\text{Average 14-day Loss}}, \quad \text{RSI} = 100 - \frac{100}{1 + \text{RS}}$$
>   RSI > 70 means Overbought (pullback risk); RSI < 30 means Oversold (dip opportunity).
> - **SMA 20 & SMA 50:** 20-day and 50-day simple moving averages to identify short-term vs. medium-term trends.
> - **MACD:** Moving Average Convergence Divergence = 12-day EMA minus 26-day EMA, plotted against a 9-day signal line.
> - **Annualized Volatility:** 20-day rolling standard deviation of daily returns multiplied by $\sqrt{252}$ trading days.

---

### Q7. How does your Dynamic 1:2 Stop-Loss and Target Price logic work?
**Answer:**
> "A quantitative trade must always have a mathematical exit strategy. Our system enforces a **1:2 Risk-to-Reward Ratio**:
> - If a stock trades at $100 and the model detects a 4% volatility buffer, the **Stop-Loss** is set at $96 (risking $4).
> - The **Take-Profit Target** is set at $108 (targeting an $8 gain).
> - This mathematical geometry guarantees that even with a modest 50% win rate, the strategy generates positive expected value because profitable trades make twice as much as losing trades lose."

---

### Q8. What is the Sharpe Ratio in your Portfolio Optimizer?
**Answer:**
> "The Sharpe Ratio measures **risk-adjusted return**:
> $$\text{Sharpe Ratio} = \frac{\text{Expected Return} - \text{Risk-Free Rate}}{\text{Portfolio Volatility}}$$
> It tells an investor how much reward they receive for every unit of volatility endured. Our engine evaluates historical return covariance across selected stocks to compute the exact capital allocation weights that maximize this Sharpe Ratio."
