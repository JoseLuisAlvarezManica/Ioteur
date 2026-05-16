import { mockRecords, mockReports } from "../data/mockData";

export const recordsApi = {
  list: (deviceId) => Promise.resolve(mockRecords),
};

export const telemetryApi = {
  requestReport: (deviceId) => Promise.resolve({ ok: true }),
  getReport:     (deviceId) => Promise.resolve(mockReports),
};