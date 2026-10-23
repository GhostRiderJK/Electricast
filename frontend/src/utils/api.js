const BASE = import.meta.env.VITE_API_URL || "";

async function get(path, signal) {
  const res = await fetch(`${BASE}${path}`, { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || body?.error || `API error ${res.status}: ${path}`);
  }
  return res.json();
}

export const api = {
  metrics:            (signal) => get("/api/metrics", signal),
  statistics:         (signal) => get("/api/eda/statistics", signal),
  edaHourly:          (signal) => get("/api/eda/hourly", signal),
  edaDaily:           (signal) => get("/api/eda/daily", signal),
  edaMonthly:         (signal) => get("/api/eda/monthly", signal),
  edaYearly:          (signal) => get("/api/eda/yearly", signal),
  edaHeatmap:         (signal) => get("/api/eda/heatmap", signal),
  edaWeekdayWeekend:  (signal) => get("/api/eda/weekday_vs_weekend", signal),
  predMonthly:        (signal) => get("/api/predictions/monthly", signal),
  predDaily:          (month = "", signal) => get(`/api/predictions/daily${month ? `?month=${month}` : ""}`, signal),
  predHourly:         (m, d, signal) => get(`/api/predictions/hourly?month=${m}&day=${d}`, signal),
  predWeeklyPattern:  (signal) => get("/api/predictions/weekly_pattern", signal),
  predMonthlyErrors:  (signal) => get("/api/predictions/monthly_errors", signal),

  uploadValidate: async (file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/api/upload-validate`, { method: "POST", body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
      throw new Error(err.detail || err.error || `Upload failed: ${res.status}`);
    }
    return res.json();
  },
};
