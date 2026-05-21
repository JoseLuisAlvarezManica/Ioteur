import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useAuth } from "./AuthContext";
import { devicesApi } from "../api/devices";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const { user } = useAuth();
  const [devices, setDevices] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loadingDevices, setLoadingDevices] = useState(false);
  const [errorDevices, setErrorDevices] = useState(null);

  const fetchDevices = useCallback(async (opts = { silent: false }) => {
    if (!user?.id) {
      setDevices([]);
      setGroups([]);
      return;
    }
    if (!opts.silent) setLoadingDevices(true);
    try {
      const data = await devicesApi.getByUser();
      setDevices(data);

      const uniqueGroups = [...new Set(data.map((d) => d.group).filter(Boolean))];
      setGroups(uniqueGroups);

      setErrorDevices(null);
    } catch (err) {
      setErrorDevices(err.message);
    } finally {
      if (!opts.silent) setLoadingDevices(false);
    }
  }, [user, setDevices, setGroups, setLoadingDevices, setErrorDevices]);

  // Cargamos los dispositivos cuando el usuario está disponible
  useEffect(() => {
    if (user?.id) {
      fetchDevices();
      
    }
  }, [user?.id, fetchDevices, setDevices, setGroups, setLoadingDevices, setErrorDevices]);

  // Poll devices periodically (silent) so UI updates when device.status changes elsewhere
  useEffect(() => {
    if (!user?.id) return;

    const POLL_INTERVAL = Number(import.meta.env.VITE_DEVICES_POLL_INTERVAL_MS) || 5000;
    let mounted = true;

    const tick = async () => {
      if (!mounted) return;
      try {
        // silent: don't toggle loading UI during background refresh
        await fetchDevices({ silent: true });
      } catch (e) {
        // ignore background errors
      }
    };

    const id = setInterval(tick, POLL_INTERVAL);
    // run one immediate silent tick after mount
    tick();

    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [user?.id, fetchDevices]);

  // Función global para refrescar todo
  const globalRefresh = useCallback(async () => {
    await fetchDevices();
    // Más adelante aquí se pueden agregar más cosas para refrescar (ej: notificaciones)
  }, [fetchDevices, setDevices, setGroups, setLoadingDevices, setErrorDevices]);

  return (
    <AppContext.Provider value={{ devices, setDevices, groups, setGroups, loadingDevices, errorDevices, globalRefresh, fetchDevices }}>
      {children}
    </AppContext.Provider>
  );
}

export const useAppContext = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext debe usarse dentro de <AppProvider>");
  return ctx;
}