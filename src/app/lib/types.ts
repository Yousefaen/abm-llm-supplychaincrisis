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
