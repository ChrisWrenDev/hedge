const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────

export interface Portfolio {
  id: string;
  name: string;
  description: string | null;
  budget: number;
}

export interface Position {
  id: string;
  portfolio_id: string;
  contract_id: string;
  quantity: number;
  entry_price: number;
  entry_date: string;
  current_price?: number | null;
  unrealized_pnl?: number | null;
}

export interface PortfolioGreeks {
  id: string;
  portfolio_id: string;
  timestamp: string;
  net_delta: number;
  net_gamma: number;
  net_theta: number;
  net_vega: number;
}

export interface ConvexityScore {
  id: string;
  contract_id: string;
  score_date: string;
  score: number;
  gamma_per_theta: number;
  vega_normalized: number;
  iv_rank: number;
  iv_percentile: number;
}

export interface RuleDefinition {
  id: string;
  name: string;
  rule_type: string;
  module_path: string | null;
  config: Record<string, unknown> | null;
  active: boolean;
  priority: number;
}

export interface RuleTrigger {
  id: string;
  rule_id: string;
  triggered_at: string;
  context: Record<string, unknown> | null;
  action_taken: string | null;
}

export interface ScenarioTemplate {
  id: string;
  name: string;
  description: string | null;
  parameters: Record<string, unknown> | null;
  active: boolean;
}

export interface ScenarioRun {
  id: string;
  template_id: string;
  status: string;
  results: Record<string, unknown> | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface AlertChannel {
  id: string;
  name: string;
  type: string;
  config: Record<string, unknown> | null;
  active: boolean;
}

export interface AlertSubscription {
  id: string;
  channel_id: string;
  rule_id: string;
  active: boolean;
}

export interface AlertHistory {
  id: string;
  channel_id: string;
  rule_id: string;
  subject: string | null;
  body: string | null;
  status: string;
  sent_at?: string | null;
}

// ── Fetch helpers ──────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) throw new Error(`Failed to fetch ${path}`);
  return res.json();
}

// ── Portfolio ──────────────────────────────────────────────────

export async function fetchPortfolios(): Promise<Portfolio[]> {
  return apiFetch<Portfolio[]>("/api/portfolio/");
}

export async function createPortfolio(data: {
  name: string;
  description?: string;
  budget?: number;
}): Promise<Portfolio> {
  return apiFetch<Portfolio>("/api/portfolio/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function fetchPositions(
  portfolioId: string
): Promise<Position[]> {
  return apiFetch<Position[]>(`/api/portfolio/${portfolioId}/positions`);
}

export async function fetchPortfolioGreeks(
  portfolioId: string
): Promise<PortfolioGreeks> {
  return apiFetch<PortfolioGreeks>(`/api/portfolio/${portfolioId}/greeks`);
}

// ── Convexity ──────────────────────────────────────────────────

export async function fetchConvexityTop(
  limit: number = 10
): Promise<ConvexityScore[]> {
  return apiFetch<ConvexityScore[]>(
    `/api/convexity/top?limit=${limit}`
  );
}

// ── Rules ──────────────────────────────────────────────────────

export async function fetchRules(): Promise<RuleDefinition[]> {
  return apiFetch<RuleDefinition[]>("/api/rules/");
}

export async function toggleRule(ruleId: string): Promise<RuleDefinition> {
  return apiFetch<RuleDefinition>(`/api/rules/${ruleId}/toggle`, {
    method: "PATCH",
  });
}

export async function fetchTriggers(): Promise<RuleTrigger[]> {
  return apiFetch<RuleTrigger[]>("/api/rules/triggers");
}

// ── Scenarios ──────────────────────────────────────────────────

export async function fetchScenarioTemplates(): Promise<ScenarioTemplate[]> {
  return apiFetch<ScenarioTemplate[]>("/api/scenarios/templates");
}

export async function createScenarioTemplate(data: {
  name: string;
  description?: string;
  parameters?: Record<string, unknown>;
}): Promise<ScenarioTemplate> {
  return apiFetch<ScenarioTemplate>("/api/scenarios/templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function runScenario(
  templateId: string
): Promise<ScenarioRun> {
  return apiFetch<ScenarioRun>(
    `/api/scenarios/templates/${templateId}/run`,
    { method: "POST" }
  );
}

export async function fetchScenarioRuns(): Promise<ScenarioRun[]> {
  return apiFetch<ScenarioRun[]>("/api/scenarios/runs");
}

// ── Alerts ─────────────────────────────────────────────────────

export async function fetchAlertChannels(): Promise<AlertChannel[]> {
  return apiFetch<AlertChannel[]>("/api/alerts/channels");
}

export async function createAlertChannel(data: {
  name: string;
  type: string;
  config?: Record<string, unknown>;
}): Promise<AlertChannel> {
  return apiFetch<AlertChannel>("/api/alerts/channels", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function fetchAlertHistory(): Promise<AlertHistory[]> {
  return apiFetch<AlertHistory[]>("/api/alerts/history");
}

export async function fetchAlertSubscriptions(): Promise<AlertSubscription[]> {
  return apiFetch<AlertSubscription[]>("/api/alerts/subscriptions");
}

export async function createAlertSubscription(data: {
  channel_id: string;
  rule_id: string;
}): Promise<AlertSubscription> {
  return apiFetch<AlertSubscription>("/api/alerts/subscriptions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}
