const BASE_URL = "/api";

let isRefreshing = false;
let failedQueue = [];

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

async function request(path, options = {}, isRetry = false) {
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

  if (res.status === 401 && !isRetry) {
    const refreshToken = localStorage.getItem("refresh_token");

    if (refreshToken) {
      if (isRefreshing) {
        try {
          const newToken = await new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });
          options.headers = options.headers || {};
          options.headers.Authorization = `Bearer ${newToken}`;
          return request(path, options, true);
        } catch (err) {
          return Promise.reject(err);
        }
      }

      isRefreshing = true;

      try {
        const refreshHeaders = {
          "Content-Type": "application/json",
          "x-refresh-token": refreshToken
        };
        
        if (token) {
           refreshHeaders.Authorization = `Bearer ${token}`; // Mantenemos el bearer actual
        }

        const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: refreshHeaders,
        });

        if (refreshRes.ok) {
          const data = await refreshRes.json();
          const newToken = data.access_token || data.token;
          const newRefreshToken = data.refresh_token;
          
          localStorage.setItem("token", newToken);
          if (newRefreshToken) {
             localStorage.setItem("refresh_token", newRefreshToken);
          }

          processQueue(null, newToken);

          options.headers = options.headers || {};
          options.headers.Authorization = `Bearer ${newToken}`;
          return request(path, options, true);
        }
      } catch (err) {
        // Ignoramos el catch para pasar a limpiar el user abajo
      } finally {
        isRefreshing = false;
      }
    }

    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
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
  put:    (path, body, opts = {}) => request(path, { method: "PUT", body: JSON.stringify(body), ...opts }),
  patch:  (path, body, opts = {}) => request(path, { method: "PATCH", body: JSON.stringify(body), ...opts }),
  delete: (path, opts = {}) => request(path, { method: "DELETE", ...opts }),
};