import { render, screen } from "@testing-library/react";
import StatsCard from "@/components/StatsCard";

describe("StatsCard", () => {
  it("renders label and value", () => {
    render(<StatsCard label="Net Delta" value="+0.31" />);
    expect(screen.getByText("Net Delta")).toBeInTheDocument();
    expect(screen.getByText("+0.31")).toBeInTheDocument();
  });

  it("renders with optional subtext", () => {
    render(<StatsCard label="Budget" value="$100,000" subtext="remaining" />);
    expect(screen.getByText("remaining")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <StatsCard label="Test" value="1" className="highlight" />
    );
    expect(container.firstChild).toHaveClass("highlight");
  });
});
