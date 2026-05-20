import React, { useEffect, useState } from "react";
import AppLayout from "../../layouts/AppLayout";
import { usersApi } from "../../api/users";

function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const data = await usersApi.list();
        setUsers(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to fetch users:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  const handleDelete = async (id) => {
    if (!confirm("¿Eliminar usuario?")) return;
    try {
      await usersApi.delete(id);
      setUsers((prev) => prev.filter((u) => u.id !== id));
    } catch (err) {
      console.error("Failed to delete user:", err);
      alert("No se pudo eliminar el usuario");
    }
  };

  const handleEdit = async (user) => {
    const newName = prompt("Nombre:", user.name);
    if (newName === null) return;
    const newRole = prompt("Rol (user/admin):", user.role || "user");
    if (newRole === null) return;
    try {
      await usersApi.update(user.id, { name: newName, role: newRole });
      setUsers((prev) => prev.map((u) => (u.id === user.id ? { ...u, name: newName, role: newRole } : u)));
    } catch (err) {
      console.error("Failed to update user:", err);
      alert("No se pudo actualizar el usuario");
    }
  };

  return (
    <AppLayout>
      <div className="flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Manage Users</h1>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700">Add User</button>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 overflow-hidden">
          {loading ? (
            <div className="p-4 text-center text-gray-500">Loading users...</div>
          ) : (
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
                {users.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-4 text-center text-gray-500">No users found.</td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.id} className="border-b border-gray-50">
                      <td className="py-4">{user.name}</td>
                      <td className="py-4 text-gray-500">{user.email}</td>
                      <td className="py-4">{user.role}</td>
                      <td className="py-4"><span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-semibold">Active</span></td>
                      <td className="py-4">
                        <button onClick={() => handleEdit(user)} className="mr-4 text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                        <button onClick={() => handleDelete(user.id)} className="text-red-600 hover:text-red-800 text-sm">Delete</button>
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

export default AdminUsers;
