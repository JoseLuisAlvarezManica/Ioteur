const BASE_URL = "/api";

async function request(path, options = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/";
    return;
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data?.detail || data?.message || "Error en la solicitud");
  }

  return data;
}

export const api = {
  get:    (path, opts = {}) => request(path, { method: "GET", ...opts }),
  post:   (path, body, opts = {}) => request(path, { method: "POST", body: JSON.stringify(body), ...opts }),
  patch:  (path, body, opts = {}) => request(path, { method: "PATCH", body: JSON.stringify(body), ...opts }),
  delete: (path, opts = {}) => request(path, { method: "DELETE", ...opts }),
};