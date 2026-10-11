import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { apiClient } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
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

export const JobsPage = () => {
  const { jobs, loading, error, refresh } = useJobsData();
  const [searchParams] = useSearchParams();
  const clientFilter = searchParams.get("clientId");

  const visibleJobs = useMemo(() => {
    if (!clientFilter) {
      return jobs;
    }
    const id = Number(clientFilter);
    return jobs.filter((entry) => entry.client.id === id);
  }, [clientFilter, jobs]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Reconciliation Jobs</h1>
          <p className="text-sm text-slate-500">Track background processing across all client workspaces.</p>
        </div>
        <button
          onClick={() => refresh()}
          className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm"
        >
          Refresh
        </button>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">Job ID</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Invoices</th>
              <th className="px-4 py-3">Match %</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-slate-500">
                  Loading jobs...
                </td>
              </tr>
            )}
            {!loading && error && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-rose-500">
                  {error}
                </td>
              </tr>
            )}
            {!loading && !error && visibleJobs.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-slate-500">
                  No jobs found yet. Upload files from the Upload tab.
                </td>
              </tr>
            )}
            {visibleJobs.map(({ job, client }) => {
              const matchPercent = job.total_invoices ? ((job.match_count / job.total_invoices) * 100).toFixed(1) : "0.0";
              return (
                <tr key={job.id} className="border-b last:border-b-0">
                  <td className="px-4 py-3 font-semibold text-slate-900">{client.name}</td>
                  <td className="px-4 py-3 font-mono text-sm text-slate-600">#{job.id}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-600">{job.total_invoices.toLocaleString()}</td>
                  <td className="px-4 py-3 text-slate-600">{matchPercent}%</td>
                  <td className="px-4 py-3 text-slate-500">{new Date(job.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                        onClick={() => refresh()}
                      >
                        Refresh
                      </button>
                      <button
                        className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 disabled:opacity-50"
                        disabled={job.status !== "completed"}
                        onClick={() => downloadReport(job.id, `GSTRecon-${client.name}-job-${job.id}.xlsx`)}
                      >
                        Download report
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
