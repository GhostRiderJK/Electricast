import { useState } from "react";
import {
  Chart, CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend, Filler
} from "chart.js";
import { Line, Bar } from "react-chartjs-2";
import { useData } from "../hooks/useData";
import { api } from "../utils/api";
import { baseChartOptions } from "../utils/chartConfig";

Chart.register(CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend, Filler);

const ALL_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

const MODEL_COLORS = {
  actual:  { border: "#111827", bg: "rgba(17,24,39,0.07)",   label: "Actual" },
  lstm:    { border: "#2563eb", bg: "rgba(37,99,235,0.08)",  label: "LSTM" },
  sarima:  { border: "#dc2626", bg: "rgba(220,38,38,0.07)",  label: "SARIMA" },
  xgboost: { border: "#16a34a", bg: "rgba(22,163,74,0.07)",  label: "XGBoost" },
};

const BAR_BG = {
  actual:  "rgba(17,24,39,0.80)",
  lstm:    "rgba(37,99,235,0.82)",
  sarima:  "rgba(220,38,38,0.82)",
  xgboost: "rgba(22,163,74,0.82)",
};

function ChartCard({ title, sub, height = 270, children }) {
  return (
    <div style={{ background: "#fff", border: "1px solid #e5e7eb",
      borderRadius: 12, padding: "18px 22px" }}>
      {title && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#374151",
            fontFamily: "'IBM Plex Mono', monospace",
            textTransform: "uppercase", letterSpacing: 0.5 }}>{title}</div>
          {sub && <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 3 }}>{sub}</div>}
        </div>
      )}
      <div style={{ height }}>{children}</div>
    </div>
  );
}

function ToggleBtn({ label, active, color, onClick }) {
  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: 6,
      padding: "5px 12px", borderRadius: 6, cursor: "pointer", border: "1.5px solid",
      borderColor: active ? color : "#e5e7eb",
      background: active ? `${color}14` : "#fff",
      transition: "all 0.15s", fontSize: 11, fontFamily: "'IBM Plex Mono', monospace",
      color: active ? color : "#9ca3af", fontWeight: 600,
    }}>
      <span style={{ width: 8, height: 8, borderRadius: 2, background: active ? color : "#d1d5db" }}/>
      {label}
    </button>
  );
}

