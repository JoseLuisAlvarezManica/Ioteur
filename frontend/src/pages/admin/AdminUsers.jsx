import React from "react";
import AppLayout from "../../layouts/AppLayout";

function AdminUsers() {
  return (
    <AppLayout>
      <div className="flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Manage Users</h1>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700">Add User</button>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="text-gray-500 border-b border-gray-100">
                <th className="pb-3 font-medium">Name</th>
                <th className="pb-3 font-medium">Email</th>
                <th className="pb-3 font-medium">Role</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-50">
                <td className="py-4">John Doe</td>
                <td className="py-4 text-gray-500">john@example.com</td>
                <td className="py-4">User</td>
                <td className="py-4"><span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-semibold">Active</span></td>
                <td className="py-4">
                  <button className="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                </td>
              </tr>
              <tr>
                <td className="py-4">Admin System</td>
                <td className="py-4 text-gray-500">admin@ioteur.com</td>
                <td className="py-4">Admin</td>
                <td className="py-4"><span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-semibold">Active</span></td>
                <td className="py-4">
                  <button className="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminUsers;
