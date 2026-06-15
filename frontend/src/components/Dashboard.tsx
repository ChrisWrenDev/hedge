"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  fetchPortfolios,
  fetchPositions,
  fetchAlertHistory,
  type Portfolio,
  type Position,
  type AlertHistory,
} from "@/lib/api";

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [alerts, setAlerts] = useState<AlertHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [pf, al] = await Promise.all([
          fetchPortfolios().catch(() => [] as Portfolio[]),
          fetchAlertHistory().catch(() => [] as AlertHistory[]),
        ]);
        setPortfolios(pf);
        setAlerts(al);

        if (pf.length > 0) {
          const pos = await fetchPositions(pf[0].id).catch(() => [] as Position[]);
          setPositions(pos);
        }
      } catch {
        console.error("Could not reach API");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const totalBudget = portfolios.reduce((s, p) => s + (p.budget || 0), 0);
  const activeAlerts = alerts.filter((a) => a.status === "pending").length;

  const pnlData = positions.map((p) => ({
    name: p.contract_id.slice(0, 8),
    pnl: p.unrealized_pnl || 0,
  }));

  const greeksData = positions.map((p) => ({
    name: p.contract_id.slice(0, 8),
    quantity: p.quantity,
  }));

  if (loading) {
    return (
      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1rem" }}>
        <p style={{ color: "#888" }}>Loading...</p>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: "1.5rem", color: "#fff" }}>
        Hedge Dashboard
      </h1>

      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8, flex: 1 }}>
          <div style={{ fontSize: "0.8rem", color: "#888" }}>Portfolios</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 600, color: "#fff" }}>{portfolios.length}</div>
        </div>
        <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8, flex: 1 }}>
          <div style={{ fontSize: "0.8rem", color: "#888" }}>Positions</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 600, color: "#fff" }}>{positions.length}</div>
        </div>
        <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8, flex: 1 }}>
          <div style={{ fontSize: "0.8rem", color: "#888" }}>Total Budget</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 600, color: "#fff" }}>${totalBudget.toLocaleString()}</div>
        </div>
        <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8, flex: 1 }}>
          <div style={{ fontSize: "0.8rem", color: "#888" }}>Active Alerts</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 600, color: activeAlerts > 0 ? "#f59e0b" : "#22c55e" }}>{activeAlerts}</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
        <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
          <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>Position P&amp;L</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={pnlData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="name" stroke="#888" fontSize={12} />
              <YAxis stroke="#888" fontSize={12} />
              <Tooltip contentStyle={{ background: "#1a1a1a", border: "1px solid #333", color: "#fff" }} />
              <Bar dataKey="pnl" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
          <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>Positions by Quantity</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={greeksData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="name" stroke="#888" fontSize={12} />
              <YAxis stroke="#888" fontSize={12} />
              <Tooltip contentStyle={{ background: "#1a1a1a", border: "1px solid #333", color: "#fff" }} />
              <Bar dataKey="quantity" fill="#22c55e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
        <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>Recent Alerts</h3>
        {alerts.length === 0 ? (
          <p style={{ color: "#666", textAlign: "center", padding: "2rem" }}>No recent alerts</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #333", textAlign: "left" }}>
                <th style={{ padding: "8px 4px", color: "#888" }}>Subject</th>
                <th style={{ padding: "8px 4px", color: "#888" }}>Status</th>
                <th style={{ padding: "8px 4px", color: "#888" }}>Sent At</th>
              </tr>
            </thead>
            <tbody>
              {alerts.slice(0, 5).map((a) => (
                <tr key={a.id} style={{ borderBottom: "1px solid #222" }}>
                  <td style={{ padding: "8px 4px" }}>{a.subject || "—"}</td>
                  <td style={{ padding: "8px 4px" }}>
                    <span style={{ color: a.status === "sent" ? "#22c55e" : "#ef4444" }}>{a.status}</span>
                  </td>
                  <td style={{ padding: "8px 4px", color: "#aaa" }}>
                    {a.sent_at ? new Date(a.sent_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}
