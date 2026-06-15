import { render, screen } from "@testing-library/react";
import ScenarioResults from "@/components/ScenarioResults";

describe("ScenarioResults", () => {
  const mockResults = [
    { priceShock: "-10%", pnl: -3200, deltaImpact: -0.12, gammaImpact: 0.01 },
    { priceShock: "+10%", pnl: 2800, deltaImpact: 0.10, gammaImpact: -0.01 },
  ];

  it("renders results table", () => {
    render(<ScenarioResults results={mockResults} />);
    expect(screen.getByText("Scenario Results")).toBeInTheDocument();
    expect(screen.getByText("-10%")).toBeInTheDocument();
    // P&L is split across text nodes ($ and number), check the td contains it
    const cells = screen.getAllByRole("cell");
    const pnlCell = cells.find((c) => c.textContent?.includes("3,200"));
    expect(pnlCell).toBeTruthy();
  });

  it("renders empty state", () => {
    render(<ScenarioResults results={[]} />);
    expect(screen.getByText("No scenario results")).toBeInTheDocument();
  });
});
