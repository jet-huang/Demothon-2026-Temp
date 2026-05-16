import type { AgentStep } from "../types";

const DOT_COLOR: Record<AgentStep["status"], string> = {
  pending: "bg-slate-300",
  running: "bg-indigo-500 animate-pulse",
  done: "bg-emerald-500",
};

export function AgentFlow({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="mx-5 mt-3 rounded-2xl bg-slate-900 p-3 text-xs text-slate-100 shadow-sm">
      <div className="mb-2 font-semibold uppercase tracking-wide text-slate-400">
        Agent mesh
      </div>
      <ul className="space-y-1.5">
        {steps.map((step) => (
          <li key={`${step.agent}-${step.label}`} className="flex items-center gap-2">
            <span className={`inline-flex h-2 w-2 rounded-full ${DOT_COLOR[step.status]}`} />
            <span className="font-semibold text-slate-100">{step.agent}</span>
            <span className="text-slate-400">·</span>
            <span className="truncate text-slate-300">{step.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
