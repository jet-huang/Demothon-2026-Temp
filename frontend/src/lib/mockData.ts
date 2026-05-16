import type { DisruptionAlert, FlightInfo, ItineraryItem, RePlan } from "../types";

export const TRAVELER = {
  name: "Hsiao-Hua Chen",
  userId: "demo-traveler-001",
};

export const FLIGHT: FlightInfo = {
  flightNo: "JL001",
  carrier: "Japan Airlines",
  origin: "SFO",
  destination: "NRT",
  scheduledDeparture: "2026-05-13T11:00:00-07:00",
  scheduledArrival: "2026-05-14T15:30:00+09:00",
  status: "ON_TIME",
  gate: "A8",
};

export const ITINERARY: ItineraryItem[] = [
  { day: 1, date: "2026-05-14", time: "16:00", title: "Hotel check-in", location: "Shinjuku Granbell Hotel", activityType: "lodging" },
  { day: 1, date: "2026-05-14", time: "19:00", title: "Dinner: Tsukiji-style sushi", location: "Sushi Zanmai Shinjuku", activityType: "dining" },
  { day: 2, date: "2026-05-15", time: "09:30", title: "Senso-ji Temple", location: "Asakusa", activityType: "sightseeing" },
  { day: 2, date: "2026-05-15", time: "11:30", title: "Asakusa walking tour", location: "Asakusa", activityType: "tour" },
  { day: 2, date: "2026-05-15", time: "14:00", title: "Tokyo Skytree", location: "Sumida", activityType: "sightseeing" },
  { day: 3, date: "2026-05-16", time: "10:00", title: "teamLab Planets", location: "Toyosu", activityType: "sightseeing" },
  { day: 3, date: "2026-05-16", time: "15:00", title: "Shibuya Crossing + Hachiko", location: "Shibuya", activityType: "sightseeing" },
];

export const SAMPLE_ALERT: DisruptionAlert = {
  flightNo: "JL001",
  status: "DELAYED",
  delayMinutes: 180,
  reason: "weather",
  issuedAt: new Date().toISOString(),
};

export const SAMPLE_REPLAN: RePlan = {
  headline: "JL001 delayed 3h. Hotel check-in moves to 19:00; day-2 plan reshuffled.",
  weather: "Tokyo 2026-05-15: Rain, 19/15 C, 70% precip. Carry an umbrella.",
  itineraryShifts: [
    { time: "19:00", title: "Hotel check-in", note: "shifted +3h" },
    { time: "21:30", title: "Dinner: late-night ramen swap", note: "sushi replaced (closes 22:00)" },
    { time: "09:30", title: "Senso-ji Temple", note: "kept — covered approach if rain" },
    { time: "11:30", title: "Asakusa walking tour", note: "kept; tour operator confirms covered route" },
    { time: "14:00", title: "Tokyo Skytree", note: "moved to indoor observation deck only" },
  ],
  agentSteps: [
    { agent: "Orchestrator", label: "Received disruption", status: "done" },
    { agent: "FlightsAgent", label: "Verified JL001 status", status: "done" },
    { agent: "WeatherAgent", label: "Pulled 2026-05-15 forecast", status: "done" },
    { agent: "ItineraryAgent", label: "Proposed shifted plan", status: "done" },
  ],
};
