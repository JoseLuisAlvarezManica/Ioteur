import { api } from "./client";

export const recordsApi = {
  list: (deviceId) => api.get(`/registers/${deviceId}`),
  listByDate: (deviceId, from, to) => api.get(`/registers/${deviceId}/by-date?from=${from}&to=${to}`),
};

export const telemetryApi = {
  requestReport: (deviceId) => api.post(`/reports/${deviceId}/generate`, {}),
  getReport:     (deviceId) => api.get(`/reports/${deviceId}`),
  getReportsByDate: (deviceId, from, to) => api.get(`/reports/${deviceId}/by-date?from=${from}&to=${to}`),
};