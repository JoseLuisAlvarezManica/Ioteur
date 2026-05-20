import { mockNotifications } from "../data/mockData";

export const notificationsApi = {
  list: ()      => Promise.resolve([...mockNotifications]),
  markRead: (id) => {
    const n = mockNotifications.find((n) => n.id === id);
    if (n) n.read = true;
    return Promise.resolve(n);
  },
  markAllRead: () => {
    mockNotifications.forEach((n) => (n.read = true));
    return Promise.resolve({ ok: true });
  },
};