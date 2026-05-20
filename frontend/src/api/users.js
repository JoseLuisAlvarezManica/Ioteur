import { api } from "./client";

export const usersApi = {
  list: () => api.get("/auth/users/"),
  update: (id, data) => api.put(`/auth/user/${id}`, data),
  delete: (id) => api.delete(`/auth/user/${id}`),
};
