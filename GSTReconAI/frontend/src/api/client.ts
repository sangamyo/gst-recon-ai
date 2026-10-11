import axios, { InternalAxiosRequestConfig } from "axios";

// Set VITE_API_URL at build time (e.g. in Vercel project settings). Trailing slashes are ignored.
const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1").replace(/\/+$/, "");

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false,
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("gst_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
