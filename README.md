# ⚡ ElectriCast — Electricity Demand Forecasting

A deployment-ready full-stack application for residential electricity demand forecasting using LSTM, SARIMA, and XGBoost models — based on the IIT Bombay 2017 residential dataset.

---

## Project Structure

```
electricity-forecast/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── MetricsBar.jsx       # Model evaluation card strip
│   │   ├── pages/
│   │   │   ├── EDAPage.jsx          # Exploratory Data Analysis
│   │   │   ├── PredictionsPage.jsx  # Model predictions vs actual
│   │   │   ├── WeeklyPage.jsx       # Weekday/weekend patterns
│   │   │   └── MetricsPage.jsx      # Metrics comparison
│   │   ├── hooks/
│   │   │   └── useData.js           # Data fetching hook
│   │   ├── utils/
│   │   │   ├── api.js               # API client
│   │   │   └── chartConfig.js       # Chart.js defaults
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Dataset

| Property        | Value                            |
|-----------------|----------------------------------|
| Source          | IIT Bombay Residential Campus    |
| Year            | 2017                             |
| Apartments      | 39                               |
| Resolution      | Hourly (8,760 rows)              |
| Features        | W1, W2, W3 → aggregated W (Wh)  |
| Timezone        | Asia/Kolkata (IST)               |
| Train split     | Jan 1 – Jun 30, 2017 (4,344 h)  |
| Test split      | Jul 1 – Dec 31, 2017 (4,416 h)  |

### Preprocessing
- Columns used: `TS` (Unix timestamp), `W1`, `W2`, `W3` (phase loads)
- Aggregated: `W = W1 + W2 + W3`
- Timestamp converted from UTC → IST
- Resampled to hourly using `.resample('h').sum()`
- Outlier cap: `mean + 3σ`
- Zero values replaced with linear interpolation (sensor dropout)
- Features engineered: `hour_sin/cos`, `month_sin/cos`, `is_weekend`

---

## Models

### LSTM (Long Short-Term Memory)
- **Architecture:** Stacked LSTM → 64 units → Dropout(0.2) → 32 units → Dropout(0.2) → Dense(16) → Dense(1)
- **Window:** 24 hours lookback
- **Features:** `[W, hour_sin, hour_cos, month_sin, month_cos, is_weekend]`
- **Scaler:** MinMaxScaler fit on training data only
- **Callbacks:** EarlyStopping (patience=10), ReduceLROnPlateau

### SARIMA
- **Order:** SARIMA(1,1,1)(1,1,1,24)
- **Seasonal period:** 24 hours
- **Library:** `statsmodels.tsa.statespace.SARIMAX`
- **ADF test:** Used to verify stationarity before fitting

### XGBoost
- **Features:** Lag features (1h, 2h, 3h, 6h, 12h, 24h, 48h, 168h) + rolling stats (mean/std/max at 6h, 12h, 24h, 168h) + cyclical time features
- **Params:** 1000 trees, LR=0.05, max_depth=6, subsample=0.8, early_stopping=50
- **SHAP:** Feature importance via TreeExplainer

---

## Model Performance (Test: Jul–Dec 2017)

| Model   | R²      | RMSE (Wh) | MAE (Wh) | sMAPE   |
|---------|---------|-----------|----------|---------|
| SARIMA  | -1.1179 | 6807.6    | 5188.9   | 149.36% |
| LSTM    | 0.7265  | 2446.4    | 1910.2   | 45.33%  |
| XGBoost | 0.8327  | 1913.2    | 1407.7   | 37.93%  |

> sMAPE mask: W > 100 Wh (excludes sensor dropout noise from metric calculation)

---

## Running Locally

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

App runs at: http://localhost:3000

---

## API Endpoints

| Method | Path                              | Description                          |
|--------|-----------------------------------|--------------------------------------|
| GET    | `/api/metrics`                    | Overall R², RMSE, MAE, sMAPE         |
| GET    | `/api/eda/hourly`                 | Avg hourly load profile (24h)        |
| GET    | `/api/eda/daily`                  | Avg load by day of week              |
| GET    | `/api/eda/monthly`                | Monthly avg with std deviation       |
| GET    | `/api/eda/yearly`                 | Full year trend (downsampled)        |
| GET    | `/api/eda/heatmap`                | Hour × Month heatmap data            |
| GET    | `/api/eda/weekday_vs_weekend`     | Weekday vs weekend profiles          |
| GET    | `/api/eda/statistics`             | Dataset summary statistics           |
| GET    | `/api/predictions/monthly`        | Monthly avg per model (Jul–Dec)      |
| GET    | `/api/predictions/daily`          | Daily predictions, optional `?month=`|
| GET    | `/api/predictions/hourly`         | 24h prediction `?month=Aug&day=15`  |
| GET    | `/api/predictions/weekly_pattern` | Avg hourly profile per day of week   |
| GET    | `/api/predictions/monthly_errors` | MAE + RMSE per month per model       |

---

## Frontend Pages

| Page             | Content                                                                 |
|------------------|-------------------------------------------------------------------------|
| **EDA**          | Yearly trend, hourly/daily/monthly/weekly profiles, Hour×Month heatmap |
| **Predictions**  | Monthly bars, daily time-series, 24h hourly, MAE/RMSE per month        |
| **Weekly Pattern** | Day-of-week profile per model, all-days overlay                       |
| **Model Metrics** | Score cards, bar charts, comparison table with best-in-class markers  |

---

## Deployment

### Docker (recommended)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

### Environment Variables

```bash
# frontend/.env
VITE_API_URL=http://your-backend-url:8000
```

---

## Integrating Real Model Outputs

To swap synthetic data for your real trained model outputs, replace the route handlers in `backend/main.py` with code that:

1. Loads your saved model files (`.keras`, `.pkl`, `.json`)
2. Reads your preprocessed DataFrame from parquet/CSV
3. Runs inference and returns actual predictions

Example skeleton:

```python
import joblib
import pandas as pd
from tensorflow.keras.models import load_model

lstm_model  = load_model("models/lstm_monthly.keras")
xgb_model   = joblib.load("models/xgboost.pkl")
df_2017     = pd.read_parquet("data/df_2017.parquet")

@app.get("/api/predictions/monthly")
def get_monthly_predictions():
    # your real inference here
    ...
```
