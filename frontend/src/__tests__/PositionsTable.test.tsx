import { render, screen } from "@testing-library/react";
import PositionsTable from "@/components/PositionsTable";

describe("PositionsTable", () => {
  const mockPositions = [
    { contract: "AAPL 190C", quantity: 10, entry: 2.15, current: 2.80, pnl: 650, delta: 0.54 },
    { contract: "SPX 5100P", quantity: -5, entry: 3.80, current: 3.20, pnl: 300, delta: -0.23 },
  ];

  it("renders positions table", () => {
    render(<PositionsTable positions={mockPositions} />);
    expect(screen.getByText("AAPL 190C")).toBeInTheDocument();
    expect(screen.getByText("+$650")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<PositionsTable positions={[]} />);
    expect(screen.getByText("No positions")).toBeInTheDocument();
  });
});
