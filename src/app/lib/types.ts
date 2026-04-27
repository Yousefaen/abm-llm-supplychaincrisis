// Agent identifiers
export const AGENT_IDS = [
  "TaiwanSemi",
  "KoreaSilicon",
  "EuroChip",
  "AmeriSemi",
  "BoschAuto",
  "ContiParts",
  "ToyotaMotors",
  "FordAuto",
  "VolkswagenAG",
] as const;

export type AgentId = (typeof AGENT_IDS)[number];

export type Tier = "foundry" | "chipDesigner" | "tier1Supplier" | "oem";

export type EmotionalState =
  | "confident"
  | "anxious"
  | "angry"
  | "opportunistic"
  | "cautious"
  | "loyal"
  | "panicked"
  | "vindictive";

// Memory record from the agent's memory stream
export interface MemoryRecord {
  round: number;
  category: "transaction" | "market" | "partner_behavior" | "own_decision" | "consequence" | "reflection";
  description: string;
  importance: number;
  tags: string[];
}

// Inter-agent signal
export interface AgentSignal {
  sender: string;
  recipient: string | null;
  signal_type: "price_warning" | "loyalty_pledge" | "threat" | "information" | "request";
  content: string;
  round: number;
}

// Strategic plan
export interface StrategicPlan {
  created_round: number;
  horizon: number;
  goals: string[];
  tactics: Record<string, string>;
  risk_assessment: string;
  invalidated: boolean;
}

// Matches the Python agent state returned by the FastAPI endpoints
export interface AgentState {
  agent_id: string;
  display_name: string;
  tier: Tier;
  inventory: number;
  capacity: number;
  current_price: number;
  emotional_state: EmotionalState;
  fill_rate: number;
  trust_scores: Record<string, number>;
  current_decision: AgentDecision | null;
  decision_history: AgentDecision[];
  round_results: RoundResult[];
  // Financial tracking
  revenue: number;
  costs: number;
  profit: number;
  round_revenue: number;
  round_costs: number;
  effective_quarterly_need: number;
  // Memory, reflection & planning (generative agents architecture)
  memories?: MemoryRecord[];
  reflections?: string[];
  memory_count?: number;
  current_plan?: StrategicPlan | null;
  signals_sent?: AgentSignal[];
  signals_received?: AgentSignal[];
}

export interface AgentDecision {
  type?: "supplier" | "buyer";
  // Supplier fields
  allocations?: Record<string, number>;
  held_in_reserve?: number;
  price_offered?: number;
  // Buyer fields
  orders?: Record<string, number>;
  max_price_willing_to_pay?: number;
  will_seek_alternatives?: boolean;
  inventory_on_hand?: number;
  // Common fields
  reasoning?: string;
  emotional_state?: EmotionalState;
  trust_scores?: Record<string, number>;
  strategy_shift?: string | null;
}

export interface RoundResult {
  ordered: Record<string, number>;
  received: Record<string, number>;
  fill_rate: number;
}

// Metrics snapshot from one round
export interface RoundMetrics {
  fill_rates: Record<string, number>;
  hoarding_index: Record<string, number>;
  trust_matrix: Record<string, Record<string, number>>;
  price_index: Record<string, number>;
  bullwhip: Record<string, number>;
}

// Streamed decision event
export interface DecisionEvent {
  agent_id: string;
  tier: Tier;
  role: string;
  decision: AgentDecision;
}

// Full round summary from POST /api/step
export interface RoundSummary {
  status: string;
  round: number;
  total_rounds: number;
  event: string;
  agents: Record<string, AgentState>;
  decisions: DecisionEvent[];
  metrics: RoundMetrics;
  total_cost: number;
}

// Full simulation state from GET /api/state
export interface SimulationState {
  status: string;
  current_round: number;
  total_rounds: number;
  current_event: string;
  agents: Record<string, AgentState>;
  metrics: RoundMetrics | null;
  total_cost: number;
  scenario_name: string;
  temperature: number;
}

// SSE event types from POST /api/step/stream
export interface SSEAgentDecided {
  type: "agent_decided";
  agent_id: string;
  tier: Tier;
  role: string;
  decision: AgentDecision & {
    plan?: StrategicPlan;
    signals?: AgentSignal[];
    insights?: string[];
    held_in_reserve?: number;
    reasoning?: string;
  };
}

export interface SSERoundComplete {
  type: "round_complete";
  round: number;
  total_rounds: number;
  event: string;
  agents: Record<string, AgentState>;
  metrics: RoundMetrics;
  total_cost: number;
  status: string;
}

export interface SSEError {
  type: "error";
  message: string;
  exc_type?: string;
  traceback?: string;
}

export type SSEEvent = SSEAgentDecided | SSERoundComplete | SSEError;

// Activity-feed entry built from a streamed SSE decision. The feed grows
// live as rounds advance — each agent_decided event becomes one entry.
export type ActivityRole =
  | "planning"
  | "signaling"
  | "buyer"
  | "supplier"
  | "reflection";

export interface ActivityEntry {
  id: string;
  round: number;
  agentId: string;
  tier: Tier;
  role: ActivityRole;
  emotion?: EmotionalState;
  summary: string;
  detail?: string;
  timestamp: number;
}

// History response from GET /api/history
export interface HistoryRound {
  round: number;
  event: string;
  total_cost: number;
  agents: Record<
    string,
    {
      inventory: number;
      current_price: number;
      emotional_state: EmotionalState;
      fill_rate: number;
      trust_scores: Record<string, number>;
      decision: AgentDecision;
    }
  >;
}

