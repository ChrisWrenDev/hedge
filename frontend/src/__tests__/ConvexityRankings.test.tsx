import { render, screen } from "@testing-library/react";
import ConvexityRankings from "@/components/ConvexityRankings";

describe("ConvexityRankings", () => {
  const mockScores = [
    { rank: 1, contract: "AAPL 190C", score: 82.5, gammaTheta: 4.2, ivRank: 35, action: "Buy" },
    { rank: 2, contract: "SPX 5100P", score: 78.1, gammaTheta: 3.8, ivRank: 42, action: "Buy" },
  ];

  it("renders rankings table", () => {
    render(<ConvexityRankings scores={mockScores} />);
    expect(screen.getByText("Convexity Rankings")).toBeInTheDocument();
    expect(screen.getByText("AAPL 190C")).toBeInTheDocument();
    expect(screen.getByText("82.5")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<ConvexityRankings scores={[]} />);
    expect(screen.getByText("No convexity scores available")).toBeInTheDocument();
  });
});
