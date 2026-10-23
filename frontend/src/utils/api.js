const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  metrics:            ()          => get("/api/metrics"),
  statistics:         ()          => get("/api/eda/statistics"),
  edaHourly:          ()          => get("/api/eda/hourly"),
  edaDaily:           ()          => get("/api/eda/daily"),
  edaMonthly:         ()          => get("/api/eda/monthly"),
  edaYearly:          ()          => get("/api/eda/yearly"),
  edaHeatmap:         ()          => get("/api/eda/heatmap"),
  edaWeekdayWeekend:  ()          => get("/api/eda/weekday_vs_weekend"),
  predMonthly:        ()          => get("/api/predictions/monthly"),
  predDaily:          (month="")  => get(`/api/predictions/daily${month ? `?month=${month}` : ""}`),
  predHourly:         (m, d)      => get(`/api/predictions/hourly?month=${m}&day=${d}`),
  predWeeklyPattern:  ()          => get("/api/predictions/weekly_pattern"),
  predMonthlyErrors:  ()          => get("/api/predictions/monthly_errors"),

  uploadValidate: async (file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/api/upload-validate`, { method: "POST", body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
      throw new Error(err.error || `Upload failed: ${res.status}`);
    }
    return res.json();
  },
};
