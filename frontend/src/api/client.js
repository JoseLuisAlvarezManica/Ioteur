const BASE_URL = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:8000';

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

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
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
      // Another refresh already in progress — queue this request until it resolves
      if (isRefreshing) {
        try {
          const newToken = await new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });
          return request(
            path,
            { ...options, headers: { ...options.headers, Authorization: `Bearer ${newToken}` } },
            true
          );
        } catch {
          // Refresh failed while we were queued — fall through to logout
        }
      } else {
        isRefreshing = true;
        try {
          const refreshHeaders = {
            "Content-Type": "application/json",
            "x-refresh-token": refreshToken,
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          };

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
            isRefreshing = false;

            // Retry original request with new token (not via finally to avoid early flag reset)
            return request(
              path,
              { ...options, headers: { ...options.headers, Authorization: `Bearer ${newToken}` } },
              true
            );
          } else {
            // Refresh token rejected by server — drain queue then log out
            processQueue(new Error("Session expired"), null);
          }
        } catch (err) {
          // Network error during refresh — drain queue then log out
          processQueue(err, null);
        } finally {
          isRefreshing = false;
        }
      }
    }

    clearSession();
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