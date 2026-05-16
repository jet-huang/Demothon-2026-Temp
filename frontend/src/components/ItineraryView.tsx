import type { FlightInfo, ItineraryItem } from "../types";

interface Props {
  travelerName: string;
  destinationCity: string;
  flight: FlightInfo;
  itinerary: ItineraryItem[];
  cancelledTitles?: Set<string>;
}

function isCancelled(title: string, cancelled?: Set<string>): boolean {
  if (!cancelled || cancelled.size === 0) return false;
  const t = title.trim().toLowerCase();
  if (cancelled.has(t)) return true;
  for (const c of cancelled) {
    if (t.includes(c) || c.includes(t)) return true;
  }
  return false;
}

export function ItineraryView({ travelerName, destinationCity, flight, itinerary, cancelledTitles }: Props) {
  const byDay = new Map<number, ItineraryItem[]>();
  for (const item of itinerary) {
    if (!byDay.has(item.day)) byDay.set(item.day, []);
    byDay.get(item.day)!.push(item);
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 pb-5">
      <header className="pb-3">
        <h1 className="text-xl font-semibold text-slate-900">Hi, {travelerName.split(" ")[0]}.</h1>
        <p className="text-sm text-slate-500">Your {destinationCity} trip is all set.</p>
      </header>

      <FlightCard flight={flight} />

      {[...byDay.entries()].map(([day, items]) => (
        <section key={day} className="mt-4">
          <div className="mb-2 flex items-baseline justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Day {day}</h2>
            <span className="text-xs text-slate-400">{items[0]?.date}</span>
          </div>
          <ul className="space-y-2">
            {items.map((it) => {
              const cancelled = isCancelled(it.title, cancelledTitles);
              return (
                <li
                  key={`${it.day}-${it.time}-${it.title}`}
                  className={`flex items-start gap-3 rounded-2xl bg-white p-3 shadow-sm transition-all duration-500 ${
                    cancelled ? "opacity-40" : ""
                  }`}
                  aria-label={cancelled ? `${it.title} cancelled` : it.title}
                >
                  <span
                    className={`w-12 shrink-0 text-sm font-semibold ${
                      cancelled ? "text-slate-400 line-through" : "text-indigo-600"
                    }`}
                  >
                    {it.time}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p
                      className={`truncate text-sm font-medium ${
                        cancelled ? "text-slate-500 line-through" : "text-slate-900"
                      }`}
                    >
                      {it.title}
                    </p>
                    <p className="truncate text-xs text-slate-500">{it.location}</p>
                  </div>
                  {cancelled && (
                    <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-rose-700">
                      Cancelled
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}

function FlightCard({ flight }: { flight: FlightInfo }) {
  return (
    <div className="rounded-2xl bg-gradient-to-br from-indigo-600 to-indigo-500 p-4 text-white shadow-md">
      <div className="flex items-center justify-between text-xs uppercase tracking-wide opacity-80">
        <span>{flight.carrier}</span>
        <span>{flight.flightNo}</span>
      </div>
      <div className="mt-2 flex items-center justify-between">
        <FlightEndpoint code={flight.origin} />
        <div className="text-center text-xs opacity-80">
          <div>direct</div>
          <div className="text-2xl">→</div>
        </div>
        <FlightEndpoint code={flight.destination} />
      </div>
      <div className="mt-3 flex items-center justify-between text-xs opacity-80">
        <span>Gate {flight.gate}</span>
        <span className="rounded-full bg-white/20 px-2 py-0.5 text-[10px] uppercase tracking-wide">
          {flight.status.replace("_", " ")}
        </span>
      </div>
    </div>
  );
}

function FlightEndpoint({ code }: { code: string }) {
  return (
    <div className="text-center">
      <p className="text-2xl font-semibold">{code}</p>
    </div>
  );
}
