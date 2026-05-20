import React, { useEffect, useState } from "react";
import AppLayout from "../../layouts/AppLayout";
import { devicesApi } from "../../api/devices";
import { usersApi } from "../../api/users";

function AdminDashboard() {
  const [totalDevices, setTotalDevices] = useState(null);
  const [totalUsers, setTotalUsers] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const devices = await devicesApi.list();
        if (Array.isArray(devices)) {
          setTotalDevices(devices.length);
        }
      } catch (error) {
        console.error("Error fetching device stats:", error);
      }

      try {
        const usersData = await usersApi.list(1, 1);
        setTotalUsers(usersData?.total ?? null);
      } catch (error) {
        console.error("Error fetching user stats:", error);
      }
    };
    fetchStats();
  }, []);

  return (
    <AppLayout>
      <div className="flex flex-col gap-6">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-medium text-gray-500">Total Users</h3>
            <p className="text-4xl font-bold text-gray-900 mt-2">
              {totalUsers !== null ? totalUsers : "--"}
            </p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-medium text-gray-500">Total Devices</h3>
            <p className="text-4xl font-bold text-gray-900 mt-2">
              {totalDevices !== null ? totalDevices : "--"}
            </p>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminDashboard;
