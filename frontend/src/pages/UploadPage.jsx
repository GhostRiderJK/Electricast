import { useState, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";
import { api } from "../utils/api";
import { baseChartOptions, lineDs, barDs } from "../utils/chartConfig";

ChartJS.register(
  CategoryScale, LinearScale, BarElement,
  PointElement, LineElement, Filler, Tooltip, Legend
);

const CARD = {
  background: "#fff", borderRadius: 12,
  border: "1px solid #e5e7eb", padding: 24, marginBottom: 20,
};
const MONO = { fontFamily: "'IBM Plex Mono', monospace" };

function ChartCard({ title, subtitle, height = 320, children }) {
  return (
    <div style={CARD}>
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: "#111827", ...MONO }}>{title}</div>
        {subtitle && <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 2 }}>{subtitle}</div>}
      </div>
      <div style={{ height }}>{children}</div>
    </div>
  );
}

function MetricCard({ label, value, color }) {
  return (
    <div style={{
      background: `${color}08`, border: `1px solid ${color}30`,
      borderRadius: 10, padding: "12px 16px", textAlign: "center", minWidth: 100,
    }}>
      <div style={{ fontSize: 10, color: "#6b7280", fontWeight: 600, ...MONO }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color, ...MONO, marginTop: 4 }}>{value}</div>
    </div>
  );
}

