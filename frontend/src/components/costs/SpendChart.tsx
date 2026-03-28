import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface DailySpend {
  date: string;
  cost_usd: number;
}

interface SpendChartProps {
  data: DailySpend[];
}

export function SpendChart({ data }: SpendChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-5">
        <p className="text-sm text-muted-foreground">No spend data available.</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
        Daily Spend
      </p>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0ea5e9" stopOpacity={0.15} />
              <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="date"
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
          <Area
            type="monotone"
            dataKey="cost_usd"
            stroke="#0ea5e9"
            strokeWidth={2}
            fill="url(#spendGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
