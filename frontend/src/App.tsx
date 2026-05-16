import { useEffect, useMemo, useRef, useState } from "react";
import { ItineraryView } from "./components/ItineraryView";
import { PhoneFrame } from "./components/PhoneFrame";
import { RePlanCard } from "./components/RePlanCard";
import { StatusBar } from "./components/StatusBar";
import { connectBroker } from "./lib/brokerClient";
import { FLIGHT, ITINERARY, TRAVELER } from "./lib/mockData";
import type { DisruptionAlert, FlightInfo, ItineraryItem, RePlan } from "./types";

interface TravelerPayload {
  traveler: { user_id: string; name: string };
  flight: FlightInfo;
  itinerary: ItineraryItem[];
  trip: { trip_id: string; destination_city: string; destination_iata: string; start_date: string; end_date: string };
}

function getTravelerId(): string | null {
  if (typeof window === "undefined") return null;
  return (window as unknown as { __TRAVELER_ID__?: string }).__TRAVELER_ID__ ?? null;
}

type ToastTone = "info" | "success";

interface ToastState {
  id: number;
  tone: ToastTone;
  title: string;
  body?: string;
}

export default function App() {
  const [trip, setTrip] = useState<TravelerPayload | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [replan, setReplan] = useState<RePlan | null>(null);
  const [replanning, setReplanning] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const brokerRef = useRef<ReturnType<typeof connectBroker> | null>(null);
  const toastIdRef = useRef(0);

  function showToast(t: Omit<ToastState, "id">) {
    toastIdRef.current += 1;
    setToast({ ...t, id: toastIdRef.current });
  }

  useEffect(() => {
    const travelerId = getTravelerId();
    if (!travelerId) {
      setTrip({
        traveler: { user_id: TRAVELER.userId, name: TRAVELER.name },
        flight: FLIGHT,
        itinerary: ITINERARY,
        trip: {
          trip_id: "mock-trip",
          destination_city: "Tokyo",
          destination_iata: "NRT",
          start_date: "2026-05-13",
          end_date: "2026-05-17",
        },
      });
      return;
    }
    let cancelled = false;
    fetch(`/api/travelers/${encodeURIComponent(travelerId)}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: TravelerPayload) => {
        if (!cancelled) setTrip(data);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(String(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    brokerRef.current = connectBroker({
      onDisruption: (a: DisruptionAlert) => {
        setReplanning(true);
        showToast({
          tone: "info",
          title: "Disruption detected on your flight.",
          body: `Reason: ${a.reason || "schedule change"}. We are re-planning automatically — feel free to keep enjoying your flight.`,
        });
      },
      onReplan: (r) => {
        setReplan(r);
        setReplanning(false);
        setAccepted(false);
        showToast({
          tone: "success",
          title: "Re-plan ready.",
          body: "Your updated itinerary is below.",
        });
      },
      onError: (err) => console.warn("[broker]", err),
    });
    return () => brokerRef.current?.close();
  }, []);

  const flight = useMemo<FlightInfo | null>(() => {
    if (!trip) return null;
    if (!replan) return trip.flight;
    return { ...trip.flight, status: "DELAYED" };
  }, [replan, trip]);

  const cancelledTitles = useMemo<Set<string>>(() => {
    if (!replan) return new Set();
    const out = new Set<string>();
    for (const shift of replan.itineraryShifts) {
      if (/cancel|skip|drop|remove|omit|scrap/i.test(shift.note ?? "") ||
          /cancel|skip|drop|remove|omit|scrap/i.test(shift.title ?? "")) {
        out.add(shift.title.trim().toLowerCase());
      }
    }
    return out;
  }, [replan]);

  if (loadError) {
    return (
      <PhoneFrame>
        <div className="p-5 text-sm text-red-600">
          Failed to load your trip: {loadError}. Please re-scan from the kiosk.
        </div>
      </PhoneFrame>
    );
  }

  if (!trip || !flight) {
    return (
      <PhoneFrame>
        <div className="p-5 text-sm text-slate-500">Loading your trip…</div>
      </PhoneFrame>
    );
  }

  return (
    <PhoneFrame>
      <StatusBar travelerName={trip.traveler.name} />
      <InFlightBanner
        travelerName={trip.traveler.name}
        replanning={replanning}
        replanned={replan !== null}
      />
      <ItineraryView
        travelerName={trip.traveler.name}
        destinationCity={trip.trip.destination_city}
        flight={flight}
        itinerary={trip.itinerary}
        cancelledTitles={cancelledTitles}
      />
      {replan && !accepted && (
        <RePlanCard
          replan={replan}
          onAccept={() => {
            setAccepted(true);
          }}
        />
      )}
      {accepted && (
        <div className="mx-5 mt-3 rounded-2xl bg-emerald-50 p-4 text-sm font-semibold text-emerald-700 shadow-sm">
          Trip updated. Confirmation sent.
        </div>
      )}
      {toast && (
        <Toast
          key={toast.id}
          tone={toast.tone}
          title={toast.title}
          body={toast.body}
          onDismiss={() => setToast(null)}
        />
      )}
      <DemoControls
        onTrigger={() => brokerRef.current?.triggerMockDisruption()}
        onReplan={() => brokerRef.current?.triggerMockReplan()}
      />
    </PhoneFrame>
  );
}

function InFlightBanner({
  travelerName,
  replanning,
  replanned,
}: {
  travelerName: string;
  replanning: boolean;
  replanned: boolean;
}) {
  const first = travelerName.split(" ")[0];
  if (replanning && !replanned) {
    return (
      <div className="mx-5 mt-3 flex items-center gap-3 rounded-2xl bg-amber-50 p-3 text-xs text-amber-800 shadow-sm">
        <span
          aria-hidden="true"
          className="inline-block h-4 w-4 flex-none animate-spin rounded-full border-2 border-amber-400 border-t-transparent"
        />
        <span>Re-planning your trip in real time — hang tight, we are on it.</span>
      </div>
    );
  }
  if (replanned) {
    return (
      <div className="mx-5 mt-3 rounded-2xl bg-amber-50 p-3 text-xs text-amber-800 shadow-sm">
        Your plan has been updated. Sit back — we have you covered.
      </div>
    );
  }
  return (
    <div className="mx-5 mt-3 rounded-2xl bg-sky-50 p-3 text-xs text-sky-800 shadow-sm">
      Hi {first}, your flight is on its way. Sit back and enjoy the journey — we are watching for any changes for you.
    </div>
  );
}

function Toast({
  tone,
  title,
  body,
  onDismiss,
}: {
  tone: ToastTone;
  title: string;
  body?: string;
  onDismiss: () => void;
}) {
  const tones: Record<ToastTone, string> = {
    info: "bg-slate-900 text-white",
    success: "bg-emerald-600 text-white",
  };
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-24 z-50 flex justify-center px-4">
      <div
        className={`pointer-events-auto w-full max-w-sm rounded-2xl px-4 py-3 shadow-lg ${tones[tone]}`}
        role="status"
      >
        <div className="flex items-start gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold">{title}</p>
            {body && <p className="mt-1 text-xs opacity-90">{body}</p>}
          </div>
          <button
            type="button"
            onClick={onDismiss}
            className="rounded-full bg-white/20 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide hover:bg-white/30"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

function DemoControls({ onTrigger, onReplan }: { onTrigger: () => void; onReplan: () => void }) {
  return (
    <div className="border-t border-slate-200 bg-white/60 px-5 py-3 backdrop-blur">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onTrigger}
          className="flex-1 rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white shadow-sm transition hover:bg-slate-700"
        >
          Mock disruption
        </button>
        <button
          type="button"
          onClick={onReplan}
          className="flex-1 rounded-full bg-emerald-600 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white shadow-sm transition hover:bg-emerald-500"
        >
          Mock replan
        </button>
      </div>
    </div>
  );
}
