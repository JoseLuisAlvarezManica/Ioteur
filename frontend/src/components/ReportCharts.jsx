import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import MetricPieChart from "./MetricPieChart";

function computeTrend(values) {
  // simple linear regression over indices
  const toNum = (v) => {
    if (v == null) return NaN;
    const s = String(v).replace(/\s+/g, "").replace(/,/, ".").replace(/[^0-9.\-]/g, "");
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : NaN;
  };
  const nums = values.map((v) => toNum(v));
  const valid = nums.map((n, i) => ({ x: i, y: n })).filter((p) => !Number.isNaN(p.y));
  if (valid.length === 0) return nums.map((_) => NaN);
  const n = valid.length;
  const sumX = valid.reduce((s, p) => s + p.x, 0);
  const sumY = valid.reduce((s, p) => s + p.y, 0);
  const sumXY = valid.reduce((s, p) => s + p.x * p.y, 0);
  const sumXX = valid.reduce((s, p) => s + p.x * p.x, 0);
  const denom = n * sumXX - sumX * sumX;
  const slope = denom === 0 ? 0 : (n * sumXY - sumX * sumY) / denom;
  const intercept = (sumY - slope * sumX) / n;
  return nums.map((_, i) => {
    const v = intercept + slope * i;
    return Number.isFinite(v) ? v : 0;
  });
}

function toNumericValue(value) {
  if (value == null) return NaN;
  const cleaned = String(value)
    .replace(/\s+/g, "")
    .replace(/,/, ".")
    .replace(/[^0-9.\-]/g, "");
  const numeric = parseFloat(cleaned);
  return Number.isFinite(numeric) ? numeric : NaN;
}

function isNumericSeries(values) {
  return values.length > 0 && values.every((value) => Number.isFinite(toNumericValue(value)));
}

const ReportCard = ({ reports = [] }) => {
  const hasReports = Array.isArray(reports) && reports.length > 0;

  if (!hasReports) {
    return (
      <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-4">
        <h3 className="text-base font-bold text-gray-900 mb-3">Datos recientes</h3>
        <p className="text-sm text-gray-400">Aún no hay registros.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {reports.map((report, ri) => {
        const created = report.created_at || report.createdAt;
        const metrics = report.metric_data || report.metricData || [];
        return (
          <div key={report.id ?? report._id ?? ri} className="bg-white border border-gray-200 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="text-sm text-gray-500">Fecha de Creación: {created ? new Date(created).toLocaleString() : "-"}</div>
              <div className="text-md text-gray-400">Reporte #{ri + 1}</div>
            </div>

            <div className="grid gap-4">
              {metrics.map((metric, mi) => {
                const name = metric.device_name || metric.deviceName || `metric-${mi}`;
                const most = metric.most_frequent_value ?? metric.mostFrequentValue ?? metric.mostFrequent;
                const pct = metric.percentaje_change ?? metric.percentajeChange ?? metric.percentaje;
                const top = metric.top_value ?? metric.topValue ?? metric.top;
                const valores = metric.value_list || metric.valueList || metric.valueListRaw || [];
                const numericSeries = isNumericSeries(valores);

                return (
                  <div key={name} className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="text-sm font-bold text-gray-900">{name}</h4>
                        <div className="text-xs text-gray-500">Top: {top ?? "-"} · Más frecuente: {most ?? "-"}</div>
                      </div>
                      <div className="text-xs text-gray-500">Cambio: {pct ?? "-"}%</div>
                    </div>

                    <div className="w-full h-44 mt-3">
                      {numericSeries ? (
                        <>
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart
                              data={valores.map((value, index) => {
                                const numericValue = toNumericValue(value);
                                return {
                                  name: `${index + 1}`,
                                  valor: Number(numericValue).toFixed(3),
                                  tendencia: Number(computeTrend(valores)[index]).toFixed(3),
                                };
                              })}
                            >
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" />
                              <YAxis />
                              <Tooltip />
                              <Line type="monotone" dataKey="valor" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                              <Line type="linear" dataKey="tendencia" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                            </LineChart>
                          </ResponsiveContainer>
                        </>
                      ) : (
                        <MetricPieChart values={valores} />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ReportCard;