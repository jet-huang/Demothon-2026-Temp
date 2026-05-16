import type { RePlan } from "../types";

export function RePlanCard({ replan, onAccept }: { replan: RePlan; onAccept: () => void }) {
  return (
    <div className="mx-5 mt-3 rounded-2xl bg-white p-4 shadow-md">
      <div className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
        Proposed re-plan
      </div>
      <p className="mt-1 text-sm font-semibold text-slate-900">{replan.headline}</p>
      <p className="mt-2 text-xs text-slate-500">{replan.weather}</p>
      <ul className="mt-3 space-y-1.5">
        {replan.itineraryShifts.map((shift) => (
          <li key={`${shift.time}-${shift.title}`} className="flex items-start gap-2 text-xs">
            <span className="w-12 shrink-0 font-semibold text-indigo-600">{shift.time}</span>
            <span className="font-medium text-slate-800">{shift.title}</span>
            <span className="text-slate-500">— {shift.note}</span>
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={onAccept}
        className="mt-4 w-full rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500"
      >
        Accept re-plan
      </button>
    </div>
  );
}
