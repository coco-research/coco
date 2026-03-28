import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface ModelBreakdownProps {
  data: Record<string, number>;
}

const MODEL_COLORS: Record<string, string> = {
  haiku: '#10b981',
  sonnet: '#3b82f6',
  opus: '#a855f7',
};

function getModelColor(model: string): string {
  const key = model.toLowerCase();
  for (const [name, color] of Object.entries(MODEL_COLORS)) {
    if (key.includes(name)) return color;
  }
  return '#f59e0b';
}

export function ModelBreakdown({ data }: ModelBreakdownProps) {
  const items = Object.entries(data)
    .map(([model, cost_usd]) => ({ model, cost_usd }))
    .sort((a, b) => b.cost_usd - a.cost_usd);

  if (items.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-5">
        <p className="text-sm text-muted-foreground">No model data available.</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
        Cost by Model
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={items} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="model"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis
            tickFormatter={(v: number) => `$${v.toFixed(2)}`}
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            width={60}
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
          <Bar dataKey="cost_usd" radius={[4, 4, 0, 0]}>
            {items.map((entry) => (
              <Cell key={entry.model} fill={getModelColor(entry.model)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
