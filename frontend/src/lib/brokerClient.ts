import solace from "solclientjs";

import type { DisruptionAlert, RePlan } from "../types";

declare global {
  interface Window {
    __TRAVELER_ID__?: string;
  }
}

const USE_MOCK = (import.meta.env.VITE_USE_MOCK ?? "false") !== "false";
const BROKER_URL = import.meta.env.VITE_BROKER_URL ?? "ws://192.168.88.188:8008";
const BROKER_VPN = import.meta.env.VITE_BROKER_VPN ?? "ai168";
const BROKER_USER = import.meta.env.VITE_BROKER_USER ?? "user01";
const BROKER_PASSWORD = import.meta.env.VITE_BROKER_PASSWORD ?? "password";

function travelerId(): string {
  return (
    (typeof window !== "undefined" && window.__TRAVELER_ID__) ||
    import.meta.env.VITE_TRAVELER_ID ||
    "demo-traveler-001"
  );
}

function replyTopic(): string {
  return `D/res/${travelerId()}/>`;
}

const CHAOS_TOPIC = "D/changes/flight/>";

let solaceInitialized = false;
function ensureSolaceInit(): void {
  if (solaceInitialized) return;
  const factoryProps = new solace.SolclientFactoryProperties();
  factoryProps.profile = solace.SolclientFactoryProfiles.version10;
  solace.SolclientFactory.init(factoryProps);
  solace.SolclientFactory.setLogLevel(solace.LogLevel.WARN);
  solaceInitialized = true;
}

export interface BrokerHandlers {
  onReplan: (replan: RePlan) => void;
  onDisruption?: (alert: DisruptionAlert) => void;
  onError: (err: Error) => void;
}

export interface BrokerHandle {
  triggerMockReplan: () => void;
  triggerMockDisruption: () => void;
  close: () => void;
}

export function connectBroker(handlers: BrokerHandlers): BrokerHandle {
  if (USE_MOCK) {
    return mockBroker(handlers);
  }
  return realBroker(handlers);
}

function mockBroker(handlers: BrokerHandlers): BrokerHandle {
  return {
    triggerMockDisruption: () => {
      handlers.onDisruption?.({
        flightNo: "JL001",
        status: "DELAYED",
        delayMinutes: 180,
        reason: "weather",
        issuedAt: new Date().toISOString(),
      });
    },
    triggerMockReplan: () => {
      handlers.onReplan({
        headline: "JL001 delayed 180 min — plan shifted",
        weather: "18°C, light rain at the new arrival window",
        itineraryShifts: [
          { time: "15:00", title: "Senso-ji temple visit", note: "moved from 09:00 due to delay" },
          { time: "18:00", title: "Tsukiji food tour", note: "kept; reservations confirmed" },
        ],
        agentSteps: [],
      });
    },
    close: () => {},
  };
}

function realBroker(handlers: BrokerHandlers): BrokerHandle {
  ensureSolaceInit();
  const myTraveler = travelerId();
  const topic = replyTopic();
  const session = solace.SolclientFactory.createSession({
    url: BROKER_URL,
    vpnName: BROKER_VPN,
    userName: BROKER_USER,
    password: BROKER_PASSWORD,
    reconnectRetries: 3,
    reconnectRetryWaitInMsecs: 3000,
  });

  session.on(solace.SessionEventCode.UP_NOTICE, () => {
    try {
      session.subscribe(
        solace.SolclientFactory.createTopicDestination(topic),
        true,
        topic,
        10000,
      );
      session.subscribe(
        solace.SolclientFactory.createTopicDestination(CHAOS_TOPIC),
        true,
        CHAOS_TOPIC,
        10000,
      );
    } catch (err) {
      handlers.onError(err instanceof Error ? err : new Error(String(err)));
    }
  });
  session.on(solace.SessionEventCode.CONNECT_FAILED_ERROR, (evt) => {
    handlers.onError(new Error(`broker connect failed: ${evt?.message ?? "unknown"}`));
  });
  session.on(solace.SessionEventCode.SUBSCRIPTION_ERROR, (evt) => {
    handlers.onError(new Error(`broker subscription error: ${evt?.message ?? "unknown"}`));
  });
  session.on(solace.SessionEventCode.MESSAGE, (message) => {
    try {
      const dest = message.getDestination?.()?.getName?.() ?? "";
      const body = message.getBinaryAttachment?.();
      const rawText = typeof body === "string" ? body : body ? new TextDecoder().decode(body) : "";
      if (!rawText) return;
      // Solace SDT-wrapped payloads (publisher used `str`/`String`) carry a
      // type-marker byte before the actual JSON. Trim any prefix that does
      // not look like JSON so we tolerate both raw-byte and SDT publishers.
      const firstJson = rawText.search(/[\[{]/);
      const text = firstJson > 0 ? rawText.slice(firstJson) : rawText;
      const obj = JSON.parse(text);
      if (dest.startsWith("D/changes/flight/")) {
        const disruptionTraveler = String(
          (obj as Record<string, unknown>).traveler_id ?? "",
        );
        if (disruptionTraveler && disruptionTraveler !== myTraveler) return;
        handlers.onDisruption?.(parseDisruption(obj));
        return;
      }
      if (dest.endsWith("/ng")) {
        handlers.onError(new Error(typeof obj === "string" ? obj : JSON.stringify(obj)));
        return;
      }
      handlers.onReplan(normaliseReplan(obj));
    } catch (err) {
      handlers.onError(err instanceof Error ? err : new Error(String(err)));
    }
  });

  try {
    session.connect();
  } catch (err) {
    handlers.onError(err instanceof Error ? err : new Error(String(err)));
  }

  return {
    triggerMockReplan: () => mockBroker(handlers).triggerMockReplan(),
    triggerMockDisruption: () => mockBroker(handlers).triggerMockDisruption(),
    close: () => {
      try {
        session.disconnect();
      } catch {
        // ignore — session already torn down
      }
    },
  };
}

function parseDisruption(obj: Record<string, unknown>): DisruptionAlert {
  const flight = (obj.flight as Record<string, unknown> | undefined) ?? {};
  const change = (obj.change as Record<string, unknown> | undefined) ?? {};
  return {
    flightNo: String(flight.flight_no ?? ""),
    status: String(change.new_status ?? "DELAYED"),
    delayMinutes: Number(change.delay_minutes ?? 0),
    reason: String(change.reason ?? ""),
    issuedAt: String(obj.issued_at ?? new Date().toISOString()),
  };
}

function normaliseReplan(obj: Record<string, unknown>): RePlan {
  const shifts = Array.isArray(obj.itineraryShifts)
    ? (obj.itineraryShifts as Array<Record<string, unknown>>).map((s) => ({
        time: String(s.time ?? ""),
        title: String(s.title ?? ""),
        note: String(s.note ?? ""),
      }))
    : [];
  const steps = Array.isArray(obj.agentSteps)
    ? (obj.agentSteps as Array<Record<string, unknown>>).map((s) => ({
        agent: String(s.agent ?? ""),
        label: String(s.label ?? ""),
        status: (String(s.status ?? "done")) as "pending" | "running" | "done",
      }))
    : [];
  return {
    headline: String(obj.headline ?? ""),
    weather: String(obj.weather ?? ""),
    itineraryShifts: shifts,
    agentSteps: steps,
  };
}
