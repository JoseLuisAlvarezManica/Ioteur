import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useAuth } from "./AuthContext";
import { devicesApi } from "../api/devices";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const { user } = useAuth();
  const [devices, setDevices] = useState([]);
  const [loadingDevices, setLoadingDevices] = useState(false);
  const [errorDevices, setErrorDevices] = useState(null);

  const fetchDevices = useCallback(async () => {
    if (!user?.id) {
      setDevices([]);
      return;
    }
    setLoadingDevices(true);
    try {
      const data = await devicesApi.getByUser(user.id);
      setDevices(data);
      setErrorDevices(null);
    } catch (err) {
      setErrorDevices(err.message);
    } finally {
      setLoadingDevices(false);
    }
  }, [user]);

  // Cargamos los dispositivos cuando el usuario está disponible, pero no cada vez que se cambia de pantalla
  useEffect(() => {
    if (user?.id && devices.length === 0) {
      fetchDevices();
    }
  }, [user, fetchDevices]); // devices.length is omitted intentinally to fetch only on mount or user change

  // Función global para refrescar todo
  const globalRefresh = useCallback(async () => {
    await fetchDevices();
    // Más adelante aquí se pueden agregar más cosas para refrescar (ej: notificaciones)
  }, [fetchDevices]);

  return (
    <AppContext.Provider value={{ devices, setDevices, loadingDevices, errorDevices, globalRefresh, fetchDevices }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext debe usarse dentro de <AppProvider>");
  return ctx;
}