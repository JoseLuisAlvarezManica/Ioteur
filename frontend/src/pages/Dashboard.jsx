import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AppLayout from "../layouts/AppLayout";
import { devicesApi } from "../api/devices";

/* ── Device Card ─────────────────────────────────────────────── */
function DeviceCard({ device, onClick }) {
  const hasData = !!device.device_name;

  return (
    <div
      onClick={() => hasData && onClick(device.id)}
      className={`bg-gray-200 rounded-2xl aspect-square relative overflow-hidden ${
        hasData ? "cursor-pointer hover:bg-gray-300 transition-colors" : ""
      }`}
    >
      {hasData && (
        <div className="absolute bottom-3 left-3">
          <p className="text-sm font-semibold text-gray-900">{device.device_name}</p>
          <div className="flex items-center gap-1 mt-0.5">
            <span className={`w-2 h-2 rounded-full ${
              device.status === "active" ? "bg-green-500" : "bg-red-500"
            }`} />
            <span className={`text-xs font-medium ${
              device.status === "active" ? "text-green-600" : "text-red-500"
            }`}>
              {device.status === "active" ? "Active" : "Inactive"}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            Last seen: {device.last_seen
              ? new Date(device.last_seen).toLocaleString()
              : "Never"}
          </p>
        </div>
      )}
    </div>
  );
}

/* ── Add Device Modal ────────────────────────────────────────── */
function AddDeviceModal({ onClose, onAdded }) {
  const [name, setName]       = useState("");
  const [mac, setMac]         = useState("");
  const [error, setError]     = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!name.trim() || !mac.trim()) {
      setError("Nombre y dirección MAC son requeridos.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const newDevice = await devicesApi.create({ name, macAddress: mac });
      onAdded(newDevice);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-xl">
        <h2 className="text-xl font-bold text-gray-900 mb-5">Add Device</h2>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 text-sm px-3 py-2 rounded-xl mb-4">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-4 mb-6">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Device name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="border border-gray-300 rounded-xl px-4 py-3 text-sm outline-none"
              placeholder="Mi sensor de temperatura"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">MAC Address</label>
            <input
              type="text"
              value={mac}
              onChange={(e) => setMac(e.target.value)}
              className="border border-gray-300 rounded-xl px-4 py-3 text-sm outline-none font-mono"
              placeholder="AA:BB:CC:DD:EE:FF"
            />
          </div>
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl border border-gray-300 text-sm text-gray-600 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-5 py-2 rounded-xl bg-gray-900 text-white text-sm font-medium hover:bg-gray-700 disabled:opacity-60"
          >
            {loading ? "Adding..." : "Add"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Dashboard ───────────────────────────────────────────────── */
function Dashboard() {
  const [filter, setFilter]       = useState("all");
  const [devices, setDevices]     = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    devicesApi.list()
      .then(setDevices)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = devices.filter((d) => {
    if (filter === "all") return true;
    return d.status === filter;
  });

  const padded = [
    ...filtered,
    ...Array(Math.max(0, 8 - filtered.length)).fill({ id: null }),
  ].slice(0, 8);

  return (
    <AppLayout pageTitle="Dashboard">
      <UserBar />
      <FilterBar filter={filter} setFilter={setFilter} />

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Devices</h2>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 text-sm font-medium text-gray-800 hover:text-black"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="16"/>
            <line x1="8" y1="12" x2="16" y2="12"/>
          </svg>
          Add Device
        </button>
      </div>

      {loading && <p className="text-sm text-gray-400">Loading devices...</p>}
      {error   && <p className="text-sm text-red-500">{error}</p>}

      {!loading && !error && (
        <div className="grid grid-cols-4 gap-4">
          {padded.map((device, i) => (
            <DeviceCard
              key={device.id ?? `empty-${i}`}
              device={device}
              onClick={(id) => navigate(`/devices/${id}`)}
            />
          ))}
        </div>
      )}

      {showModal && (
        <AddDeviceModal
          onClose={() => setShowModal(false)}
          onAdded={(d) => setDevices((prev) => [...prev, d])}
        />
      )}
    </AppLayout>
  );
}

/* ── Exports compartidos (los usan otras páginas) ────────────── */
export function UserBar() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const handleLogout = async () => {
    const { authApi } = await import("../api/auth");
    try { await authApi.logout(); } catch { /* ignore */ }
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/");
  };

  return (
    <div className="flex justify-end items-center gap-2 mb-4">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-gray-600">
        <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
      </svg>
      <span className="text-sm text-gray-700">{user.name || "Name"}</span>
      <button
        onClick={handleLogout}
        title="Logout"
        className="w-8 h-8 flex items-center justify-center rounded-full border border-gray-300 hover:bg-gray-100"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
          <polyline points="16 17 21 12 16 7"/>
          <line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
      </button>
    </div>
  );
}

export function FilterBar({ filter, setFilter }) {
  return (
    <div className="flex gap-2 mb-6">
      {["all", "active", "inactive"].map((f) => (
        <button
          key={f}
          onClick={() => setFilter(f)}
          className={`px-4 py-1.5 rounded-full border text-sm capitalize transition-colors ${
            filter === f
              ? "border-gray-900 text-gray-900 font-medium"
              : "border-gray-400 text-gray-500 hover:border-gray-600"
          }`}
        >
          {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
        </button>
      ))}
    </div>
  );
}

export default Dashboard;