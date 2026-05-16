import type { AgentStep, DisruptionAlert, RePlan } from "../types";
import { SAMPLE_REPLAN } from "./mockData";

const SAM_BASE = import.meta.env.VITE_SAM_BASE ?? "http://localhost:8000";
const USE_MOCK = (import.meta.env.VITE_USE_MOCK ?? "true") !== "false";

export interface RePlanStream {
  onStep: (step: AgentStep) => void;
  onFinal: (replan: RePlan) => void;
  onError: (err: Error) => void;
}

export function requestReplan(alert: DisruptionAlert, handlers: RePlanStream): () => void {
  if (USE_MOCK) {
    return runMockStream(handlers);
  }
  return runRealStream(alert, handlers);
}

function runMockStream(handlers: RePlanStream): () => void {
  let cancelled = false;
  const steps = SAMPLE_REPLAN.agentSteps;
  steps.forEach((step, idx) => {
    setTimeout(() => {
      if (cancelled) return;
      handlers.onStep({ ...step, status: "running" });
    }, 200 + idx * 700);
    setTimeout(() => {
      if (cancelled) return;
      handlers.onStep({ ...step, status: "done" });
    }, 200 + idx * 700 + 600);
  });
  setTimeout(() => {
    if (cancelled) return;
    handlers.onFinal(SAMPLE_REPLAN);
  }, 200 + steps.length * 700 + 600);
  return () => {
    cancelled = true;
  };
}

function runRealStream(alert: DisruptionAlert, handlers: RePlanStream): () => void {
  const controller = new AbortController();
  const prompt = buildPrompt(alert);
  let lastFinal: RePlan | null = null;
  fetch(`${SAM_BASE}/api/v2/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ prompt }),
    signal: controller.signal,
  })
    .then(async (resp) => {
      if (!resp.body) throw new Error("no response body from SAM");
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const ev of events) {
          const maybeFinal = tryDispatch(ev, handlers);
          if (maybeFinal) lastFinal = maybeFinal;
        }
      }
      handlers.onFinal(
        lastFinal ?? { ...SAMPLE_REPLAN, headline: "SAM stream ended without a structured re-plan payload." },
      );
    })
    .catch((err) => {
      if (err.name === "AbortError") return;
      handlers.onError(err instanceof Error ? err : new Error(String(err)));
    });
  return () => controller.abort();
}

function buildPrompt(alert: DisruptionAlert): string {
  return [
    `Flight ${alert.flightNo} is now ${alert.status} by ${alert.delayMinutes} minutes (${alert.reason}).`,
    "Acting on behalf of the active traveler (user_id demo-traveler-001):",
    "1. Confirm the flight status via FlightsAgent.",
    "2. Pull the weather forecast for the destination on day 2 via WeatherAgent.",
    "3. Ask ItineraryAgent for a proposed shifted plan for day 1 and day 2.",
    "Return a single compact JSON object with keys: headline, weather, itineraryShifts (array of {time,title,note}).",
  ].join("\n");
}

function tryDispatch(eventChunk: string, handlers: RePlanStream): RePlan | null {
  const dataLine = eventChunk.split("\n").find((l) => l.startsWith("data:"));
  if (!dataLine) return null;
  const payload = dataLine.slice(5).trim();
  if (!payload || payload === "[DONE]") return null;
  try {
    const obj = JSON.parse(payload);
    if (obj?.agent && obj?.label) {
      handlers.onStep({ agent: obj.agent, label: obj.label, status: obj.status ?? "done" });
      return null;
    }
    if (obj?.headline && Array.isArray(obj?.itineraryShifts)) {
      return obj as RePlan;
    }
    if (obj?.final && typeof obj.final === "object") {
      return obj.final as RePlan;
    }
  } catch {
    // ignore unparseable chunks; SAM v2 payload shape will be finalized during integration
  }
  return null;
}
