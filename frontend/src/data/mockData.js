export const mockDevices = [
  { id: "1", device_name: "Sensor Temp",    status: "active",   last_seen: new Date().toISOString(),                    mac_address: "AA:BB:CC:DD:EE:FF" },
  { id: "2", device_name: "Sensor CO2",     status: "inactive", last_seen: "2026-05-15T10:00:00Z",                      mac_address: "11:22:33:44:55:66" },
  { id: "3", device_name: "Sensor Humedad", status: "active",   last_seen: new Date(Date.now() - 60000).toISOString(),  mac_address: "AA:11:BB:22:CC:33" },
];

export const mockRecords = [
  { created_at: "2026-05-16T09:00:01Z", values: { temp: 22.3 } },
  { created_at: "2026-05-16T08:55:12Z", values: { temp: 21.8 } },
  { created_at: "2026-05-16T08:50:43Z", values: { temp: 22.1 } },
];

export const mockNotifications = [
  { id: "1", severity: "critical", reason: "Device disconnected", message: "Sensor Temp no ha enviado datos en 10 min.", read: false, created_at: "2026-05-16T09:10:00Z" },
  { id: "2", severity: "warning",  reason: "High temperature",    message: "Sensor Temp superó el umbral de 30°C.",      read: false, created_at: "2026-05-16T08:30:00Z" },
  { id: "3", severity: "info",     reason: "Device registered",   message: "Sensor CO2 fue registrado exitosamente.",    read: true,  created_at: "2026-05-15T10:00:00Z" },
];

export const mockReports = [
  { id: "1", device_name: "Sensor Temp", metric: "temperature", unit: "°C", min: 20.1, max: 24.5, avg: 22.1, created_at: "2026-05-16T09:00:00Z" },
];