export interface HistoryResponse {
  rounds: HistoryRound[];
}

// Network topology (static, for D3 graph)
export interface NetworkEdge {
  source: string;
  target: string;
}

export const NETWORK_EDGES: NetworkEdge[] = [
  // Foundries → Chip Designers
  { source: "TaiwanSemi", target: "EuroChip" },
  { source: "TaiwanSemi", target: "AmeriSemi" },
  { source: "KoreaSilicon", target: "EuroChip" },
  { source: "KoreaSilicon", target: "AmeriSemi" },
  // Chip Designers → Tier-1
  { source: "EuroChip", target: "BoschAuto" },
  { source: "EuroChip", target: "ContiParts" },
  { source: "AmeriSemi", target: "BoschAuto" },
  { source: "AmeriSemi", target: "ContiParts" },
  // Tier-1 → OEMs
  { source: "BoschAuto", target: "ToyotaMotors" },
  { source: "BoschAuto", target: "FordAuto" },
  { source: "BoschAuto", target: "VolkswagenAG" },
  { source: "ContiParts", target: "ToyotaMotors" },
  { source: "ContiParts", target: "FordAuto" },
  { source: "ContiParts", target: "VolkswagenAG" },
];

// Tier & emotion palettes harmonized with the warm-cream base. Muted,
// perceptually even, and with a common chroma so no tier or emotion
// shouts over the others. The single bright terracotta (var(--primary))
// is reserved for the active/thinking agent so it always reads as signal.
export const TIER_COLORS: Record<Tier, string> = {
  foundry: "#6F5B7E",       // plum
  chipDesigner: "#547587",  // dusty blue
  tier1Supplier: "#7A8A5F", // sage
  oem: "#B6804A",           // muted amber
};

export const TIER_LABELS: Record<Tier, string> = {
  foundry: "Foundry",
  chipDesigner: "Chip Designer",
  tier1Supplier: "Tier-1 Supplier",
  oem: "OEM",
};

export const EMOTIONAL_COLORS: Record<EmotionalState, string> = {
  confident: "#7A8A5F",     // sage
  anxious: "#C2995A",       // soft amber
  angry: "#B85A3C",         // terracotta-red
  opportunistic: "#B6804A", // amber
  cautious: "#6F7A8F",      // slate blue
  loyal: "#547587",         // dusty blue
  panicked: "#A03A28",      // deep red
  vindictive: "#6F3A3A",    // oxblood
};

// ---------------------------------------------------------------------------
// Persona provenance — surfaces the source of each agent's persona text.
// Renders as a badge on agent cards and a line in the inspect panel so the
// audience can trace any persona back to a verifiable public document.
// Keep this in sync with backend/persona_sources.py.
// ---------------------------------------------------------------------------

export interface PersonaSource {
  company: string;       // formal company name in the filing
  document: string;      // "20-F" / "10-K" / "Annual Report"
  fiscalYear: number;    // 2019 for the current baseline
  origin: "SEC" | "IR";  // SEC EDGAR vs investor-relations website
}

export const PERSONA_SOURCES: Record<AgentId, PersonaSource> = {
  TaiwanSemi:   { company: "TSMC", document: "20-F", fiscalYear: 2019, origin: "SEC" },
  KoreaSilicon: { company: "Samsung Electronics", document: "Business Report", fiscalYear: 2019, origin: "IR" },
  EuroChip:     { company: "Infineon Technologies", document: "Annual Report", fiscalYear: 2019, origin: "IR" },
  AmeriSemi:    { company: "NXP Semiconductors", document: "10-K", fiscalYear: 2019, origin: "SEC" },
  BoschAuto:    { company: "Robert Bosch GmbH", document: "Annual Report", fiscalYear: 2019, origin: "IR" },
  ContiParts:   { company: "Continental AG", document: "Annual Report", fiscalYear: 2019, origin: "IR" },
  ToyotaMotors: { company: "Toyota Motor Corporation", document: "20-F", fiscalYear: 2019, origin: "SEC" },
  FordAuto:     { company: "Ford Motor Company", document: "10-K", fiscalYear: 2019, origin: "SEC" },
  VolkswagenAG: { company: "Volkswagen AG", document: "Annual Report", fiscalYear: 2019, origin: "IR" },
};

// ---------------------------------------------------------------------------
// Experiment registry — types for the GET /api/experiments endpoints
// ---------------------------------------------------------------------------

export interface ExperimentSummary {
  id: string;
  label: string;
  created_at: string;
  config: {
    seed?: number;
    temperature?: number;
    total_rounds?: number;
    phase_concurrency?: number;
    scenario?: string;
    persona_variant?: string;
  };
  summary: {
    wall_clock_sec?: number;
    total_cost_usd?: number;
    rounds_completed?: number;
    error_count?: number;
  };
  git: {
    branch?: string;
    commit_short?: string;
    dirty?: boolean;
  };
  notes: string;
}

export interface ExperimentRunRound {
  round: number;
  event: string;
  elapsed_sec: number;
  round_cost_usd: number;
  cumulative_cost_usd: number;
  metrics: RoundMetrics | null;
  agents: Record<string, Partial<AgentState> & {
    tier: Tier;
    inventory: number;
    current_price: number;
    fill_rate: number;
    emotional_state: EmotionalState;
    profit: number;
    current_decision: AgentDecision | null;
  }>;
  events: DecisionEvent[];
  status: string;
  error_count: number;
}

export interface ExperimentDetail {
  meta: ExperimentSummary;
  run: {
    meta: Record<string, unknown>;
    per_round: ExperimentRunRound[];
  };
}
