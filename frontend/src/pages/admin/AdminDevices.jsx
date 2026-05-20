import React, { useEffect, useState } from "react";
import AppLayout from "../../layouts/AppLayout";
import { devicesApi } from "../../api/devices";

function AdminDevices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const data = await devicesApi.list();
        setDevices(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error("Failed to fetch devices:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchDevices();
  }, []);

  return (
    <AppLayout>
      <div className="flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Manage Devices</h1>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700">Add Device</button>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 overflow-hidden">
          {loading ? (
            <div className="p-4 text-center text-gray-500">Loading devices...</div>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="text-gray-500 border-b border-gray-100">
                  <th className="pb-3 font-medium">Name</th>
                  <th className="pb-3 font-medium">Type</th>
                  <th className="pb-3 font-medium">Owner</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {devices.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-4 text-center text-gray-500">No devices found.</td>
                  </tr>
                ) : (
                  devices.map((device) => (
                    <tr key={device.id} className="border-b border-gray-50">
                      <td className="py-4 font-semibold">{device.device_name || device.name}</td>
                      <td className="py-4 text-gray-500">{device.type || 'N/A'}</td>
                      <td className="py-4 text-gray-500">{device.user_id || 'N/A'}</td>
                      <td className="py-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${device.status === 'online' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>
                          {device.status || 'Unknown'}
                        </span>
                      </td>
                      <td className="py-4">
                        <button className="text-blue-600 hover:text-blue-800 text-sm">Configure</button>
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
