import { api } from "./client";

export const usersApi = {
  // Returns UsersPageResponse: { total, page, page_size, total_pages, users: [{id,name,email,role}] }
  list: (page = 1, pageSize = 10) =>
    api.get(`/auth/user/?page=${page}&page_size=${pageSize}`),
  update: (id, data) => api.put(`/auth/user/${id}`, data),
  delete: (id) => api.delete(`/auth/user/${id}`),
};
