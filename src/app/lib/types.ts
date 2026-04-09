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
  decision: AgentDecision;
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

export type SSEEvent = SSEAgentDecided | SSERoundComplete;

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

export const TIER_COLORS: Record<Tier, string> = {
  foundry: "#8b5cf6",       // purple
  chipDesigner: "#3b82f6",  // blue
  tier1Supplier: "#22c55e", // green
  oem: "#f97316",           // orange
};

export const TIER_LABELS: Record<Tier, string> = {
  foundry: "Foundry",
  chipDesigner: "Chip Designer",
  tier1Supplier: "Tier-1 Supplier",
  oem: "OEM",
};

export const EMOTIONAL_COLORS: Record<EmotionalState, string> = {
  confident: "#22c55e",
  anxious: "#eab308",
  angry: "#ef4444",
  opportunistic: "#f97316",
  cautious: "#6366f1",
  loyal: "#3b82f6",
  panicked: "#dc2626",
  vindictive: "#991b1b",
};
