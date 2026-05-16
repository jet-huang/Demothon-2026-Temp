import type { ReactNode } from "react";

export function PhoneFrame({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="relative h-[820px] w-[400px] rounded-[48px] border-[10px] border-slate-950 bg-slate-100 shadow-2xl">
        <div className="absolute left-1/2 top-2 z-10 h-6 w-32 -translate-x-1/2 rounded-b-2xl bg-slate-950" />
        <div className="absolute inset-0 overflow-hidden rounded-[36px]">
          <div className="flex h-full flex-col">{children}</div>
        </div>
      </div>
    </div>
  );
}
