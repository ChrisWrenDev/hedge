interface StatsCardProps {
  label: string;
  value: string;
  subtext?: string;
  className?: string;
}

export default function StatsCard({ label, value, subtext, className }: StatsCardProps) {
  return (
    <div
      className={className}
      style={{
        padding: "1rem",
        background: "#1a1a1a",
        border: "1px solid #333",
        borderRadius: 8,
        flex: 1,
        minWidth: 150,
      }}
    >
      <div style={{ fontSize: "0.8rem", color: "#888", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: 600, color: "#fff" }}>{value}</div>
      {subtext && <div style={{ fontSize: "0.75rem", color: "#666", marginTop: 2 }}>{subtext}</div>}
    </div>
  );
}
