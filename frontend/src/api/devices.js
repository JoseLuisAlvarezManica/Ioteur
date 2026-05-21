import { api } from "./client";

export const devicesApi = {
  list: () => api.get("/devices/"),
  getByUser: () => api.get(`/devices/me`),
  create: (data) =>
  api.post("/devices/register", {
    user_id: data.userId,
    device_name: data.name,
    mac_address: data.macAddress,
    report_interval: Number(data.reportInterval),
    icon: data.icon ?? "sensor",
    color: data.color ?? "#000000",
    group: data.group?.trim() || undefined,
  }),
  update: (data) =>
    api.put("/devices/update", {
      device_uuid: data.device_uuid,
      report_interval: data.report_interval ? Number(data.report_interval) : undefined,
      icon: data.icon,
      color: data.color,
      group: data.group,
      status: data.status,
    }),
  updateStatus: (id, status) => 
    api.put("/devices/update", {
      device_uuid: id,
      status: status
    }),
    // El endpoint real de delete no está expuesto en call.py, pero lo dejamos preparado
    delete: (id) => api.delete(`/devices/${id}`),
  };