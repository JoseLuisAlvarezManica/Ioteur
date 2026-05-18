import { api } from "./client";

export const devicesApi = {
  list: () => api.get("/devices/"),
  getByUser: (userId) => api.get(`/devices/${userId}`),
  create: ({ userId, name, macAddress, reportInterval }) => 
    api.post("/devices/register", {
      user_id: userId,
      device_name: name, 
      mac_address: macAddress,
      report_interval: parseInt(reportInterval, 10)
    }),
  updateStatus: (id, status) => 
    api.patch("/devices/update", {
      device_id: id,
      status: status
    }),
  // El endpoint real de delete no está expuesto en call.py, pero lo dejamos preparado
  delete: (id) => api.delete(`/devices/${id}`),
};