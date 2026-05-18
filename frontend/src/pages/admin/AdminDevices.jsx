import React from "react";
import AppLayout from "../../layouts/AppLayout";

function AdminDevices() {
  return (
    <AppLayout>
      <div className="flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Manage Devices</h1>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700">Add Device</button>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 overflow-hidden">
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
              <tr className="border-b border-gray-50">
                <td className="py-4 font-semibold">Sensor Alpha</td>
                <td className="py-4 text-gray-500">Temperature</td>
                <td className="py-4 text-gray-500">john@example.com</td>
                <td className="py-4"><span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-semibold">Online</span></td>
                <td className="py-4">
                  <button className="text-blue-600 hover:text-blue-800 text-sm">Configure</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminDevices;
