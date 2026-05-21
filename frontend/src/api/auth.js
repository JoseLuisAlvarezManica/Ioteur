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

  // Proactive refresh — called while the access token is still valid.
  // The Authorization header is added automatically by the api client.
  refresh: () => {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return Promise.reject(new Error("No refresh token"));
    return api.post("/auth/refresh", {}, {
      headers: { "x-refresh-token": refreshToken },
    });
  },

  logout: () => {
    const refreshToken = localStorage.getItem("refresh_token") || "";
    return api.post("/auth/logout", {}, {
      headers: { "x-refresh-token": refreshToken }
    });
  },

  me: () => api.get("/auth/me"),
};