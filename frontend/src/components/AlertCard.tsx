import type { DisruptionAlert } from "../types";

export function AlertCard({ alert }: { alert: DisruptionAlert }) {
  return (
    <div className="mx-5 mt-3 animate-pulse-once rounded-2xl border border-amber-300 bg-amber-50 p-4 shadow-sm">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-amber-700">
        <span className="inline-flex h-2 w-2 rounded-full bg-amber-500" />
        Live alert
      </div>
      <p className="mt-2 text-sm font-semibold text-amber-900">
        {alert.flightNo} {alert.status.toLowerCase()} by {alert.delayMinutes} min.
      </p>
      <p className="mt-1 text-xs text-amber-800">
        Reason: {alert.reason}. Checking downstream impact on your trip…
      </p>
    </div>
  );
}
