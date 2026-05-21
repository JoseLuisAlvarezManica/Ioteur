import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

function buildPieData(values) {
  const counts = new Map();

  values.forEach((value) => {
    const label = value == null || value === "" ? "Sin valor" : String(value);
    counts.set(label, (counts.get(label) ?? 0) + 1);
  });

  return Array.from(counts.entries()).map(([name, value], index) => ({
    name,
    value,
    fill: COLORS[index % COLORS.length],
  }));
}

function MetricPieChart({ values = [] }) {
  const chartData = buildPieData(values);

  if (chartData.length === 0) {
    return <p className="text-xs text-gray-400">No hay datos para graficar.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart margin={{ right: 300 }}>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          cx="40%"
          cy="50%"
          outerRadius={78}
          innerRadius={36}
          paddingAngle={2}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
        >
          {chartData.map((entry) => (
            <Cell key={entry.name} fill={entry.fill} />
          ))}
        </Pie>
        <Tooltip />
        <Legend layout="vertical" align="right" verticalAlign="middle" iconSize={10} iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  );
}

export default MetricPieChart;