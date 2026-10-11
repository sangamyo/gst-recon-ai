import { ChangeEvent, FormEvent, useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import { Client } from "../types/models";

const initialForm = {
  name: "",
  gstin: "",
};

export const ClientsPage = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchClients = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<Client[]>("/clients");
      setClients(data);
    } catch (err) {
      setError("Unable to load clients");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.name || !form.gstin) {
      setError("Provide both firm name and GSTIN");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const payload = { name: form.name.trim(), gstin: form.gstin.trim().toUpperCase() };
      const { data } = await apiClient.post<Client>("/clients", payload);
      setClients((prev) => [data, ...prev]);
      setForm(initialForm);
    } catch (err) {
      setError("Failed to create client");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Client Workspaces</h1>
          <p className="text-sm text-slate-500">Manage GSTINs you support and trigger reconciliation runs.</p>
        </div>
        <button
          onClick={() => fetchClients()}
          className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm"
        >
          Refresh
        </button>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Add a new GST client</h2>
        <form onSubmit={handleSubmit} className="mt-4 grid gap-4 md:grid-cols-3">
          <input
            name="name"
            placeholder="Acme Manufacturing"
            value={form.name}
            onChange={handleChange}
            className="rounded-lg border border-slate-200 px-3 py-2"
          />
          <input
            name="gstin"
            placeholder="22AAAAA0000A1Z5"
            value={form.gstin}
            onChange={handleChange}
            className="rounded-lg border border-slate-200 px-3 py-2 uppercase"
          />
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-primary px-4 py-2 font-semibold text-white"
          >
            {submitting ? "Creating..." : "Create client"}
          </button>
        </form>
        {error && <p className="mt-2 text-sm text-rose-500">{error}</p>}
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">GSTIN</th>
              <th className="px-4 py-3">Onboarded</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-500">
                  Loading clients...
                </td>
              </tr>
            )}
            {!loading && clients.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-500">
                  No clients yet. Start by onboarding your first GSTIN above.
                </td>
              </tr>
            )}
            {clients.map((client) => (
              <tr key={client.id} className="border-b last:border-b-0">
                <td className="px-4 py-3 font-semibold text-slate-900">{client.name}</td>
                <td className="px-4 py-3 font-mono text-sm text-slate-600">{client.gstin}</td>
                <td className="px-4 py-3 text-slate-500">{new Date(client.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => navigate(`/upload?clientId=${client.id}`)}
                      className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                    >
                      Upload files
                    </button>
                    <button
                      onClick={() => navigate(`/jobs?clientId=${client.id}`)}
                      className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                    >
                      View jobs
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
