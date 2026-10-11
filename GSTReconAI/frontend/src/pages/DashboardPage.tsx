import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiClient } from "../api/client";
import { StatsCard } from "../components/StatsCard";
import { DashboardMetrics, MonthlyTrend, RiskSupplier } from "../types/models";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const percent = (value?: number) => `${((value ?? 0) * 100).toFixed(1)}%`;

export const DashboardPage = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trend, setTrend] = useState<MonthlyTrend[]>([]);
  const [risks, setRisks] = useState<RiskSupplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [metricsRes, trendRes, riskRes] = await Promise.all([
          apiClient.get<DashboardMetrics>("/reconciliation/dashboard/metrics"),
          apiClient.get<MonthlyTrend[]>("/reconciliation/dashboard/monthly-trend"),
          apiClient.get<RiskSupplier[]>("/reconciliation/dashboard/top-risk"),
        ]);
        setMetrics(metricsRes.data);
        setTrend(trendRes.data);
        setRisks(riskRes.data);
      } catch (err) {
        setError("Unable to load dashboard data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className="rounded-xl border border-slate-200 bg-white p-6 text-slate-500">Loading dashboard...</div>;
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-rose-700">
        <p className="font-semibold">{error}</p>
        <p className="text-sm text-rose-500">Check your API server and try again.</p>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Executive Dashboard</h1>
        <p className="text-sm text-slate-500">
          Track GST reconciliation throughput, ITC leakage, and risky suppliers in near real-time.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard label="Active Clients" value={metrics.total_clients} subtext="Workspaces managed" />
        <StatsCard label="Invoices processed" value={metrics.total_invoices.toLocaleString()} subtext="Last 60 days" />
        <StatsCard label="Book ITC" value={currency.format(metrics.total_itc_purchase)} subtext="Purchases ledger" />
        <StatsCard label="2B vs Book" value={currency.format(metrics.difference)} subtext="Variance" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Match Quality</p>
              <p className="text-xl font-semibold text-slate-900">{percent(metrics.match_ratio)} match rate</p>
            </div>
            <div className="text-right text-sm text-slate-500">
              <p>Mismatches: {percent(metrics.mismatch_ratio)}</p>
              <p>Missing: {percent(metrics.missing_ratio)}</p>
            </div>
          </div>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="4 4" stroke="#e2e8f0" />
                <XAxis dataKey="month" stroke="#475569" />
                <YAxis stroke="#475569" />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="match_count" stroke="#0ea5e9" strokeWidth={2} name="Matches" />
                <Line type="monotone" dataKey="mismatch_count" stroke="#f43f5e" strokeWidth={2} name="Mismatches" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-slate-700">Top GSTINs Needing Attention</p>
          <p className="text-xs text-slate-500">Focus review on suppliers with repeated mismatches</p>
          <div className="mt-4 divide-y divide-slate-100">
            {risks.length === 0 && <p className="py-4 text-sm text-slate-500">No critical mismatches yet 🎉</p>}
            {risks.map((risk) => (
              <div key={risk.supplier_gstin} className="flex items-center justify-between py-3">
                <div>
                  <p className="font-semibold text-slate-900">{risk.supplier_gstin}</p>
                  <p className="text-xs text-slate-500">Tax gap ~ {currency.format(risk.tax_gap)}</p>
                </div>
                <span className="text-sm font-semibold text-rose-600">{risk.mismatch_count} mismatches</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
