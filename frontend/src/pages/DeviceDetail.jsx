import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AppLayout from "../layouts/AppLayout";
import { devicesApi } from "../api/devices";
import { waitForDeviceAbsent, waitForDevicePresent } from "../utils/poll";
import { recordsApi, telemetryApi } from "../api/telemetry";
import { UserBar, FilterBar } from "./Dashboard";
import { useAppContext } from "../context/AppContext";

function DeviceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { devices, loadingDevices, fetchDevices, globalRefresh } = useAppContext();

  const [device, setDevice]       = useState(null);
  const [records, setRecords]     = useState([]);
  const [loadingRecords, setLoadingRecords] = useState(true);
  // Extraemos el load de reportMsg y errors más abajo
  const [error, setError]         = useState(null);
  const [reportMsg, setReportMsg] = useState(null);
  const [deleting, setDeleting]   = useState(false);
  const [filter, setFilter]       = useState("all");
  const [showEditModal, setShowEditModal] = useState(false);

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

      // Espera corta hasta que el device deje de existir upstream
      await waitForDeviceAbsent(id, { interval: 100, maxAttempts: 6 });

      await globalRefresh();
      navigate("/dashboard");
    } catch (err) {
      alert(err.message);
      setDeleting(false);
    }
  };

  const handleToggleStatus = async () => {
    const newStatus = device.status === "active" ? "inactive" : "active";
    try {
      await devicesApi.updateStatus(id, newStatus);
      await globalRefresh();
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

      {/* Device info card */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-4">
        <h2 className="text-xl font-bold text-purple-900 mb-5 bg-gray-100 p-2 pl-6 rounded-lg">Vista Detallada de Dispositivos</h2>
        

        <div className="flex justify-between items-center mx-4">
          <div className="flex gap-6 items-center">
            {/* Icon */}
            <div
                className="w-14 h-14"
                style={{
                  backgroundColor: device?.color ?? "#d60404",
                  WebkitMaskImage: `url(/${device?.icon ?? "casa"}.svg)`,
                  WebkitMaskSize: "contain",
                  WebkitMaskRepeat: "no-repeat",
                  WebkitMaskPosition: "center",
                  maskImage: `url(/${device?.icon ?? "casa"}.svg)`,
                  maskSize: "contain",
                  maskRepeat: "no-repeat",
                  maskPosition: "center",
                }}
              />

            {/* Info */}
            <ul className="flex flex-col justify-center gap-3 text-sm text-gray-800">
              <li><span className="font-bold">Nombre:</span> {device.device_name}</li>
              <li><span className="font-bold">Dirección MAC:</span> {device.mac_address}</li>
              <li><span className="font-bold">UUID:</span> {device.device_uuid}</li>
              <li>
                <span className="font-bold">Última vez visto:</span>{" "}
                {device.last_seen
                  ? new Date(device.last_seen).toLocaleString()
                  : "Nunca visto"}
              </li>
              <li><span className="font-bold">Grupo:</span> {device.group}</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="flex flex-col items-end gap-3 text-sm text-gray-800 border-l border-gray-200 pl-6">
            <div className="flex items-center gap-2">
              <span className="font-bold">Estado:</span>
              <span className={isActive ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
                {isActive ? "Active" : "Inactive"}
              </span>
              <span className={`w-3 h-3 rounded-full ${
                isActive ? "bg-green-500" : "bg-red-500"
              }`} />
            </div>
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={handleToggleStatus}
                className="px-3 py-1.5 rounded border border-gray-300 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
              >
                {isActive ? "Desactivar" : "Activar"}
              </button>
              <button
                onClick={() => setShowEditModal(true)}
                className="px-3 py-1.5 rounded bg-purple-50 text-purple-700 hover:bg-purple-100 text-xs font-medium transition-colors border border-purple-100"
              >
                Editar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Data */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-4">
        <h3 className="text-base font-bold text-gray-900 mb-3">Ultimas Mediciones</h3>
        {records.length === 0 ? (
          <div className="bg-gray-50 rounded-xl p-6 text-sm text-gray-600 font-mono">
            <p className="mb-2 text-gray-500 font-sans font-medium">Envía un registro con este formato a la siguiente ruta <span className="font-bold text-purple-700 bg-purple-100 mx-4 px-2 py-0.5 rounded">POST {window.location.origin}/api/registers/received</span>: </p>
            <pre className="bg-gray-800 text-green-400 p-4 rounded-lg overflow-x-auto">
              {`{  
      "device_id": "${device.device_uuid}",
      "time_procesing": 12,
      "values": {
                  "temperatura": 24.5,
                  "humedad": 60
      }
 }`}
            </pre>
          </div>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="border border-gray-300 px-4 py-2 text-center font-semibold text-gray-800">
                  Hora
                </th>
                <th className="border border-gray-300 px-4 py-2 text-center font-semibold text-gray-800">
                  Contenido
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
          Solicitar Reporte
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="px-5 py-2 rounded-full bg-red-500 text-white text-sm font-semibold hover:bg-red-600 disabled:opacity-60"
        >
          {deleting ? "Eliminando..." : "Eliminar Dispositivo"}
        </button>
      </div>

      {showEditModal && (
        <EditDeviceModal
          device={device}
          onClose={() => setShowEditModal(false)}
          onUpdated={() => {
            setShowEditModal(false);
            globalRefresh();
          }}
        />
      )}
    </AppLayout>
  );
}

export default DeviceDetail;
function EditDeviceModal({ device, onClose, onUpdated }) {
  const { groups } = useAppContext();
  const [group, setGroup] = useState(device.group || "");
  const [interval, setInterval] = useState(device.report_interval || "60");
  const [color, setColor] = useState(device.color || "#6B7280");
  const [icon, setIcon] = useState(device.icon || "sensor");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const colors = ["#6B7280", "#EF4444", "#F59E0B", "#10B981", "#3B82F6", "#9f1cd3"];
  const icons = ["radar", "sensor", "vehículo", "casa", "micro", "rasp"];

  const handleSubmit = async () => {
    if (!interval) {
      setError("El intervalo es requerido.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await devicesApi.update({
        device_uuid: device.device_uuid,
        report_interval: interval,
        color,
        icon,
        group,
      });

      // Espera a que la actualización se refleje upstream
      await waitForDevicePresent(device.device_uuid, { interval: 500, maxAttempts: 6 });

      onUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-xl">
        <h2 className="text-xl font-bold text-gray-900 mb-5">Editar Dispositivo</h2>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 text-sm px-3 py-2 rounded-xl mb-4">
            {error}
          </div>
        )}
      
        <div className="flex flex-col gap-4 mb-6">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Grupo</label>
            <input
              list="edit-groups-list"
              value={group}
              onChange={(e) => setGroup(e.target.value)}
              className="border border-gray-300 rounded-xl px-4 py-3 text-sm focus:border-purple-400 focus:ring-1 focus:ring-purple-100 transition-colors"
              placeholder="Asignar a un grupo"
            />
            <datalist id="edit-groups-list">
              {groups.map((g) => (
                <option key={g} value={g} />
              ))}
            </datalist>
            <p className="text-xs text-purple-600 font-medium ml-1 mt-0.5">
              Doble click para seleccionar un grupo existente o escribe uno nuevo.
            </p>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Intervalo de reporte (segundos)</label>
            <input
              type="number"
              min="1"
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              className="border border-gray-300 rounded-xl px-4 py-3 text-sm focus:border-purple-400 focus:ring-1 focus:ring-purple-100 transition-colors"
            />
            <p className="text-xs text-purple-600 font-medium ml-1 mt-0.5">
              Esto nos ayudará a saber si el dispositivo tiene problemas.
            </p>
          </div>

          <div className="mt-2">
            <label className="text-sm font-medium text-gray-700 mb-2 block">Icono</label>
            <div className="grid grid-cols-4 gap-2">
              {icons.map((i) => (
                <button
                  key={i}
                  onClick={() => setIcon(i)}
                  className={`flex items-center justify-center p-2 rounded-xl border ${
                    icon === i ? "border-purple-700 border-2 bg-gray-100" : "border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <img src={`/${i}.svg`} className="w-5 h-5" style={{ filter: `drop-shadow(0 0 0 ${color})` }} />
                </button>
              ))}
            </div>
          </div>

          <div className="mt-2">
            <label className="text-sm font-medium text-gray-700 mb-2 block">Color</label>
            <div className="flex gap-2">
              {colors.map((c) => (
                <button
                  key={c}
                  onClick={() => setColor(c)}
                  className={`w-8 h-8 rounded-full border-4 ${
                    color === c ? "border-purple-700" : "border-transparent"
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-3 justify-end mt-auto">
          <button onClick={onClose} className="px-5 py-2 rounded-xl border border-gray-300 text-sm">
            Cancelar
          </button>
          <button onClick={handleSubmit} disabled={loading} className="px-5 py-2 rounded-xl bg-purple-700 text-white text-sm">
            {loading ? "Guardando..." : "Guardar"}
          </button>
        </div>
      </div>
    </div>
  );
}

