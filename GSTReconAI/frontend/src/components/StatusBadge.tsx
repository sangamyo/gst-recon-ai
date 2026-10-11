const colors: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-rose-100 text-rose-700",
};

export const StatusBadge = ({ status }: { status: string }) => {
  const className = colors[status] || "bg-slate-100 text-slate-600";
  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${className}`}>{status}</span>;
};
