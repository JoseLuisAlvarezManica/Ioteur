import { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";
import { authApi } from "../api/auth";

function decodeJwtPayload(token) {
  if (!token) {
    return null;
  }

  const parts = token.split(".");
  if (parts.length < 2) {
    return null;
  }

  try {
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

function buildUserFromSession(me, token) {
  if (!me) {
    return null;
  }

  const payload = decodeJwtPayload(token);

  return {
    id: me.id || payload?.sub || null,
    name: me.name,
    email: me.email,
    role: me.role,
  };
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      return null;
    }

    try {
      return JSON.parse(localStorage.getItem("user")) || null;
    } catch {
      return null;
    }
  });

  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const refreshTimerRef       = useRef(null);

  // Schedule a proactive token refresh 60 s before the JWT expires.
  // This prevents the access token from being expired when the refresh
  // endpoint is called (which itself requires a valid token via @must_be_logged_in).
  const scheduleTokenRefresh = useCallback(() => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);

    const token = localStorage.getItem("token");
    if (!token) return;

    const payload = decodeJwtPayload(token);
    if (!payload?.exp) return;

    const msUntilExpiry = payload.exp * 1000 - Date.now();
    const delay = msUntilExpiry - 60_000; // refresh 60 s early
    if (delay <= 0) return; // already expired or too close — let 401 handler deal with it

    refreshTimerRef.current = setTimeout(async () => {
      try {
        const data = await authApi.refresh();
        const newToken = data.access_token || data.token;
        localStorage.setItem("token", newToken);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }
        scheduleTokenRefresh(); // arm next cycle
      } catch {
        // Proactive refresh failed silently; the 401 handler in client.js
        // will attempt one final refresh when the next request fires.
      }
    }, delay);
  }, []);

  // Arm / disarm the timer whenever the user session changes.
  useEffect(() => {
    if (user) {
      scheduleTokenRefresh();
    } else {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    }
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, [user, scheduleTokenRefresh]);

  const syncUser = useCallback(async () => {
    const me = await authApi.me();
    const token = localStorage.getItem("token");
    const userInfo = buildUserFromSession(me, token);

    if (!userInfo?.email) {
      throw new Error("No se pudo cargar la sesión");
    }

    localStorage.setItem("user", JSON.stringify(userInfo));
    setUser(userInfo);
    return userInfo;
  }, []);

  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const data = await authApi.login(email, password);
      const token = data.access_token || data.token;

      localStorage.setItem("token", token);
      if (data.refresh_token) {
        localStorage.setItem("refresh_token", data.refresh_token);
      }

      const userInfo = await syncUser();
      localStorage.setItem("user", JSON.stringify(userInfo));
      return userInfo;
    } catch (err) {
      clearSession();
      setUser(null);
      setError(err.message || "Error al iniciar sesión");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [syncUser]);

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      clearSession();
      setUser(null);
      return;
    }

    syncUser().catch(() => {
      clearSession();
      setUser(null);
    });
  }, [syncUser]);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
    } finally {
      clearSession();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}