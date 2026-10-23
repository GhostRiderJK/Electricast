import { useData } from "../hooks/useData";
import { api } from "../utils/api";
import DataError from "./DataError";

const MODEL_CONFIG = {
  sarima:  { label: "SARIMA",  accent: "#b91c1c", bg: "#fef2f2", icon: "⌇" },
  xgboost: { label: "XGBoost", accent: "#15803d", bg: "#f0fdf4", icon: "⬢" },
};

function MetricCard({ model, metrics }) {
  const cfg = MODEL_CONFIG[model];
  if (!cfg || !metrics) return null;
  const items = [
    { k: "R²",    v: metrics.R2.toFixed(4),     good: metrics.R2 >= 0.8 ? true : metrics.R2 < 0 ? false : null },
    { k: "RMSE",  v: `${metrics.RMSE.toFixed(0)} Wh`, good: null },
    { k: "MAE",   v: `${metrics.MAE.toFixed(0)} Wh`,  good: null },
    { k: "sMAPE", v: `${metrics.sMAPE.toFixed(2)}%`,  good: metrics.sMAPE < 15 },
  ];

  return (
    <div title={metrics.description} style={{
      flex: "1 1 380px", minWidth: 0,
      display: "flex", alignItems: "center", gap: 12,
      background: "#fff",
      border: `1.5px solid ${cfg.accent}22`,
      borderLeft: `3px solid ${cfg.accent}`,
      borderRadius: 10,
      padding: "8px 14px",
    }}>
      <span style={{
        fontSize: 15, background: cfg.bg, width: 28, height: 28, borderRadius: 7,
        display: "flex", alignItems: "center", justifyContent: "center",
        color: cfg.accent, flexShrink: 0,
      }}>{cfg.icon}</span>
      <div style={{ minWidth: 0 }}>
        <div style={{
          fontSize: 12, fontWeight: 700, color: "#111827",
          fontFamily: "'IBM Plex Mono', monospace", lineHeight: 1.2,
        }}>{cfg.label}</div>
        <div style={{
          fontSize: 9, color: "#4b5563", fontFamily: "'IBM Plex Sans', sans-serif",
          whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
        }}>{metrics.period}</div>
      </div>
      <div style={{ display: "flex", gap: 16, marginLeft: "auto", flexShrink: 0 }}>
        {items.map(({ k, v, good }) => (
          <div key={k} style={{ textAlign: "right" }}>
            <div style={{
              fontSize: 9, color: "#4b5563",
              fontFamily: "'IBM Plex Sans', sans-serif", marginBottom: 1,
            }}>{k}</div>
            <div style={{
              fontSize: 13, fontWeight: 700,
              fontFamily: "'IBM Plex Mono', monospace",
              color: good === true ? "#15803d" : good === false ? "#dc2626" : "#111827",
            }}>{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MetricsBar() {
  const { data, loading, error } = useData(api.metrics);

  if (loading) return (
    <div style={{ display: "flex", gap: 10 }}>
      {[0, 1].map(i => (
        <div key={i} style={{
          flex: 1, height: 52, background: "#f9fafb",
          borderRadius: 10, animation: "pulse 1.5s ease-in-out infinite"
        }}/>
      ))}
    </div>
  );

  if (error) return <DataError error={error} label="model metrics" />;

  const active = ["sarima", "xgboost"].filter(
    model => data?.[model]?.status === "ok"
  );

  return (
    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
      {active.map(model => (
        <MetricCard key={model} model={model} metrics={data?.[model] ?? null} />
      ))}
    </div>
  );
}
