import { render, screen } from "@testing-library/react";
import PnLChart from "@/components/PnLChart";

describe("PnLChart", () => {
  const mockData = [
    { date: "2025-01-01", pnl: 150 },
    { date: "2025-01-02", pnl: -80 },
    { date: "2025-01-03", pnl: 220 },
  ];

  it("renders chart with data", () => {
    render(<PnLChart data={mockData} />);
    expect(screen.getByText("P&L Over Time")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<PnLChart data={[]} />);
    expect(screen.getByText("P&L Over Time")).toBeInTheDocument();
  });
});
