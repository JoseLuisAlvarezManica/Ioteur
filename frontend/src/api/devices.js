import { api } from "./client";

export const devicesApi = {
  list: () => api.get("/devices/"),
  getByUser: (userId) => api.get(`/devices/${userId}`),
  create: ({ name, macAddress }) => 
    api.post("/devices/register", { 
      name, 
      mac_address: macAddress 
    }),
  updateStatus: (id, status) => 
    api.patch("/devices/update", {
      device_id: id,
      status: status
    }),
  // El endpoint real de delete no está expuesto en call.py, pero lo dejamos preparado
  delete: (id) => api.delete(`/devices/${id}`),
};