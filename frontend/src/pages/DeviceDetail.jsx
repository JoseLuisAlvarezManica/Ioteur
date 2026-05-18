import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AppLayout from "../layouts/AppLayout";
import { devicesApi } from "../api/devices";
import { recordsApi, telemetryApi } from "../api/telemetry";
import { UserBar, FilterBar } from "./Dashboard";
import { useAppContext } from "../context/AppContext";

function DeviceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { devices, loadingDevices, fetchDevices } = useAppContext();

  const [device, setDevice]       = useState(null);
  const [records, setRecords]     = useState([]);
  const [loadingRecords, setLoadingRecords] = useState(true);
  // Extraemos el load de reportMsg y errors más abajo
  const [error, setError]         = useState(null);
  const [reportMsg, setReportMsg] = useState(null);
  const [deleting, setDeleting]   = useState(false);
  const [filter, setFilter]       = useState("all");

  useEffect(() => {
    // Si todavía no hay dispositivos, los refrescamos (por si el usuario entró directo a la url)
    if (devices.length === 0 && !loadingDevices) {
       fetchDevices();
    }
  }, [devices.length, loadingDevices, fetchDevices]);

  useEffect(() => {
    const found = devices.find(d => d.device_uuid === id);
    if (found) {
      setDevice(found);
    }
  }, [devices, id]);

  useEffect(() => {
    if (id) {
      setLoadingRecords(true);
      recordsApi.list(id)
        .then((recs) => setRecords(recs))
        .catch((err) => setError(err.message))
        .finally(() => setLoadingRecords(false));
    }
  }, [id]);

  const handleRequestReport = async () => {
    setReportMsg(null);
    try {
      await telemetryApi.requestReport(id);
      setReportMsg("✓ Report requested. You'll receive an email when it's ready.");
    } catch (err) {
      setReportMsg(`Error: ${err.message}`);
    }
  };

  const handleDelete = async () => {
    if (!confirm("¿Seguro que deseas eliminar este dispositivo?")) return;
    setDeleting(true);
    try {
      await devicesApi.delete(id);
      navigate("/dashboard");
    } catch (err) {
      alert(err.message);
      setDeleting(false);
    }
  };

  const handleToggleStatus = async () => {
    const newStatus = device.status === "active" ? "inactive" : "active";
    try {
      const updated = await devicesApi.updateStatus(id, newStatus);
      // Puesto que usamos AppContext, deberíamos recargarlo... 
      // pero por ahora actualizamos visualmente copiando o llamando a fetchDevices:
      fetchDevices();
      setDevice(prev => ({ ...prev, status: newStatus }));
    } catch (err) {
      alert(err.message);
    }
  };

  if (loadingDevices || loadingRecords) {
    return (
      <AppLayout pageTitle="Dispositivos">
        <p className="text-gray-400 text-sm">Loading...</p>
      </AppLayout>
    );
  }

  if (error || !device) {
    return (
      <AppLayout pageTitle="Dispositivos">
        <p className="text-red-500 text-sm">{error || "Device not found."}</p>
      </AppLayout>
    );
  }

  const isActive = device.status === "active";

  return (
    <AppLayout pageTitle={`Dispositivos (${device.device_name})`}>
      <UserBar />
      <FilterBar filter={filter} setFilter={setFilter} />

      {/* Device info card */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-4">
        <h2 className="text-xl font-bold text-gray-900 mb-1">Dispositivos</h2>
        <p className="text-base font-semibold text-gray-800 mb-4">
          {device.device_name}
        </p>

        <div className="flex gap-6">
          {/* Image placeholder */}
          <div className="w-52 h-44 bg-gray-200 rounded-xl flex-shrink-0 flex items-center justify-center">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="1.5">
              <rect x="2" y="3" width="20" height="14" rx="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
          </div>

          {/* Info */}
          <ul className="flex flex-col justify-center gap-3 text-sm text-gray-800">
            <li><span className="font-bold">Name:</span> {device.device_name}</li>
            <li><span className="font-bold">MAC Address:</span> {device.mac_address}</li>
            <li><span className="font-bold">UUID:</span> {device.device_uuid}</li>
            <li>
              <span className="font-bold">Last seen:</span>{" "}
              {device.last_seen
                ? new Date(device.last_seen).toLocaleString()
                : "Never"}
            </li>
            <li className="flex items-center gap-2">
              <span className="font-bold">Status:</span>
              <span>{isActive ? "Active" : "Inactive"}</span>
              <span className={`w-3 h-3 rounded-full ${
                isActive ? "bg-green-500" : "bg-red-500"
              }`} />
              <button
                onClick={handleToggleStatus}
                className="ml-2 text-xs text-gray-500 underline hover:text-gray-700"
              >
                {isActive ? "Deactivate" : "Activate"}
              </button>
            </li>
          </ul>
        </div>
      </div>

      {/* Recent Data */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-4">
        <h3 className="text-base font-bold text-gray-900 mb-3">Recent Data</h3>
        {records.length === 0 ? (
          <p className="text-sm text-gray-400">No records yet.</p>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="border border-gray-300 px-4 py-2 text-center font-semibold text-gray-800">
                  Timestamp
                </th>
                <th className="border border-gray-300 px-4 py-2 text-center font-semibold text-gray-800">
                  Payload
                </th>
              </tr>
            </thead>
            <tbody>
              {records.map((row, i) => (
                <tr key={i}>
                  <td className="border border-gray-200 px-4 py-2 text-gray-600">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                  <td className="border border-gray-200 px-4 py-2 text-gray-600 font-mono text-xs">
                    {typeof row.values === "object"
                      ? JSON.stringify(row.values)
                      : row.values}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Report feedback */}
      {reportMsg && (
        <div className={`text-sm px-4 py-2 rounded-xl mb-4 ${
          reportMsg.startsWith("Error")
            ? "bg-red-50 text-red-600"
            : "bg-green-50 text-green-700"
        }`}>
          {reportMsg}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleRequestReport}
          className="px-5 py-2 rounded-full border border-gray-400 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Request Report
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="px-5 py-2 rounded-full bg-red-500 text-white text-sm font-semibold hover:bg-red-600 disabled:opacity-60"
        >
          {deleting ? "Deleting..." : "Delete Device"}
        </button>
      </div>
    </AppLayout>
  );
}

export default DeviceDetail;