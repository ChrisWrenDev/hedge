interface ScenarioResult {
  priceShock: string;
  pnl: number;
  deltaImpact: number;
  gammaImpact: number;
}

interface ScenarioResultsProps {
  results: ScenarioResult[];
}

export default function ScenarioResults({ results }: ScenarioResultsProps) {
  return (
    <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
      <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>Scenario Results</h3>
      {results.length === 0 ? (
        <p style={{ color: "#666", textAlign: "center", padding: "2rem" }}>No scenario results</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #333", textAlign: "left" }}>
              <th style={{ padding: "8px 4px", color: "#888" }}>Price Δ</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>P&amp;L</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Δ Impact</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Γ Impact</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #222" }}>
                <td style={{ padding: "8px 4px" }}>{r.priceShock}</td>
                <td
                  style={{
                    padding: "8px 4px",
                    color: r.pnl >= 0 ? "#22c55e" : "#ef4444",
                  }}
                >
                  {r.pnl >= 0 ? "+" : ""}${r.pnl.toLocaleString()}
                </td>
                <td style={{ padding: "8px 4px" }}>{r.deltaImpact}</td>
                <td style={{ padding: "8px 4px" }}>{r.gammaImpact}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
