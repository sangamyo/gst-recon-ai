import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { apiClient } from "../api/client";
import { Client } from "../types/models";

export const UploadPage = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [clientId, setClientId] = useState<string>("");
  const [purchaseFile, setPurchaseFile] = useState<File | null>(null);
  const [gstrFile, setGstrFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const loadClients = async () => {
      try {
        const { data } = await apiClient.get<Client[]>("/clients");
        setClients(data);
        const preselected = searchParams.get("clientId") || (data[0]?.id.toString() ?? "");
        setClientId(preselected);
      } catch (err) {
        setStatus("Unable to load clients. Refresh and try again.");
      }
    };
    loadClients();
  }, [searchParams]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!clientId || !purchaseFile || !gstrFile) {
      setStatus("Select a client and both Excel files before uploading.");
      return;
    }
    setLoading(true);
    setStatus("Uploading sheets and creating job...");
    try {
      const formData = new FormData();
      formData.append("purchase_file", purchaseFile);
      formData.append("gstr2b_file", gstrFile);
      const { data } = await apiClient.post(`/clients/${clientId}/jobs`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setStatus(`Job #${data.job_id} queued successfully!`);
      setPurchaseFile(null);
      setGstrFile(null);
      (event.target as HTMLFormElement).reset();
    } catch (err) {
      setStatus("Upload failed. Validate the template and try again.");
    } finally {
      setLoading(false);
    }
  };

  const fileLabel = (file: File | null) => file?.name || "No file selected";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Upload GST Data</h1>
        <p className="text-sm text-slate-500">Drop FY purchase and GSTR-2B workbooks to initiate a reconciliation job.</p>
      </div>
      <form onSubmit={handleSubmit} className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 shadow-sm">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="client-select" className="text-sm font-semibold text-slate-600">
              Client
            </label>
            <select
              id="client-select"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              value={clientId}
              onChange={(event: ChangeEvent<HTMLSelectElement>) => setClientId(event.target.value)}
            >
              <option value="">Select client</option>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.name} — {client.gstin}
                </option>
              ))}
            </select>
          </div>
          <div className="rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-500">
            Each workbook should follow the prescribed headers (Supplier GSTIN, Invoice Number, Taxable Value, Tax Amount...).
          </div>
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <label className="flex flex-col rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            <span className="font-semibold text-slate-900">Purchase register (.xlsx)</span>
            <span className="mt-1 text-xs text-slate-500">Headers: Supplier GSTIN, Invoice No, Taxable, IGST/CGST/SGST.</span>
            <input
              type="file"
              accept=".xlsx,.xls"
              className="mt-3 cursor-pointer"
              onChange={(event: ChangeEvent<HTMLInputElement>) => setPurchaseFile(event.target.files?.[0] ?? null)}
            />
            <span className="mt-2 text-xs text-slate-500">{fileLabel(purchaseFile)}</span>
          </label>
          <label className="flex flex-col rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            <span className="font-semibold text-slate-900">GSTR-2B download (.xlsx)</span>
            <span className="mt-1 text-xs text-slate-500">Use the official portal CSV export converted to Excel.</span>
            <input
              type="file"
              accept=".xlsx,.xls"
              className="mt-3 cursor-pointer"
              onChange={(event: ChangeEvent<HTMLInputElement>) => setGstrFile(event.target.files?.[0] ?? null)}
            />
            <span className="mt-2 text-xs text-slate-500">{fileLabel(gstrFile)}</span>
          </label>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="mt-6 rounded-xl bg-primary px-6 py-3 font-semibold text-white shadow-lg"
        >
          {loading ? "Processing..." : "Queue reconciliation job"}
        </button>
        {status && <p className="mt-3 text-sm text-slate-600">{status}</p>}
      </form>
    </div>
  );
};
