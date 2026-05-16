export function StatusBar({ travelerName }: { travelerName: string }) {
  return (
    <div className="flex items-center justify-between px-6 pt-8 pb-2 text-xs font-medium text-slate-500">
      <span>9:41</span>
      <span className="font-semibold text-slate-700">Wayfarer</span>
      <span>{travelerName.split(" ")[0]}</span>
    </div>
  );
}
