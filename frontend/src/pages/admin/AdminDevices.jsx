 import React, { useEffect, useState } from "react";
import AppLayout from "../../layouts/AppLayout";
import { devicesApi } from "../../api/devices";

const STATUS_STYLES = {
  active:   "bg-green-100 text-green-700",
  inactive: "bg-gray-100 text-gray-600",
  online:   "bg-blue-100 text-blue-700",
};

function AdminDevices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const data = await devicesApi.list();
        setDevices(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to fetch devices:", err);
        setError("No se pudieron cargar los dispositivos.");
      } finally {
        setLoading(false);
      }
    };
    fetchDevices();
  }, []);

  const handleToggleStatus = async (device) => {
    const next = device.status === "active" ? "inactive" : "active";
    try {
      await devicesApi.updateStatus(device.device_uuid, next);
      setDevices((prev) =>
        prev.map((d) =>
          d.device_uuid === device.device_uuid ? { ...d, status: next } : d
        )
      );
    } catch (err) {
      console.error("Failed to update status:", err);
      alert("No se pudo cambiar el estado del dispositivo.");
    }
  };

  return (
    <AppLayout>
      <div className="flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Manage Devices</h1>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 overflow-x-auto">
          {loading ? (
            <div className="p-4 text-center text-gray-500">Loading devices...</div>
          ) : error ? (
            <div className="p-4 text-center text-red-500">{error}</div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-gray-500 border-b border-gray-100">
                  <th className="pb-3 font-medium">Name</th>
                  <th className="pb-3 font-medium">MAC Address</th>
                  <th className="pb-3 font-medium">Owner (user_id)</th>
                  <th className="pb-3 font-medium">Group</th>
                  <th className="pb-3 font-medium">Interval (s)</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {devices.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="py-4 text-center text-gray-500">
                      No devices found.
                    </td>
                  </tr>
                ) : (
                  devices.map((device) => (
                    <tr key={device.device_uuid} className="border-b border-gray-50">
                      <td className="py-3 font-semibold">
                        <span title={device.device_uuid}>{device.device_name}</span>
                      </td>
                      <td className="py-3 font-mono text-gray-600">{device.mac_address}</td>
                      <td className="py-3 text-gray-500 truncate max-w-[120px]" title={device.user_id}>
                        {device.user_id || "N/A"}
                      </td>
                      <td className="py-3 text-gray-500">{device.group || "—"}</td>
                      <td className="py-3 text-gray-500">{device.report_interval ?? "—"}</td>
                      <td className="py-3">
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            STATUS_STYLES[device.status] ?? "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {device.status ?? "unknown"}
                        </span>
                      </td>
                      <td className="py-3">
                        <button
                          onClick={() => handleToggleStatus(device)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          {device.status === "active" ? "Deactivate" : "Activate"}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminDevices;
