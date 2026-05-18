import React from "react";
import AppLayout from "../../layouts/AppLayout";

function AdminDashboard() {
  return (
    <AppLayout>
      <div className="flex flex-col gap-6">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-medium text-gray-500">Total Users</h3>
            <p className="text-4xl font-bold text-gray-900 mt-2">124</p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-medium text-gray-500">Total Devices</h3>
            <p className="text-4xl font-bold text-gray-900 mt-2">56</p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-medium text-gray-500">Active Alerts</h3>
            <p className="text-4xl font-bold text-red-600 mt-2">3</p>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminDashboard;
