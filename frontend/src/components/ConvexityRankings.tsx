interface Score {
  rank: number;
  contract: string;
  score: number;
  gammaTheta: number;
  ivRank: number;
  action: string;
}

interface ConvexityRankingsProps {
  scores: Score[];
}

export default function ConvexityRankings({ scores }: ConvexityRankingsProps) {
  return (
    <div style={{ padding: "1rem", background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}>
      <h3 style={{ fontSize: "0.9rem", color: "#ccc", marginBottom: 12 }}>Convexity Rankings</h3>
      {scores.length === 0 ? (
        <p style={{ color: "#666", textAlign: "center", padding: "2rem" }}>No convexity scores available</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #333", textAlign: "left" }}>
              <th style={{ padding: "8px 4px", color: "#888" }}>Rank</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Contract</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Score</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Γ/Θ</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>IV Rank</th>
              <th style={{ padding: "8px 4px", color: "#888" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {scores.map((s) => (
              <tr key={s.rank} style={{ borderBottom: "1px solid #222" }}>
                <td style={{ padding: "8px 4px", color: "#aaa" }}>{s.rank}</td>
                <td style={{ padding: "8px 4px" }}>{s.contract}</td>
                <td style={{ padding: "8px 4px", color: "#22c55e" }}>{s.score}</td>
                <td style={{ padding: "8px 4px" }}>{s.gammaTheta}</td>
                <td style={{ padding: "8px 4px" }}>{s.ivRank}</td>
                <td style={{ padding: "8px 4px" }}>
                  <button
                    style={{
                      background: "#3b82f6",
                      color: "#fff",
                      border: "none",
                      borderRadius: 4,
                      padding: "4px 12px",
                      cursor: "pointer",
                    }}
                  >
                    {s.action}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
