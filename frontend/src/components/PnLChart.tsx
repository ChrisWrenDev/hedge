"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface PnLDataPoint {
  date: string;
  pnl: number;
}

interface PnLChartProps {
  data: PnLDataPoint[];
}

export default function PnLChart({ data }: PnLChartProps) {
  return (
    <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
      <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>P&amp;L Over Time</h3>
      {data.length === 0 ? (
        <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center", color: "#666" }}>
          No data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" fontSize={12} />
            <YAxis stroke="#888" fontSize={12} />
            <Tooltip
              contentStyle={{ background: "#1a1a1a", border: "1px solid #333", color: "#fff" }}
            />
            <Line type="monotone" dataKey="pnl" stroke="#3b82f6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
