import {
  fetchPortfolios,
  createPortfolio,
  fetchPositions,
  fetchPortfolioGreeks,
  fetchConvexityTop,
  fetchRules,
  toggleRule,
  fetchTriggers,
  fetchScenarioTemplates,
  createScenarioTemplate,
  runScenario,
  fetchScenarioRuns,
  fetchAlertChannels,
  createAlertChannel,
  fetchAlertHistory,
  fetchAlertSubscriptions,
  createAlertSubscription,
  type Portfolio,
  type Position,
  type PortfolioGreeks,
  type ConvexityScore,
  type RuleDefinition,
  type ScenarioTemplate,
  type ScenarioRun,
  type AlertChannel,
  type AlertSubscription,
  type AlertHistory,
} from "@/lib/api";

const API_BASE = "http://localhost:8000";

beforeEach(() => {
  jest.restoreAllMocks();
});

describe("API Client", () => {
  describe("fetchPortfolios", () => {
    it("returns list of portfolios", async () => {
      const mockData: Portfolio[] = [
        { id: "1", name: "Main", description: "Primary", budget: 100000 },
      ];
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await fetchPortfolios();
      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE}/api/portfolio/`,
        undefined
      );
    });

    it("throws on non-ok response", async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: false });
      await expect(fetchPortfolios()).rejects.toThrow("Failed to fetch /api/portfolio/");
    });
  });

  describe("createPortfolio", () => {
    it("sends POST with correct body", async () => {
      const mockResult: Portfolio = {
        id: "2", name: "Test", description: null, budget: 50000,
      };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const result = await createPortfolio({ name: "Test", budget: 50000 });
      expect(result).toEqual(mockResult);
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE}/api/portfolio/`,
        expect.objectContaining({ method: "POST" })
      );
    });

    it("throws on non-ok response", async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: false });
      await expect(
        createPortfolio({ name: "Test", budget: 50000 })
      ).rejects.toThrow();
    });
  });

  describe("fetchPositions", () => {
    it("fetches positions for a portfolio", async () => {
      const mockData: Position[] = [
        { id: "1", portfolio_id: "1", contract_id: "c1", quantity: 10, entry_price: 2.15, entry_date: "2025-01-15" },
      ];
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await fetchPositions("1");
      expect(result).toEqual(mockData);
    });
  });

  describe("fetchPortfolioGreeks", () => {
    it("fetches greeks for a portfolio", async () => {
      const mockData: PortfolioGreeks = {
        id: "1", portfolio_id: "1", timestamp: "2025-01-15T10:00:00Z",
        net_delta: 0.31, net_gamma: -0.02, net_theta: -45, net_vega: 1.2,
      };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await fetchPortfolioGreeks("1");
      expect(result).toEqual(mockData);
    });
  });

  describe("fetchConvexityTop", () => {
    it("returns top convexity scores", async () => {
      const mockData: ConvexityScore[] = [
        { id: "1", contract_id: "c1", score_date: "2025-01-15", score: 82.5, gamma_per_theta: 4.2, vega_normalized: 0.15, iv_rank: 35, iv_percentile: 30 },
      ];
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await fetchConvexityTop(10);
      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("limit=10"),
        undefined
      );
    });
  });

  describe("fetchRules", () => {
    it("returns list of rules", async () => {
      const mockData: RuleDefinition[] = [
        { id: "1", name: "delta_hedge", rule_type: "code", module_path: "delta_hedge", config: {}, active: true, priority: 5 },
      ];
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await fetchRules();
      expect(result).toEqual(mockData);
    });
  });

  describe("toggleRule", () => {
    it("sends PATCH to toggle", async () => {
      const mockResult: RuleDefinition = {
        id: "1", name: "delta_hedge", rule_type: "code", module_path: "delta_hedge", config: {}, active: false, priority: 5,
      };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const result = await toggleRule("1");
      expect(result.active).toBe(false);
    });
  });

  describe("fetchScenarioTemplates", () => {
    it("returns templates", async () => {
      const mockData: ScenarioTemplate[] = [
        { id: "1", name: "Price Shock", description: "test", parameters: { type: "price_shock" }, active: true },
      ];
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await fetchScenarioTemplates();
      expect(result).toEqual(mockData);
    });
  });

  describe("runScenario", () => {
    it("sends POST to run scenario", async () => {
      const mockResult: ScenarioRun = {
        id: "1", template_id: "1", status: "complete", results: { type: "price_shock" },
      };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const result = await runScenario("1");
      expect(result.status).toBe("complete");
    });
  });

  describe("fetchAlertChannels", () => {
    it("returns channels", async () => {
      const mockData: AlertChannel[] = [
        { id: "1", name: "Slack", type: "webhook", config: { url: "x" }, active: true },
      ];
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await fetchAlertChannels();
      expect(result).toEqual(mockData);
    });
  });

  describe("fetchAlertHistory", () => {
    it("returns history", async () => {
      const mockData: AlertHistory[] = [];
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await fetchAlertHistory();
      expect(result).toEqual([]);
    });
  });
});
