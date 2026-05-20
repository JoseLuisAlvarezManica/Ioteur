import { useState, useEffect } from "react";
import AppLayout from "../layouts/AppLayout";
import { devicesApi } from "../api/devices";
import { telemetryApi } from "../api/telemetry";
import { UserBar } from "./Dashboard";
import { useAuth } from "../context/AuthContext";
import ReportCard from "../components/ReportCharts";

function Reports() {
  const { user } = useAuth();
  const [devices, setDevices]         = useState([]);
  const [selectedDevice, setSelected] = useState("");
  const [reports, setReports]         = useState([]);
  const [loadingReports, setLoadingR] = useState(false);
  const [requesting, setRequesting]   = useState(false);
  const [msg, setMsg]                 = useState(null);
  const [error, setError]             = useState(null);

  // Cargar dispositivos al montar
  useEffect(() => {
    if (!user?.id) return;
    
    devicesApi.getByUser(user.id)
      .then((devs) => {
        setDevices(devs);
        if (devs.length > 0) setSelected(devs[0].device_uuid);
      })
      .catch((err) => setError(err.message));
  }, [user]);

  // Cargar reportes cuando cambia el dispositivo seleccionado
  useEffect(() => {
    if (!selectedDevice) return;
    setLoadingR(true);
    setReports([]);
    telemetryApi.getReport(selectedDevice)
      .then((data) => 
        {setReports(Array.isArray(data) ? data : [data])
          console.log("Reportes cargados:", data);
        })
      .catch(() => setReports([]))
      .finally(() => setLoadingR(false));
  }, [selectedDevice]);

  const handleRequestReport = async () => {
    if (!selectedDevice) return;
    setRequesting(true);
    setMsg(null);
    try {
      await telemetryApi.requestReport(selectedDevice);
      setMsg("✓ Reporte solicitado. Aparecerá aquí una vez procesado.");
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setRequesting(false);
    }
  };

  return (
    <AppLayout pageTitle="Reportes">
      <UserBar />

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Reportes</h2>
      </div>

      {error && <p className="text-sm text-red-500 mb-4">{error}</p>}

      {/* Device selector + request button */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5 mb-6 flex items-end gap-4">
        <div className="flex flex-col gap-1 flex-1">
          <label className="text-sm font-medium text-gray-700">Seleccionar dispositivo</label>
          <select
            value={selectedDevice}
            onChange={(e) => setSelected(e.target.value)}
            className="border border-gray-300 rounded-xl px-4 py-2.5 text-sm outline-none bg-white"
          >
            {devices.map((d) => (
              <option key={d.device_uuid} value={d.device_uuid}>
                {d.device_name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleRequestReport}
          disabled={requesting || !selectedDevice}
          className="px-5 py-2.5 rounded-xl border border-gray-400 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60 flex-shrink-0"
        >
          {requesting ? "Solicitando..." : "Solicitar Reporte"}
        </button>
      </div>

      {/* Feedback */}
      {msg && (
        <div className={`text-sm px-4 py-2 rounded-xl mb-4 ${
          msg.startsWith("Error")
            ? "bg-red-50 text-red-600"
            : "bg-green-50 text-green-700"
        }`}>
          {msg}
        </div>
      )}

      {loadingReports && (
        <p className="text-sm text-gray-400">Cargando reportes...</p>
      )}

      {/* Estado vacío */}
      {!loadingReports && reports.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mb-3">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <line x1="8" y1="12" x2="8" y2="16"/>
            <line x1="12" y1="8" x2="12" y2="16"/>
            <line x1="16" y1="10" x2="16" y2="16"/>
          </svg>
          <p className="text-sm">No hay reportes aún para este dispositivo.</p>
          <p className="text-xs mt-1">Solicita uno usando el botón de arriba.</p>
        </div>
      )}

      {/* Lista de reportes */}
      {!loadingReports && reports.length > 0 && (
        <div className="flex flex-col gap-4">
          <ReportCard reports={reports} />
        </div>
      )}
    </AppLayout>
  );
}

export default Reports;