# 🎓 Teacher Viva & Project Defense Guide: AeroQuant

Use these simple, conversational explanations to ace your college presentation and examiner questions.

---

### Q1. Which Machine Learning model did you use, and why?
**Answer:**
> "I used a **Random Forest Classifier**. It works like an ensemble or 'committee' of 100 decision trees. Each individual tree examines technical indicators (RSI, Moving Averages, MACD, and volatility) and votes on whether the stock will rise or fall over the next 5 days. The majority vote determines the final signal. Random Forest was chosen because it resists overfitting, handles non-linear financial patterns effectively, and provides clear feature importances."

---

### Q2. Why did you predict market trend direction instead of predicting tomorrow's exact stock price?
**Answer:**
> "Under the **Efficient Market Hypothesis (EMH)**, predicting exact tomorrow price numbers (like $182.47) is prone to extreme noise and curve-fitting. Professional quantitative funds do not try to guess exact prices; instead, they forecast **trend probabilities** (e.g., 65% probability of positive momentum over the next week) and manage capital using strict risk controls like stop-loss levels."

---

### Q3. What is the Relative Strength Index (RSI)?
**Answer:**
> "RSI is a momentum oscillator measuring price velocity on a scale from 0 to 100:
> - **RSI > 70:** Indicates the stock is **Overbought** (price has risen too fast, higher risk of pullback).
> - **RSI < 30:** Indicates the stock is **Oversold** (price is deeply discounted, potential bounce).
> - **RSI between 45 and 65:** Indicates steady, healthy upward momentum."

---

### Q4. How does your Dynamic Stop-Loss and Target Price logic work?
**Answer:**
> "A trade should never be taken without a defined exit plan. Our system uses a **1:2 Risk-to-Reward Ratio**:
> - If a stock trades at $100 and has a 4% risk buffer, the **Stop-Loss** is placed at $96 (risking $4).
> - The **Take-Profit Target** is automatically calculated at $108 (targeting an $8 gain).
> - This ensures that even with a 50% win rate, the strategy remains profitable over time because winners earn twice as much as losers lose."

---

### Q5. What is the Sharpe Ratio in your Portfolio Optimizer?
**Answer:**
> "The Sharpe Ratio measures **risk-adjusted return**:
> $$\text{Sharpe Ratio} = \frac{\text{Expected Return} - \text{Risk-Free Rate}}{\text{Portfolio Volatility}}$$
> It tells an investor how much excess return they receive for the extra volatility endured. A Sharpe ratio above 1.0 is considered good, and above 1.5 is excellent. Our optimizer runs Monte Carlo simulations to find the exact combination of stock weights that maximizes this ratio."

---

### Q6. How does AWS SageMaker fit into this architecture?
**Answer:**
> "- **Amazon S3:** Stores our historical daily market data lake and serialized model checkpoints.
> - **SageMaker SKLearn Estimator:** Automates cloud training on an EC2 instance without tying up our local computer.
> - **SageMaker Serverless Endpoint:** Hosts the trained Random Forest model in the cloud. It automatically scales down to zero instances when no queries are made, resulting in near-zero hosting cost."
