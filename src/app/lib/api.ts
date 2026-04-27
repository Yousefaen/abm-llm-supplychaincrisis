import type {
  ExperimentDetail,
  ExperimentSummary,
  HistoryResponse,
  RoundSummary,
  SimulationState,
  SSEEvent,
} from "./types";

// For normal JSON requests the Next.js rewrite proxy works fine (empty string
// means same-origin, rewritten to the backend by next.config.ts).
// For SSE/streaming the rewrite proxy drops the response, so we call the
// backend directly.  NEXT_PUBLIC_API_URL overrides both (set it to the
// externally-reachable backend URL in production).
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const STREAM_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

export async function resetSimulation(
  temperature = 1.0,
  seed?: number
): Promise<SimulationState> {
  return fetchJSON<SimulationState>("/api/reset", {
    method: "POST",
    body: JSON.stringify({ temperature, seed: seed ?? null }),
  });
}

export async function runStep(): Promise<RoundSummary> {
  return fetchJSON<RoundSummary>("/api/step", { method: "POST" });
}

export async function getState(): Promise<SimulationState> {
  return fetchJSON<SimulationState>("/api/state");
}

export async function getHistory(): Promise<HistoryResponse> {
  return fetchJSON<HistoryResponse>("/api/history");
}

export interface ServerConfig {
  persona_variant: string;
}

export async function getServerConfig(): Promise<ServerConfig> {
  return fetchJSON<ServerConfig>("/api/config");
}

export async function listExperiments(): Promise<{ experiments: ExperimentSummary[] }> {
  return fetchJSON<{ experiments: ExperimentSummary[] }>("/api/experiments");
}

export async function getExperiment(id: string): Promise<ExperimentDetail> {
  return fetchJSON<ExperimentDetail>(`/api/experiments/${encodeURIComponent(id)}`);
}

/**
 * Stream a single round via SSE. Calls `onEvent` for each agent decision,
 * then for the final round_complete event.
 */
export async function runStepStream(
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${STREAM_BASE}/api/step/stream`, {
    method: "POST",
    signal,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const payload = JSON.parse(line.slice(6)) as SSEEvent;
          onEvent(payload);
        } catch {
          // skip malformed lines
        }
      }
    }
  }
}
