import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AppLayout from "../layouts/AppLayout";
import { devicesApi } from "../api/devices";
import { useAuth } from "../context/AuthContext";
import { useAppContext } from "../context/AppContext";

/* ── Device Card ─────────────────────────────────────────────── */
function DeviceCard({ device, onClick }) {
  const hasData = !!device.device_name;

  const icon = device.icon || "sensor";

  return (
    <div
      onClick={() => hasData && onClick(device.device_uuid)}
      className={`bg-gray-200 rounded-2xl aspect-square relative overflow-hidden ${
        hasData ? "cursor-pointer hover:bg-gray-300 transition-colors" : ""
      }`}
    >
      {hasData && (
        <>
          {/* ICONO CENTRADO */}
          <div className="absolute inset-0 flex items-center justify-center ">
            <div className="p-2 bg-gray-100/50 rounded-xl">
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
            </div>
          </div>

          {/* INFO ABAJO */}
          <div className="absolute bottom-3 left-3">
            <p className="text-sm font-semibold text-gray-900">
              {device.device_name}
            </p>

            <div className="flex items-center gap-1 mt-0.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  device.status === "active"
                    ? "bg-green-500"
                    : "bg-red-500"
                }`}
              />
              <span
                className={`text-xs font-medium ${
                  device.status === "active"
                    ? "text-green-600"
                    : "text-red-500"
                }`}
              >
                {device.status === "active" ? "Activo" : "Inactivo"}
              </span>
            </div>

            <p className="text-xs text-gray-500 mt-0.5">
              Última vez visto:{" "}
              {device.last_seen
                ? new Date(device.last_seen).toLocaleString()
                : "No hay información"}
            </p>
          </div>
        </>
      )}
    </div>
  );
}

/* ── Add Device Modal ────────────────────────────────────────── */
export function AddDeviceModal({ userId, onClose, onAdded }) {
  const [name, setName] = useState("");
  const { groups } = useAppContext();
  const [mac, setMac] = useState("");
  const [group, setGroup] = useState(groups[0] || ""); // Default al primer grupo o vacío
  const [interval, setInterval] = useState("60");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [color, setColor] = useState("#6B7280"); // gray default
  const [icon, setIcon] = useState("sensor");

  const colors = [
    "#6B7280", // default (gray)
    "#EF4444", // red
    "#F59E0B", // amber
    "#10B981", // green
    "#3B82F6", // blue
    "#9f1cd3", // purple
  ];

  const icons = ["radar", "sensor", "vehículo", "casa"];

  const handleSubmit = async () => {
    if (!name.trim() || !mac.trim() || !interval) {
      setError("Todos los campos son requeridos.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const newDevice = await devicesApi.create({
        userId,
        name,
        macAddress: mac,
        reportInterval: interval,
        color,
        icon,
      });

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
      <div className="bg-white rounded-2xl p-8 w-full max-w-md md:max-w-2xl shadow-xl">

        <h2 className="text-xl font-bold text-gray-900 mb-5">
          Add Device
        </h2>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 text-sm px-3 py-2 rounded-xl mb-4">
            {error}
          </div>
        )}
      
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
          
          {/* PRIMERA COLUMNA */}
          <div className="flex flex-col gap-4">

            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Device name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="border border-gray-300 rounded-xl px-4 py-3 text-sm w-full"
            placeholder="Mi sensor de temperatura"
            />
          </div>

          {/* MAC */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">MAC</label>
            <input
              value={mac}
              onChange={(e) => setMac(e.target.value)}
              className="border border-gray-300 rounded-xl px-4 py-3 text-sm font-mono"
            placeholder="AA:BB:CC:DD:EE:FF"
            />
          </div>

          {/* GROUP */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Grupo</label>
            <input
              list="groups-list"
              value={group}
              onChange={(e) => setGroup(e.target.value)}
              className="border border-gray-300 rounded-xl px-4 py-3 text-sm focus:border-purple-400 focus:ring-1 focus:ring-purple-100 transition-colors"
              placeholder="Asignar a un grupo (ej. Sala)"
            />
            <datalist id="groups-list">
              {groups.map((g) => (
                <option key={g} value={g} />
              ))}
            </datalist>
          </div>

          {/* INTERVAL */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">
              Intervalo de reporte (segundos)
            </label>
            <input
              type="number"
              min="1"
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              className="border border-gray-300 rounded-xl px-4 py-3 text-sm outline-none w-full focus:border-purple-400 focus:ring-1 focus:ring-purple-100 transition-colors"
              placeholder="60"
            />
            <p className="text-xs text-purple-600 font-medium ml-1 mt-0.5">
              Esto nos ayudará a saber si el dispositivo tiene problemas.
            </p>
          </div>
          </div>

          {/* SEGUNDA COLUMNA */}
          <div className="flex flex-col gap-4">

            {/* ICON SELECTOR */}
            <div className="col-span-2">
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Icono
              </label>

            <div className="grid grid-cols-2 gap-2">
              {icons.map((i) => (
                <button
                  key={i}
                  onClick={() => setIcon(i)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm capitalize ${
                    icon === i
                      ? "border-purple-700 border-2 bg-gray-100"
                      : "border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <img
                    src={`/${i}.svg`}
                    className="w-5 h-5"
                    style={{ filter: `drop-shadow(0 0 0 ${color})` }}
                  />
                  {i}
                </button>
              ))}
            </div>
          </div>

          {/* COLOR SELECTOR */}
          <div className="col-span-2">
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Color
            </label>

            <div className="grid grid-cols-6 gap-1">
              {colors.map((c) => (
                <button
                  key={c}
                  onClick={() => setColor(c)}
                  className={`w-10 h-10 rounded-full border-4 ${
                    color === c ? "border-purple-700" : "border-transparent"
                  }`}
                  style={{ backgroundColor: c }}
                />))}
            </div>
          </div>

          <div className="col-span-2 flex items-center gap-3 mt-2">
            <div
              className="w-14 h-14"
              style={{
                backgroundColor: color,
                WebkitMaskImage: `url(/${icon}.svg)`,
                WebkitMaskSize: "contain",
                WebkitMaskRepeat: "no-repeat",
                WebkitMaskPosition: "center",
                maskImage: `url(/${icon}.svg)`,
                maskSize: "contain",
                maskRepeat: "no-repeat",
                maskPosition: "center",
              }}
            />
            <span className="text-sm text-gray-600">Preview del icono</span>
          </div>
              
          {/* ACTIONS */}
          <div className="flex gap-3 justify-end mt-auto col-span-2">
            <button
              onClick={onClose}
              className="px-5 py-2 rounded-xl border border-gray-300 text-sm"
            >
              Cancel
            </button>

            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-purple-700 text-white text-sm"
            >
              {loading ? "Adding..." : "Add"}
            </button>
          </div>
          </div>
          
        </div>

      </div>
    </div>
  );
}

/* ── Dashboard ───────────────────────────────────────────────── */
function Dashboard() {
  const { user } = useAuth();
  const { devices, groups, loadingDevices: loading, errorDevices: error, fetchDevices } = useAppContext();
  const [filter, setFilter]       = useState("all");
  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  const filtered = devices.filter((d) => {
    if (filter === "all") return true;
    return d.status === filter;
  });

  const padded = [
    ...filtered,
    ...Array(Math.max(0, 8 - filtered.length)).fill({ device_uuid: null }),
  ].slice(0, 8);

  return (
    <AppLayout pageTitle="Dashboard">
      <UserBar />

      {/* Notas moradas */}
      <div className="bg-purple-100 border border-purple-200 rounded-2xl p-5 mb-6 shadow-sm relative overflow-hidden flex items-center gap-4">
        <div className="p-3 bg-purple-200 rounded-full text-purple-700">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <div>
          <h3 className="text-purple-900 font-bold text-sm">Resumen del sistema</h3>
          <p className="text-purple-700 text-xs mt-0.5">La conexión con el Gateway está estable. Revisa el estado general de tus dispositivos a continuación.</p>
        </div>
      </div>

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
              key={device.device_uuid ?? `empty-${i}`}
              device={device}
              onClick={(id) => navigate(`/devices/${id}`)}
            />
          ))}
        </div>
      )}

      {showModal && (
        <AddDeviceModal
          userId={user?.id}
          onClose={() => setShowModal(false)}
          onAdded={() => {
            setShowModal(false);
            fetchDevices();
          }}
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