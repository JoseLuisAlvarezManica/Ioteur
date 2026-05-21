import React, { useEffect, useState } from "react";
import AppLayout from "../../layouts/AppLayout";
import { usersApi } from "../../api/users";

const PAGE_SIZE = 10;

function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await usersApi.list(page, PAGE_SIZE);
        setUsers(Array.isArray(data?.users) ? data.users : []);
        setTotalPages(data?.total_pages ?? 1);
      } catch (err) {
        console.error("Failed to fetch users:", err);
        setError("No se pudieron cargar los usuarios.");
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, [page]);

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
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, name: newName, role: newRole } : u))
      );
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
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 overflow-hidden">
          {loading ? (
            <div className="p-4 text-center text-gray-500">Loading users...</div>
          ) : error ? (
            <div className="p-4 text-center text-red-500">{error}</div>
          ) : (
            <>
              <table className="w-full text-left">
                <thead>
                  <tr className="text-gray-500 border-b border-gray-100">
                    <th className="pb-3 font-medium">Name</th>
                    <th className="pb-3 font-medium">Email</th>
                    <th className="pb-3 font-medium">Role</th>
                    <th className="pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="py-4 text-center text-gray-500">
                        No users found.
                      </td>
                    </tr>
                  ) : (
                    users.map((user) => (
                      <tr key={user.id} className="border-b border-gray-50">
                        <td className="py-4">{user.name}</td>
                        <td className="py-4 text-gray-500">{user.email}</td>
                        <td className="py-4">
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${
                              user.role === "admin"
                                ? "bg-purple-100 text-purple-700"
                                : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {user.role}
                          </span>
                        </td>
                        <td className="py-4">
                          <button
                            onClick={() => handleEdit(user)}
                            className="mr-4 text-blue-600 hover:text-blue-800 text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(user.id)}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-end gap-3 mt-4 pt-4 border-t border-gray-100">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                    className="px-3 py-1 text-sm rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
                  >
                    ← Prev
                  </button>
                  <span className="text-sm text-gray-500">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                    className="px-3 py-1 text-sm rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminUsers;
