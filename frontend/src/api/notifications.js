import { api } from "./client";

export const notificationsApi = {
  // Returns a list of EmailNotification objects for the logged-in user.
  // Fields: id, device_id, user_id, email, reason, severity, message, status, created_at
  list: (limit = 100, skip = 0) =>
    api.get(`/notifications/me?limit=${limit}&skip=${skip}`),
};