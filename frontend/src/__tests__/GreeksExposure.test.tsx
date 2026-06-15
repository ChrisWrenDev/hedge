import { render, screen } from "@testing-library/react";
import GreeksExposure from "@/components/GreeksExposure";

describe("GreeksExposure", () => {
  const mockData = [
    { name: "AAPL 190C", delta: 540, gamma: 30, theta: -5, vega: 15 },
    { name: "SPX 5100P", delta: -230, gamma: 20, theta: -4, vega: 12 },
  ];

  it("renders chart title", () => {
    render(<GreeksExposure data={mockData} />);
    expect(screen.getByText("Greeks Exposure")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<GreeksExposure data={[]} />);
    expect(screen.getByText("Greeks Exposure")).toBeInTheDocument();
  });
});
