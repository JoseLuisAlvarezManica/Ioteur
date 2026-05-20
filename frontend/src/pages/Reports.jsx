import { useState, useEffect } from "react";
import AppLayout from "../layouts/AppLayout";
import { devicesApi } from "../api/devices";
import { telemetryApi } from "../api/telemetry";
import { UserBar } from "./Dashboard";
import { useAuth } from "../context/AuthContext";

function ReportCard({ report }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-base font-bold text-gray-900">
            {report.device_name || "Device"}
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">
            Generated: {new Date(report.created_at).toLocaleString()}
          </p>
        </div>
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full border border-gray-200">
          {report.metric || "Telemetry"}
        </span>
      </div>

      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-3 mt-4">
        {[
          { label: "Min", value: report.min ?? "—" },
          { label: "Max", value: report.max ?? "—" },
          { label: "Avg", value: report.avg != null
              ? Number(report.avg).toFixed(2)
              : "—"
          },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-50 rounded-xl p-3 text-center border border-gray-100">
            <p className="text-xs text-gray-400 mb-1">{label}</p>
            <p className="text-base font-bold text-gray-900">
              {value} {report.unit || ""}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

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
        if (devs.length > 0) setSelected(devs[0].id);
      })
      .catch((err) => setError(err.message));
  }, [user]);

  // Cargar reportes cuando cambia el dispositivo seleccionado
  useEffect(() => {
    if (!selectedDevice) return;
    setLoadingR(true);
    setReports([]);
    telemetryApi.getReport(selectedDevice)
      .then((data) => setReports(Array.isArray(data) ? data : [data]))
      .catch(() => setReports([]))
      .finally(() => setLoadingR(false));
  }, [selectedDevice]);

  const handleRequestReport = async () => {
    if (!selectedDevice) return;
    setRequesting(true);
    setMsg(null);
    try {
      await telemetryApi.requestReport(selectedDevice);
      setMsg("✓ Report requested. It will appear here once processed.");
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setRequesting(false);
    }
  };

  return (
    <AppLayout pageTitle="Reports">
      <UserBar />

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Reports</h2>
      </div>

      {error && <p className="text-sm text-red-500 mb-4">{error}</p>}

      {/* Device selector + request button */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5 mb-6 flex items-end gap-4">
        <div className="flex flex-col gap-1 flex-1">
          <label className="text-sm font-medium text-gray-700">Select device</label>
          <select
            value={selectedDevice}
            onChange={(e) => setSelected(e.target.value)}
            className="border border-gray-300 rounded-xl px-4 py-2.5 text-sm outline-none bg-white"
          >
            {devices.map((d) => (
              <option key={d.id} value={d.id}>
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
          {requesting ? "Requesting..." : "Request Report"}
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
        <p className="text-sm text-gray-400">Loading reports...</p>
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
          <p className="text-sm">No reports yet for this device.</p>
          <p className="text-xs mt-1">Request one using the button above.</p>
        </div>
      )}

      {/* Lista de reportes */}
      {!loadingReports && reports.length > 0 && (
        <div className="flex flex-col gap-4">
          {reports.map((r, i) => (
            <ReportCard key={r.id ?? i} report={r} />
          ))}
        </div>
      )}
    </AppLayout>
  );
}

export default Reports;