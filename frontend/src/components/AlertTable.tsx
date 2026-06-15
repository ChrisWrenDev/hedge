interface Alert {
  id: string;
  time: string;
  rule: string;
  action: string;
  status: string;
}

interface AlertTableProps {
  alerts: Alert[];
}

export default function AlertTable({ alerts }: AlertTableProps) {
  if (alerts.length === 0) {
    return (
      <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
        <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>Recent Alerts</h3>
        <p style={{ color: "#666", textAlign: "center", padding: "2rem" }}>No recent alerts</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
      <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>Recent Alerts</h3>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid #333", textAlign: "left" }}>
            <th style={{ padding: "8px 4px", color: "#888" }}>Time</th>
            <th style={{ padding: "8px 4px", color: "#888" }}>Rule</th>
            <th style={{ padding: "8px 4px", color: "#888" }}>Action</th>
            <th style={{ padding: "8px 4px", color: "#888" }}>Status</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((a) => (
            <tr key={a.id} style={{ borderBottom: "1px solid #222" }}>
              <td style={{ padding: "8px 4px", color: "#aaa" }}>{a.time}</td>
              <td style={{ padding: "8px 4px" }}>{a.rule}</td>
              <td style={{ padding: "8px 4px" }}>{a.action}</td>
              <td style={{ padding: "8px 4px" }}>
                <span
                  style={{
                    color: a.status === "sent" ? "#22c55e" : a.status === "failed" ? "#ef4444" : "#f59e0b",
                  }}
                >
                  {a.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
