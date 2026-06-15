"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface GreeksDataPoint {
  name: string;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
}

interface GreeksExposureProps {
  data: GreeksDataPoint[];
}

export default function GreeksExposure({ data }: GreeksExposureProps) {
  return (
    <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
      <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>Greeks Exposure</h3>
      {data.length === 0 ? (
        <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center", color: "#666" }}>
          No data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="name" stroke="#888" fontSize={12} />
            <YAxis stroke="#888" fontSize={12} />
            <Tooltip
              contentStyle={{ background: "#1a1a1a", border: "1px solid #333", color: "#fff" }}
            />
            <Legend />
            <Bar dataKey="delta" fill="#3b82f6" stackId="greeks" />
            <Bar dataKey="gamma" fill="#22c55e" stackId="greeks" />
            <Bar dataKey="theta" fill="#ef4444" stackId="greeks" />
            <Bar dataKey="vega" fill="#f59e0b" stackId="greeks" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
