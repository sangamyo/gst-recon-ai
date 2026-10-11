export type UserRole = "admin" | "accountant";

export interface DashboardMetrics {
  total_clients: number;
  total_invoices: number;
  match_ratio: number;
  mismatch_ratio: number;
  missing_ratio: number;
  total_itc_purchase: number;
  total_itc_2b: number;
  difference: number;
}

export interface Client {
  id: number;
  name: string;
  gstin: string;
  created_at: string;
}

export interface ReconciliationJob {
  id: number;
  client_id: number;
  status: string;
  total_invoices: number;
  match_count: number;
  mismatch_count: number;
  missing_count: number;
  extra_count: number;
  purchase_itc_total: number;
  gstr2b_itc_total: number;
  report_path?: string;
  created_at: string;
}

export interface RiskSupplier {
  supplier_gstin: string;
  mismatch_count: number;
  tax_gap: number;
}

export interface MonthlyTrend {
  month: string;
  match_count: number;
  mismatch_count: number;
}
