import { useCallback, useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { Client, ReconciliationJob } from "../types/models";

export interface HydratedJob {
  job: ReconciliationJob;
  client: Client;
}

export const useJobsData = () => {
  const [jobs, setJobs] = useState<HydratedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data: clients } = await apiClient.get<Client[]>("/clients");
      const jobGroups = await Promise.all(
        clients.map(async (client) => {
          const { data: clientJobs } = await apiClient.get<ReconciliationJob[]>(`/clients/${client.id}/jobs`);
          return clientJobs.map((job) => ({ job, client }));
        })
      );
      const flattened = jobGroups.flat();
      flattened.sort((a, b) => new Date(b.job.created_at).getTime() - new Date(a.job.created_at).getTime());
      setJobs(flattened);
    } catch (err) {
      setError("Unable to load jobs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  return { jobs, loading, error, refresh: fetchJobs };
};
