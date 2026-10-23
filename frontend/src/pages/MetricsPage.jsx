import {
  Chart, CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend
} from "chart.js";
import { Bar } from "react-chartjs-2";
import { useData } from "../hooks/useData";
import { api } from "../utils/api";
import { baseChartOptions } from "../utils/chartConfig";

Chart.register(CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend);

const MODELS = [
  { key: "lstm",    label: "LSTM",    color: "#2563eb", bg: "rgba(37,99,235,0.15)" },
  { key: "sarima",  label: "SARIMA",  color: "#dc2626", bg: "rgba(220,38,38,0.15)" },
  { key: "xgboost", label: "XGBoost", color: "#16a34a", bg: "rgba(22,163,74,0.15)" },
];

function ScoreBadge({ label, value, best, type }) {
  const isBest = value === best;
  return (
    <div style={{
      textAlign: "center", padding: "12px 10px",
      background: isBest ? "#f0fdf4" : "#f9fafb",
      border: `1.5px solid ${isBest ? "#16a34a" : "#e5e7eb"}`,
      borderRadius: 8, position: "relative",
    }}>
      {isBest && (
        <div style={{ position: "absolute", top: -8, left: "50%", transform: "translateX(-50%)",
          background: "#16a34a", color: "#fff", fontSize: 8, fontWeight: 700,
          padding: "1px 7px", borderRadius: 10, fontFamily: "'IBM Plex Mono', monospace",
          whiteSpace: "nowrap" }}>BEST</div>
      )}
      <div style={{ fontSize: 9, color: "#9ca3af", fontFamily: "'IBM Plex Sans', sans-serif",
        textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</div>
      <div style={{ fontSize: 17, fontWeight: 700,
        fontFamily: "'IBM Plex Mono', monospace",
        color: isBest ? "#16a34a" : "#111827", marginTop: 3 }}>
        {typeof value === "number" ? value.toFixed(type === "r2" ? 4 : type === "pct" ? 1 : 0) : value}
        {type === "pct" && "%"}
        {type === "wh" && " kWh"}
      </div>
    </div>
  );
}

export default function MetricsPage() {
  const { data, loading } = useData(api.metrics);
  const opts = baseChartOptions;

  if (loading || !data) {
    return <div style={{ color: "#9ca3af", fontFamily: "'IBM Plex Mono', monospace" }}>Loading metrics...</div>;
  }

  const bestR2    = Math.max(...MODELS.map(m => data[m.key].R2));
  const bestRmse  = Math.min(...MODELS.map(m => data[m.key].RMSE));
  const bestMae   = Math.min(...MODELS.map(m => data[m.key].MAE));
  const bestSmape = Math.min(...MODELS.map(m => data[m.key].sMAPE));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>

      {/* Score cards per model */}
      {MODELS.map(({ key, label, color }) => {
        const m = data[key];
        return (
          <div key={key} style={{ background: "#fff", border: "1px solid #e5e7eb",
            borderRadius: 12, padding: "18px 22px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: color }}/>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#111827",
                fontFamily: "'IBM Plex Mono', monospace" }}>{label}</div>
              <div style={{ fontSize: 11, color: "#9ca3af", marginLeft: 6,
                fontFamily: "'IBM Plex Sans', sans-serif" }}>{m.description}</div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
              <ScoreBadge label="R² Score" value={m.R2}    best={bestR2}    type="r2" />
              <ScoreBadge label="RMSE"     value={m.RMSE}  best={bestRmse}  type="wh" />
              <ScoreBadge label="MAE"      value={m.MAE}   best={bestMae}   type="wh" />
              <ScoreBadge label="sMAPE"    value={m.sMAPE} best={bestSmape} type="pct" />
            </div>
          </div>
        );
      })}

      {/* Side-by-side bar charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>

        <div style={{ background: "#fff", border: "1px solid #e5e7eb",
          borderRadius: 12, padding: "18px 22px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#374151",
            fontFamily: "'IBM Plex Mono', monospace",
            textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 14 }}>
            R² Score Comparison
          </div>
          <div style={{ height: 220 }}>
            <Bar
              data={{
                labels: MODELS.map(m => m.label),
                datasets: [{
                  label: "R²",
                  data: MODELS.map(m => data[m.key].R2),
                  backgroundColor: MODELS.map(m => m.bg.replace("0.15", "0.82")),
                  borderColor: MODELS.map(m => m.color),
                  borderWidth: 1.5,
                  borderRadius: 6,
                }]
              }}
              options={{
                ...opts,
                scales: {
                  ...opts.scales,
                  y: { ...opts.scales.y }
                }
              }}
            />
          </div>
        </div>

        <div style={{ background: "#fff", border: "1px solid #e5e7eb",
          borderRadius: 12, padding: "18px 22px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#374151",
            fontFamily: "'IBM Plex Mono', monospace",
            textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 14 }}>
            sMAPE Comparison (lower = better)
          </div>
          <div style={{ height: 220 }}>
            <Bar
              data={{
                labels: MODELS.map(m => m.label),
                datasets: [{
                  label: "sMAPE (%)",
                  data: MODELS.map(m => data[m.key].sMAPE),
                  backgroundColor: MODELS.map(m => m.bg.replace("0.15", "0.78")),
                  borderColor: MODELS.map(m => m.color),
                  borderWidth: 1.5,
                  borderRadius: 6,
                }]
              }}
              options={opts}
            />
          </div>
        </div>

        <div style={{ background: "#fff", border: "1px solid #e5e7eb",
          borderRadius: 12, padding: "18px 22px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#374151",
            fontFamily: "'IBM Plex Mono', monospace",
            textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 14 }}>
            RMSE (kWh) — lower = better
          </div>
          <div style={{ height: 220 }}>
            <Bar
              data={{
                labels: MODELS.map(m => m.label),
                datasets: [{
                  label: "RMSE (kWh)",
                  data: MODELS.map(m => data[m.key].RMSE),
                  backgroundColor: MODELS.map(m => m.bg.replace("0.15", "0.75")),
                  borderColor: MODELS.map(m => m.color),
                  borderWidth: 1.5,
                  borderRadius: 6,
                }]
              }}
              options={opts}
            />
          </div>
        </div>

        <div style={{ background: "#fff", border: "1px solid #e5e7eb",
          borderRadius: 12, padding: "18px 22px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#374151",
            fontFamily: "'IBM Plex Mono', monospace",
            textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 14 }}>
            MAE (kWh) — lower = better
          </div>
          <div style={{ height: 220 }}>
            <Bar
              data={{
                labels: MODELS.map(m => m.label),
                datasets: [{
                  label: "MAE (kWh)",
                  data: MODELS.map(m => data[m.key].MAE),
                  backgroundColor: MODELS.map(m => m.bg.replace("0.15", "0.75")),
                  borderColor: MODELS.map(m => m.color),
                  borderWidth: 1.5,
                  borderRadius: 6,
                }]
              }}
              options={opts}
            />
          </div>
        </div>
      </div>

      {/* Summary table */}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb",
        borderRadius: 12, padding: "18px 22px" }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#374151",
          fontFamily: "'IBM Plex Mono', monospace",
          textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 14 }}>
          Summary Table — Test Period
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse",
          fontFamily: "'IBM Plex Mono', monospace", fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
              {["Model","R²","RMSE (kWh)","MAE (kWh)","sMAPE"].map(h => (
                <th key={h} style={{ padding: "8px 12px", textAlign: h === "Model" ? "left" : "right",
                  fontSize: 10, color: "#6b7280", fontWeight: 700,
                  textTransform: "uppercase", letterSpacing: 0.5 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {MODELS.map(({ key, label, color }) => {
              const m = data[key];
              return (
                <tr key={key} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "10px 12px", display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: 2, background: color }}/>
                    {label}
                  </td>
                  {[
                    { v: m.R2.toFixed(4),   best: m.R2 === bestR2,    higher: true  },
                    { v: m.RMSE.toFixed(1), best: m.RMSE === bestRmse, higher: false },
                    { v: m.MAE.toFixed(1),  best: m.MAE === bestMae,   higher: false },
                    { v: `${m.sMAPE.toFixed(2)}%`, best: m.sMAPE === bestSmape, higher: false },
                  ].map(({ v, best }, ci) => (
                    <td key={ci} style={{
                      padding: "10px 12px", textAlign: "right",
                      fontWeight: best ? 700 : 400,
                      color: best ? "#16a34a" : "#374151",
                    }}>
                      {v}{best && " ★"}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
        <div style={{ marginTop: 10, fontSize: 10, color: "#9ca3af",
          fontFamily: "'IBM Plex Sans', sans-serif" }}>
          ★ Best in category
        </div>
      </div>
    </div>
  );
}
