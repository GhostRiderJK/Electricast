# Project Guidelines — ElectriCast

## Architecture

Full-stack electricity demand forecasting dashboard. FastAPI backend serves synthetic data matching IIT Bombay 2017 residential patterns. React frontend visualizes EDA and model predictions (LSTM, SARIMA, XGBoost).

```
backend/main.py      → FastAPI app, all endpoints, synthetic data generation
frontend/src/
  pages/             → 4 page components (EDA, Predictions, Weekly, Metrics)
  components/        → MetricsBar sticky card strip
  hooks/useData.js   → Reusable fetch hook (loading/error/data states)
  utils/api.js       → Centralized API client, all endpoint functions
  utils/chartConfig.js → Chart.js defaults, color constants, dataset helpers
```

Data flow: Page → `useData()` hook → `api.js` → Vite proxy (`/api/*`) → FastAPI → synthetic generator → JSON response → Chart.js render.

## Build and Test

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs

# Frontend
cd frontend && npm install && npm run dev
# App: http://localhost:3000

# Docker (both services)
docker-compose up --build
```

No test suite exists yet. Validate backend changes via Swagger UI at `/docs`.

## Code Style

### Backend (Python / FastAPI)
- Single-file backend (`main.py`). All endpoints, data generation, and constants live here.
- Endpoints return consistent JSON: `{"labels": [...], "actual": [...], "lstm": [...], ...}`
- Numeric values rounded to 1 decimal place.
- Numpy seed-based reproducibility (seed=42, per-endpoint seeds).
- CORS is open (`allow_origins=["*"]`) — demo only.

### Frontend (React / Vite)
- Hooks-only state management — no Redux, no Context API.
- All styling is inline React styles (no CSS-in-JS library, no Tailwind).
- Fonts: IBM Plex Mono (headings/metrics), IBM Plex Sans (body).
- Chart.js via `react-chartjs-2`. Use `lineDs()` / `barDs()` helpers from `chartConfig.js`.
- Consistent model colors: LSTM `#2563eb`, SARIMA `#dc2626`, XGBoost `#16a34a`, Actual `#111827`.

## Conventions

- **API client**: Add new endpoints as named exports in `frontend/src/utils/api.js`. Base URL reads from `VITE_API_URL` env var, defaults to `http://localhost:8000`.
- **New pages**: Follow existing pattern — fetch data via `useData()`, compose with `ChartCard`/`StatBox`/`SectionHeader` inline components, add nav link in `App.jsx`.
- **New charts**: Register required Chart.js scales/elements at page level. Use `baseChartOptions` from `chartConfig.js`.
- **Heatmap**: EDA heatmap uses custom canvas rendering (not Chart.js).
- **Model key casing**: API uses lowercase (`sarima`), MetricsBar displays `Sarima` — intentional.

## Pitfalls

- Backend is stateless in-memory synthetic data — no database, no saved models. To add real ML inference, replace `add_model_noise()` calls with model loading/prediction.
- Yearly chart defaults to `downsample=24` to prevent rendering 8,760 points.
- React StrictMode causes double mount in dev — effects fire twice.
- Vite proxy handles `/api/*` routes in dev; in Docker, Nginx proxies instead.

See [README.md](../README.md) for dataset details, model architectures, and performance metrics.
