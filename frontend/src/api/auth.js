import { api } from "./client";

export const authApi = {
  register: (data) =>
    api.post("/auth/register", {
      name: data.name,
      email: data.email,
      password: data.password,
    }),

  login: (email, password) =>
    api.post("/auth/login", { email, password }),

  logout: () =>
    api.post("/auth/logout", {}),
};