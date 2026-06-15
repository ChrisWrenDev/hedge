import { render, screen } from "@testing-library/react";
import AlertTable from "@/components/AlertTable";

describe("AlertTable", () => {
  const mockAlerts = [
    { id: "1", time: "14:30", rule: "convex_bargain", action: "buy", status: "sent" },
    { id: "2", time: "13:15", rule: "delta_hedge", action: "rebalance", status: "failed" },
  ];

  it("renders table headers", () => {
    render(<AlertTable alerts={mockAlerts} />);
    expect(screen.getByText("Time")).toBeInTheDocument();
    expect(screen.getByText("Rule")).toBeInTheDocument();
    expect(screen.getByText("Action")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  it("renders alert rows", () => {
    render(<AlertTable alerts={mockAlerts} />);
    expect(screen.getByText("convex_bargain")).toBeInTheDocument();
    expect(screen.getByText("delta_hedge")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<AlertTable alerts={[]} />);
    expect(screen.getByText("No recent alerts")).toBeInTheDocument();
  });
});
