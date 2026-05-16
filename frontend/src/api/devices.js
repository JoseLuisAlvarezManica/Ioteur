import { mockDevices } from "../data/mockData";

export const devicesApi = {
  list: ()        => Promise.resolve([...mockDevices]),
  get:  (id)      => Promise.resolve(mockDevices.find((d) => d.id === id)),
  create: ({ name, macAddress }) => {
    const nuevo = { id: String(Date.now()), device_name: name, status: "active", last_seen: null, mac_address: macAddress };
    mockDevices.push(nuevo);
    return Promise.resolve(nuevo);
  },
  updateStatus: (id, status) => {
    const d = mockDevices.find((d) => d.id === id);
    if (d) d.status = status;
    return Promise.resolve(d);
  },
  delete: (id) => Promise.resolve({ ok: true }),
};