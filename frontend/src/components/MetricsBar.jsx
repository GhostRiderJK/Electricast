import { useData } from "../hooks/useData";
import { api } from "../utils/api";

const MODEL_CONFIG = {
  lstm:    { label: "LSTM",    accent: "#2563eb", bg: "#eff6ff", icon: "⬡" },
  sarima:  { label: "SARIMA",  accent: "#dc2626", bg: "#fef2f2", icon: "⌇" },
  xgboost: { label: "XGBoost", accent: "#16a34a", bg: "#f0fdf4", icon: "⬢" },
};

function MetricCard({ model, metrics }) {
  const cfg = MODEL_CONFIG[model];
  if (!cfg || !metrics) return null;
  return (
    <div style={{
      background: "#fff",
      border: `1.5px solid ${cfg.accent}22`,
      borderRadius: 12,
      padding: "18px 20px",
      flex: 1,
      minWidth: 0,
      position: "relative",
      overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", top: 0, left: 0, width: 4,
        height: "100%", background: cfg.accent, borderRadius: "12px 0 0 12px"
      }}/>
      <div style={{ paddingLeft: 4 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <span style={{
            fontSize: 18, background: cfg.bg,
            width: 34, height: 34, borderRadius: 8,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: cfg.accent
          }}>{cfg.icon}</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#111827", fontFamily: "'IBM Plex Mono', monospace" }}>
              {cfg.label}
            </div>
            <div style={{ fontSize: 10, color: "#9ca3af", fontFamily: "'IBM Plex Sans', sans-serif", marginTop: 1 }}>
              {metrics.period}
            </div>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 16px" }}>
          {[
            { k: "R²",    v: metrics.R2.toFixed(4),     good: metrics.R2 >= 0.8 ? true : metrics.R2 < 0 ? false : null },
            { k: "RMSE",  v: `${metrics.RMSE.toFixed(0)} Wh`, good: null },
            { k: "MAE",   v: `${metrics.MAE.toFixed(0)} Wh`,  good: null },
            { k: "sMAPE", v: `${metrics.sMAPE.toFixed(2)}%`,  good: metrics.sMAPE < 15 },
          ].map(({ k, v, good }) => (
            <div key={k}>
              <div style={{ fontSize: 10, color: "#6b7280", fontFamily: "'IBM Plex Sans', sans-serif", marginBottom: 2 }}>{k}</div>
              <div style={{
                fontSize: 15, fontWeight: 700,
                fontFamily: "'IBM Plex Mono', monospace",
                color: good === true ? "#16a34a" : good === false ? "#dc2626" : "#111827"
              }}>{v}</div>
            </div>
          ))}
        </div>
        <div style={{
          marginTop: 12, fontSize: 10, color: "#9ca3af",
          fontFamily: "'IBM Plex Sans', sans-serif",
          lineHeight: 1.5, borderTop: "1px solid #f3f4f6", paddingTop: 10
        }}>
          {metrics.description}
        </div>
      </div>
    </div>
  );
}

export default function MetricsBar() {
  const { data, loading } = useData(api.metrics);

  if (loading) return (
    <div style={{ display: "flex", gap: 12 }}>
      {[0,1,2].map(i => (
        <div key={i} style={{
          flex: 1, height: 160, background: "#f9fafb",
          borderRadius: 12, animation: "pulse 1.5s ease-in-out infinite"
        }}/>
      ))}
    </div>
  );

  const active = ["lstm", "sarima", "xgboost"].filter(
    model => data?.[model]?.status === "ok"
  );

  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      {active.map(model => (
    <MetricCard key={model} model={model} metrics={data?.[model] ?? null} />
    ))}
    </div>
  );
}
