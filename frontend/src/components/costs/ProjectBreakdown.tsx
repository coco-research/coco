import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface ProjectBreakdownProps {
  data: Record<string, number>;
}

export function ProjectBreakdown({ data }: ProjectBreakdownProps) {
  const items = Object.entries(data)
    .map(([project, cost_usd]) => ({ project, cost_usd }))
    .sort((a, b) => b.cost_usd - a.cost_usd);

  if (items.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-5">
        <p className="text-sm text-muted-foreground">No project data available.</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
        Cost by Project
      </p>
      <ResponsiveContainer width="100%" height={Math.max(items.length * 40, 120)}>
        <BarChart
          data={items}
          layout="vertical"
          margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis
            type="number"
            tickFormatter={(v: number) => `$${v.toFixed(2)}`}
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis
            type="category"
            dataKey="project"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            width={100}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: 8,
              fontSize: 13,
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
            labelStyle={{ color: '#475569' }}
            formatter={(value) => [`$${Number(value).toFixed(4)}`, 'Cost']}
          />
          <Bar dataKey="cost_usd" fill="#3b82f6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