export default function UploadPage() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef(null);

  async function handleFile(file) {
    if (!file) return;
    if (!file.name.endsWith(".csv")) {
      setError("Please upload a .csv file.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.uploadValidate(file);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    handleFile(file);
  }

  function onFileSelect(e) {
    handleFile(e.target.files?.[0]);
  }

  // ── Render upload zone ──────────────────────────────────────────
  if (!result && !loading) {
    return (
      <div>
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#111827", ...MONO, margin: 0 }}>
            ◈ Upload &amp; Validate
          </h2>
          <p style={{ fontSize: 12, color: "#6b7280", marginTop: 6, lineHeight: 1.6 }}>
            Upload the <b>smart_home_dataset.csv</b> to validate how models trained on
            India 2017 (Jan–Jun) perform on the first 6 months of your dataset.
            <br />
            <span style={{ color: "#9ca3af" }}>
              Note: Smart Home data (UTC, 2020s) will be converted to IST to match training timezone.
            </span>
          </p>
        </div>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          style={{
            border: `2px dashed ${dragOver ? "#2563eb" : "#d1d5db"}`,
            borderRadius: 14,
            padding: "60px 40px",
            textAlign: "center",
            cursor: "pointer",
            background: dragOver ? "#eff6ff" : "#fafbfc",
            transition: "all 0.2s",
          }}
        >
          <div style={{ fontSize: 36, marginBottom: 12 }}>📄</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#374151" }}>
            Drop smart_home_dataset.csv here
          </div>
          <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 6 }}>
            or click to browse
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            onChange={onFileSelect}
            style={{ display: "none" }}
          />
        </div>

        {error && (
          <div style={{
            marginTop: 16, padding: "12px 16px", borderRadius: 8,
            background: "#fef2f2", border: "1px solid #fecaca", color: "#dc2626",
            fontSize: 12, ...MONO,
          }}>
            {error}
          </div>
        )}

        <div style={{ ...CARD, marginTop: 24, background: "#f8fafc" }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#374151", ...MONO, marginBottom: 8 }}>
            How it works
          </div>
          <ol style={{ fontSize: 12, color: "#6b7280", margin: 0, paddingLeft: 20, lineHeight: 2 }}>
            <li>XGBoost model is trained on India residential building data — <b>Jan–Jun 2017</b></li>
            <li>Upload the <code>smart_home_dataset.csv</code> (UTC timestamps, 2020–2023)</li>
            <li>Data is converted UTC → IST and resampled to hourly</li>
            <li>Scale normalization aligns smart home values to the training data range</li>
            <li>Trained models predict on the first 6 months and metrics are computed</li>
          </ol>
        </div>
      </div>
    );
  }

  // ── Loading state ───────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "80px 0" }}>
        <div style={{ fontSize: 28, marginBottom: 16 }}>⏳</div>
        <div style={{ fontSize: 14, fontWeight: 600, color: "#374151" }}>
          Processing dataset &amp; running models…
        </div>
        <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 8 }}>
          This may take a moment
        </div>
      </div>
    );
  }

  // ── Error state ─────────────────────────────────────────────────
  if (error) {
    return (
      <div style={{ textAlign: "center", padding: "60px 0" }}>
        <div style={{
          padding: "16px 24px", borderRadius: 10, display: "inline-block",
          background: "#fef2f2", border: "1px solid #fecaca",
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#dc2626", ...MONO }}>{error}</div>
        </div>
        <div style={{ marginTop: 20 }}>
          <button
            onClick={() => { setError(null); setResult(null); }}
            style={{
              padding: "8px 20px", borderRadius: 8, border: "1px solid #d1d5db",
              background: "#fff", cursor: "pointer", fontSize: 12, fontWeight: 600,
            }}
          >Try Again</button>
        </div>
      </div>
    );
  }

  // ── Results ─────────────────────────────────────────────────────
  const { dataset_info, monthly_comparison, daily_comparison, hourly_profile, metrics, monthly_metrics } = result;

  const monthlyBarData = {
    labels: monthly_comparison.months,
    datasets: [
      barDs("Actual", monthly_comparison.actual, "rgba(26,26,46,0.75)"),
      barDs("XGBoost", monthly_comparison.xgboost, "rgba(22,163,74,0.75)"),
    ],
  };

  const dailyLineData = {
    labels: daily_comparison.labels,
    datasets: [
      lineDs("Actual", daily_comparison.actual, "actual"),
      lineDs("XGBoost", daily_comparison.xgboost, "xgboost", { dash: [4, 4] }),
    ],
  };

  const hourlyLineData = {
    labels: hourly_profile.hours,
    datasets: [
      lineDs("Actual", hourly_profile.actual, "actual", { fill: true }),
      lineDs("XGBoost", hourly_profile.xgboost, "xgboost", { dash: [4, 4] }),
    ],
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#111827", ...MONO, margin: 0 }}>
            ◈ Upload Validation Results
          </h2>
          <p style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>
            {dataset_info.filename} — {dataset_info.date_range} ({dataset_info.validation_hours} hours)
          </p>
        </div>
        <button
          onClick={() => { setResult(null); setError(null); }}
          style={{
            padding: "8px 18px", borderRadius: 8, border: "1px solid #d1d5db",
            background: "#fff", cursor: "pointer", fontSize: 11, fontWeight: 600, ...MONO,
          }}
        >↻ Upload Another</button>
      </div>

      {/* Info banner */}
      <div style={{
        ...CARD, background: "#f0f9ff", borderColor: "#bfdbfe", padding: "14px 20px",
        display: "flex", gap: 32, flexWrap: "wrap", fontSize: 11, color: "#1e3a5f",
      }}>
        <div><b style={MONO}>Timezone:</b> {dataset_info.timezone_note}</div>
        <div><b style={MONO}>Scale:</b> {dataset_info.scale_note}</div>
      </div>

      {/* Metrics cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, marginBottom: 20 }}>
        <div style={{ ...CARD, padding: "16px 20px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#16a34a", ...MONO, marginBottom: 10 }}>XGBoost</div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <MetricCard label="R²" value={metrics.xgboost.R2} color="#16a34a" />
            <MetricCard label="RMSE" value={metrics.xgboost.RMSE} color="#16a34a" />
            <MetricCard label="MAE" value={metrics.xgboost.MAE} color="#16a34a" />
            <MetricCard label="sMAPE" value={`${metrics.xgboost.sMAPE}%`} color="#16a34a" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <ChartCard title="Monthly Avg — Actual vs Predictions" subtitle="First 6 months of uploaded dataset">
          <Bar data={monthlyBarData} options={{
            ...baseChartOptions,
            plugins: { ...baseChartOptions.plugins, title: { display: false } },
          }} />
        </ChartCard>

        <ChartCard title="Avg Hourly Profile" subtitle="24-hour load pattern comparison">
          <Line data={hourlyLineData} options={baseChartOptions} />
        </ChartCard>
      </div>

      <ChartCard title="Daily Avg — Time Series" subtitle="Day-by-day comparison across validation period" height={280}>
        <Line data={dailyLineData} options={baseChartOptions} />
      </ChartCard>

      {/* Monthly metrics table */}
      {monthly_metrics && (
        <div style={CARD}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#111827", ...MONO, marginBottom: 14 }}>
            Per-Month Error Breakdown
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, ...MONO }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
                <th style={{ textAlign: "left", padding: "8px 12px", color: "#6b7280" }}>Month</th>
                <th style={{ textAlign: "right", padding: "8px 12px", color: "#16a34a" }}>XGB MAE</th>
                <th style={{ textAlign: "right", padding: "8px 12px", color: "#16a34a" }}>XGB RMSE</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(monthly_metrics).map(([month, data]) => (
                <tr key={month} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "8px 12px", fontWeight: 600, color: "#374151" }}>{month}</td>
                  <td style={{ textAlign: "right", padding: "8px 12px", color: "#16a34a" }}>{data.xgboost?.mae}</td>
                  <td style={{ textAlign: "right", padding: "8px 12px", color: "#16a34a" }}>{data.xgboost?.rmse}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
