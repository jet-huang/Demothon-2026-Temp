export interface ItineraryItem {
  day: number;
  date: string;
  time: string;
  title: string;
  location: string;
  activityType: string;
}

export interface FlightInfo {
  flightNo: string;
  carrier: string;
  origin: string;
  destination: string;
  scheduledDeparture: string;
  scheduledArrival: string;
  status: "ON_TIME" | "DELAYED" | "CANCELLED" | "GATE_CHANGE";
  gate: string;
}

export interface DisruptionAlert {
  flightNo: string;
  status: string;
  delayMinutes: number;
  reason: string;
  issuedAt: string;
}

export interface AgentStep {
  agent: string;
  label: string;
  status: "pending" | "running" | "done";
}

export interface RePlan {
  headline: string;
  weather: string;
  itineraryShifts: Array<{ time: string; title: string; note: string }>;
  agentSteps: AgentStep[];
}