export default function PredictionsPage() {
  const [visibleModels, setVisibleModels] = useState({
    actual: true, lstm: true, sarima: true, xgboost: true,
  });
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [selectedDay, setSelectedDay] = useState(15);

  const { data: predMonthly } = useData(api.predMonthly);
  const { data: predDaily }   = useData(api.predDaily, []);
  const { data: errData }     = useData(api.predMonthlyErrors);
  const { data: stats }       = useData(api.statistics);

  // Derive the selected month/day instead of writing state during render.
  const testMonths = predMonthly?.months || [];
  const effectiveMonth = selectedMonth ?? testMonths[0] ?? null;
  const dayOptions = effectiveMonth && predDaily
    ? predDaily.labels
        .filter(l => l.startsWith(`${effectiveMonth} `))
        .map(l => Number(l.slice(4, 6)))
        .filter(Number.isFinite)
    : [];
  const effectiveDay = dayOptions.includes(selectedDay)
    ? selectedDay
    : (dayOptions[dayOptions.length - 1] ?? selectedDay);

  const { data: predHourly } = useData(
    () => effectiveMonth ? api.predHourly(effectiveMonth, effectiveDay) : Promise.resolve(null),
    [effectiveMonth, effectiveDay]
  );

  const splitLabel = stats
    ? `${(stats.train_hours / (stats.train_hours + stats.test_hours) * 100).toFixed(1)}% / ` +
      `${(stats.test_hours / (stats.train_hours + stats.test_hours) * 100).toFixed(1)}% ` +
      `(${stats.train_hours.toLocaleString()} / ${stats.test_hours.toLocaleString()} h)`
    : "loading…";

  const toggle = (key) => setVisibleModels(p => ({ ...p, [key]: !p[key] }));

  const opts = baseChartOptions;

  function mkLineDatasets(data, keys) {
    if (!data) return [];
    return keys
      .filter(k => visibleModels[k])
      .map(k => ({
        label: MODEL_COLORS[k].label,
        data: data[k],
        borderColor: MODEL_COLORS[k].border,
        backgroundColor: MODEL_COLORS[k].bg,
        borderWidth: k === "actual" ? 2.2 : 1.6,
        borderDash: k === "lstm" ? [6,3] : k === "sarima" ? [3,2] : k === "xgboost" ? [8,3] : [],
        tension: 0.35, pointRadius: 0, pointHoverRadius: 4, fill: false,
      }));
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>

      {/* Controls */}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb",
        borderRadius: 12, padding: "16px 20px" }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#374151",
          fontFamily: "'IBM Plex Mono', monospace", textTransform: "uppercase",
          letterSpacing: 0.5, marginBottom: 12 }}>Model Visibility</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          {Object.entries(MODEL_COLORS).map(([k, v]) => (
            <ToggleBtn key={k} label={v.label} active={visibleModels[k]}
              color={v.border} onClick={() => toggle(k)} />
          ))}
          <div style={{ marginLeft: "auto", fontSize: 11, color: "#6b7280",
            fontFamily: "'IBM Plex Sans', sans-serif" }}>
            Train / Test split: {splitLabel}
          </div>
        </div>
      </div>

      {/* Monthly bar comparison */}
      <ChartCard title="Monthly Average Load — Actual vs All Models"
        sub="Average hourly load (Wh) per test month"
        height={280}>
        {predMonthly && (
          <Bar
            data={{
              labels: predMonthly.months,
              datasets: Object.entries(BAR_BG)
                .filter(([k]) => visibleModels[k])
                .map(([k, bg]) => ({
                  label: MODEL_COLORS[k].label,
                  data: predMonthly[k] || predMonthly["actual"],
                  backgroundColor: bg,
                  borderRadius: 4,
                  borderSkipped: false,
                }))
            }}
            options={{ ...opts, plugins: { ...opts.plugins } }}
          />
        )}
      </ChartCard>

      {/* Daily time series */}
      <ChartCard title="Daily Average Load — Full Test Period"
        sub="Day-by-day comparison of model predictions vs actual consumption (Wh)"
        height={280}>
        {predDaily && (
          <Line
            data={{
              labels: predDaily.labels,
              datasets: mkLineDatasets(predDaily, ["actual","lstm","sarima","xgboost"])
            }}
            options={{
              ...opts,
              scales: {
                ...opts.scales,
                x: { ...opts.scales.x, ticks: { ...opts.scales.x.ticks, maxTicksLimit: 12 } }
              }
            }}
          />
        )}
      </ChartCard>

      {/* Hourly single-day prediction */}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 14, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#374151",
              fontFamily: "'IBM Plex Mono', monospace",
              textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6 }}>
              Hourly Prediction — Select Day
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {testMonths.map(m => (
                <button key={m} onClick={() => setSelectedMonth(m)} style={{
                  padding: "4px 12px", borderRadius: 6, cursor: "pointer",
                  border: "1.5px solid",
                  borderColor: effectiveMonth === m ? "#2563eb" : "#e5e7eb",
                  background: effectiveMonth === m ? "#eff6ff" : "#fff",
                  color: effectiveMonth === m ? "#2563eb" : "#6b7280",
                  fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, fontWeight: 600,
                }}>{m}</button>
              ))}
              <select value={effectiveDay} onChange={e => setSelectedDay(Number(e.target.value))}
                disabled={dayOptions.length === 0}
                style={{ padding: "4px 10px", borderRadius: 6,
                  border: "1.5px solid #e5e7eb", fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 11, color: "#374151", cursor: "pointer", background: "#fff" }}>
                {dayOptions.map(d => (
                  <option key={d} value={d}>Day {d}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        <ChartCard height={270}>
          {predHourly && (
            <Line
              data={{
                labels: predHourly.labels,
                datasets: mkLineDatasets(predHourly, ["actual","lstm","sarima","xgboost"])
              }}
              options={{
                ...opts,
                plugins: {
                  ...opts.plugins,
                  title: {
                    display: true,
                    text: `24-Hour Prediction — ${predHourly.date}`,
                    color: "#374151",
                    font: { family: "'IBM Plex Mono', monospace", size: 11 },
                    padding: { bottom: 8 }
                  }
                }
              }}
            />
          )}
        </ChartCard>
      </div>

      {/* Per-month error breakdown — MAE */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <ChartCard title="Monthly MAE — All Models"
          sub="Mean Absolute Error (Wh) per test month" height={240}>
          {errData && (
            <Bar
              data={{
                labels: errData.months,
                datasets: [
                  { label: "LSTM MAE",    data: errData.months.map(m => errData.lstm[m].mae),    backgroundColor: "rgba(37,99,235,0.78)",  borderRadius: 4 },
                  { label: "SARIMA MAE",  data: errData.months.map(m => errData.sarima[m].mae),  backgroundColor: "rgba(220,38,38,0.78)",  borderRadius: 4 },
                  { label: "XGBoost MAE", data: errData.months.map(m => errData.xgboost[m].mae), backgroundColor: "rgba(22,163,74,0.78)",  borderRadius: 4 },
                ].filter((_, i) => [visibleModels.lstm, visibleModels.sarima, visibleModels.xgboost][i])
              }}
              options={opts}
            />
          )}
        </ChartCard>

        <ChartCard title="Monthly RMSE — All Models"
          sub="Root Mean Square Error (Wh) per test month" height={240}>
          {errData && (
            <Bar
              data={{
                labels: errData.months,
                datasets: [
                  { label: "LSTM RMSE",    data: errData.months.map(m => errData.lstm[m].rmse),    backgroundColor: "rgba(37,99,235,0.42)",  borderRadius: 4 },
                  { label: "SARIMA RMSE",  data: errData.months.map(m => errData.sarima[m].rmse),  backgroundColor: "rgba(220,38,38,0.42)",  borderRadius: 4 },
                  { label: "XGBoost RMSE", data: errData.months.map(m => errData.xgboost[m].rmse), backgroundColor: "rgba(22,163,74,0.42)",  borderRadius: 4 },
                ].filter((_, i) => [visibleModels.lstm, visibleModels.sarima, visibleModels.xgboost][i])
              }}
              options={opts}
            />
          )}
        </ChartCard>
      </div>
    </div>
  );
}
