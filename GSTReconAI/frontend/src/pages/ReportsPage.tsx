import { useMemo } from "react";
import { apiClient } from "../api/client";
import { StatsCard } from "../components/StatsCard";
import { useJobsData } from "../hooks/useJobsData";

const downloadReport = async (jobId: number, filename: string) => {
  const { data } = await apiClient.get(`/reconciliation/jobs/${jobId}/report`, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.URL.revokeObjectURL(url);
};

export const ReportsPage = () => {
  const { jobs, loading, error, refresh } = useJobsData();

  const completedJobs = useMemo(() => jobs.filter(({ job }) => job.status === "completed"), [jobs]);
  const mismatchInvoices = useMemo(
    () => completedJobs.reduce((sum, entry) => sum + entry.job.mismatch_count + entry.job.missing_count, 0),
    [completedJobs]
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Reports & Downloads</h1>
          <p className="text-sm text-slate-500">Download reconciled workbooks and monitor outstanding issues.</p>
        </div>
        <button
          onClick={() => refresh()}
          className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm"
        >
          Refresh
        </button>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <StatsCard label="Completed jobs" value={completedJobs.length} />
        <StatsCard label="Pending downloads" value={jobs.length - completedJobs.length} />
        <StatsCard label="Invoices needing review" value={mismatchInvoices.toLocaleString()} />
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">Job ID</th>
              <th className="px-4 py-3">Matched</th>
              <th className="px-4 py-3">Mismatched/Missing</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3 text-right">Download</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-500">
                  Loading reports...
                </td>
              </tr>
            )}
            {!loading && error && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-rose-500">
                  {error}
                </td>
              </tr>
            )}
            {!loading && !error && completedJobs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-500">
                  No completed jobs yet.
                </td>
              </tr>
            )}
            {completedJobs.map(({ job, client }) => (
              <tr key={job.id} className="border-b last:border-b-0">
                <td className="px-4 py-3 font-semibold text-slate-900">{client.name}</td>
                <td className="px-4 py-3 font-mono text-sm text-slate-600">#{job.id}</td>
                <td className="px-4 py-3 text-emerald-600">{job.match_count.toLocaleString()}</td>
                <td className="px-4 py-3 text-rose-600">
                  {(job.mismatch_count + job.missing_count).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-slate-500">{new Date(job.created_at).toLocaleString()}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                    onClick={() => downloadReport(job.id, `GSTRecon-${client.name}-job-${job.id}.xlsx`)}
                  >
                    Download
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
