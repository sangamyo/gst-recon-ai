interface StatsCardProps {
  label: string;
  value: string | number;
  subtext?: string;
}

export const StatsCard = ({ label, value, subtext }: StatsCardProps) => (
  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <p className="text-sm text-slate-500">{label}</p>
    <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    {subtext && <p className="text-xs text-slate-400">{subtext}</p>}
  </div>
);
