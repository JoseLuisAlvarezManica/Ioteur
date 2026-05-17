import { api } from "./client";

export const authApi = {
  register: (data) =>
    api.post("/auth/signup", {
      name: data.name,
      email: data.email,
      password: data.password,
    }),

  login: (email, password) =>
    api.post("/auth/login", { email, password }),

  logout: () => {
    const refreshToken = localStorage.getItem("refresh_token") || "";
    return api.post("/auth/logout", {}, {
      headers: { "x-refresh-token": refreshToken }
    });
  },

  me: () => api.get("/auth/me"),
};