interface Position {
  contract: string;
  quantity: number;
  entry: number;
  current: number;
  pnl: number;
  delta: number;
}

interface PositionsTableProps {
  positions: Position[];
}

export default function PositionsTable({ positions }: PositionsTableProps) {
  return (
    <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
      <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>Positions</h3>
      {positions.length === 0 ? (
        <p style={{ color: "#666", textAlign: "center", padding: "2rem" }}>No positions</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #333", textAlign: "left" }}>
              <th style={{ padding: "8px 4px", color: "#888" }}>Contract</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Qty</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Entry</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Current</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>P&amp;L</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Δ</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #222" }}>
                <td style={{ padding: "8px 4px" }}>{p.contract}</td>
                <td style={{ padding: "8px 4px" }}>{p.quantity > 0 ? `+${p.quantity}` : p.quantity}</td>
                <td style={{ padding: "8px 4px" }}>${p.entry.toFixed(2)}</td>
                <td style={{ padding: "8px 4px" }}>${p.current.toFixed(2)}</td>
                <td
                  style={{
                    padding: "8px 4px",
                    color: p.pnl >= 0 ? "#22c55e" : "#ef4444",
                  }}
                >
                  {p.pnl >= 0 ? "+" : ""}${p.pnl.toLocaleString()}
                </td>
                <td style={{ padding: "8px 4px" }}>{p.delta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
