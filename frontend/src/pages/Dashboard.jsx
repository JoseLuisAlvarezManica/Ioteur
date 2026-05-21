import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AppLayout from "../layouts/AppLayout";
import { devicesApi } from "../api/devices";
import { BASE_URL } from "../api/client";
import { waitForDevicePresent } from "../utils/poll";
import { useAuth } from "../context/AuthContext";
import { useAppContext } from "../context/AppContext";

/* ── Device Card ─────────────────────────────────────────────── */
function DeviceCard({ device, onClick }) {
  const hasData = !!device.device_name;

  return (
    <div
      onClick={() => hasData && onClick(device.device_uuid)}
      className={`bg-white border border-gray-200 rounded-2xl p-4 flex items-center gap-4 ${
        hasData ? "cursor-pointer hover:bg-gray-50 transition-colors" : ""
      }`}
    >
      {hasData && (
        <>
          {/* ICONO A LA IZQUIERDA */}
          <div className="flex-shrink-0 p-2 bg-gray-100 rounded-xl">
            <div
              className="w-10 h-10"
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

          {/* INFO A LA DERECHA */}
          <div className="flex flex-col overflow-hidden">
            <p className="text-sm font-semibold text-gray-900 truncate">
              {device.device_name}
            </p>

            <div className="flex items-center gap-1 mt-0.5">
              <span
                className={`w-2 h-2 rounded-full flex-shrink-0 ${
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

            <p className="text-xs text-gray-500 mt-1 truncate">
              Visto:{" "}
              {device.last_seen
                ? new Date(device.last_seen).toLocaleDateString() + " " + new Date(device.last_seen).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                : "Sin datos"}
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

  const icons = ["radar", "sensor", "vehículo", "casa", "micro", "rasp"];

  useEffect(() => {
    if (!group && groups.length > 0) {
      setGroup(groups[0]);
    }
  }, [group, groups]);

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
        group,
      });

      // Espera hasta que el device aparezca upstream (asíncrono vía RabbitMQ)
      if (newDevice?.device_uuid) {
        await waitForDevicePresent(newDevice.device_uuid, { interval: 100, maxAttempts: 10 });
      }

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
          Añadir nuevo dispositivo
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
              <label className="text-sm font-medium text-gray-700">Nombre del dispositivo</label>
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
            <span className="text-sm text-gray-600">Vista previa del icono</span>
          </div>
              
          {/* ACTIONS */}
          <div className="flex gap-3 justify-end mt-auto col-span-2">
            <button
              onClick={onClose}
              className="px-5 py-2 rounded-xl border border-gray-300 text-sm"
            >
              Cancelar
            </button>

            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-purple-700 text-white text-sm"
            >
              {loading ? "Agregando..." : "Agregar"}
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
  const { devices, groups, loadingDevices: loading, errorDevices: error, fetchDevices, globalRefresh } = useAppContext();
  const [filter, setFilter]       = useState("Todos");
  const [groupFilter, setGroupFilter] = useState("Todos los grupos");
  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  const availableGroups = ["Todos los grupos", ...new Set(devices.map(d => d.group || "Sin grupo"))];

  const filtered = devices.filter((d) => {
    const matchesStatus = filter === "Todos" ? true : d.status === filter;
    const matchesGroup = groupFilter === "Todos los grupos" ? true : (d.group || "Sin grupo") === groupFilter;
    return matchesStatus && matchesGroup;
  });

  const groupedDevices = filtered.reduce((acc, device) => {
    const groupName = device.group || "Sin grupo";
    if (!acc[groupName]) acc[groupName] = [];
    acc[groupName].push(device);
    return acc;
  }, {});

  return (
    <AppLayout pageTitle="Dashboard de Dispositivos">
      <UserBar />

      <FilterBar 
        filter={filter} 
        setFilter={setFilter} 
        groupFilter={groupFilter} 
        setGroupFilter={setGroupFilter} 
        availableGroups={availableGroups} 
      />

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Dispositivos</h2>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 text-sm font-medium text-gray-800 hover:text-black"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="16"/>
            <line x1="8" y1="12" x2="16" y2="12"/>
          </svg>
          Añadir Dispositivo
        </button>
      </div>

      {loading && <p className="text-sm text-gray-400">Cargando dispositivos...</p>}
      {error   && <p className="text-sm text-red-500">{error}</p>}

      {!loading && !error && (
        <div className="flex flex-col gap-8">
          {Object.entries(groupedDevices).map(([groupName, groupDevices]) => (
            <div key={groupName} className="bg-white p-5 rounded-2xl border border-gray-200">
              <h3 className="text-xl font-bold text-gray-900 mb-4 pb-2 border-b border-gray-100 placeholder:">{groupName}</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {groupDevices.map((device) => (
                  <DeviceCard
                    key={device.device_uuid}
                    device={device}
                    onClick={(id) => navigate(`/devices/${id}`)}
                  />
                ))}
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <p className="text-sm text-gray-500">No hay dispositivos para mostrar.</p>
          )}
        </div>
      )}

      {showModal && (
        <AddDeviceModal
          userId={user?.id}
          onClose={() => setShowModal(false)}
          onAdded={() => {
            setShowModal(false);
            globalRefresh();
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
  const [gwStatus, setGwStatus] = useState("checking");

  useEffect(() => {
    const check = async () => {
      try {
        const controller = new AbortController();
        const tid = setTimeout(() => controller.abort(), 4000);
        const res = await fetch(`${BASE_URL}/health`, { signal: controller.signal });
        clearTimeout(tid);
        const data = await res.json().catch(() => ({}));
        setGwStatus(data.status === "ok" ? "online" : "offline");
      } catch {
        setGwStatus("offline");
      }
    };
    check();
    const id = setInterval(check, 30000);
    return () => clearInterval(id);
  }, []);

  const handleLogout = async () => {
    const { authApi } = await import("../api/auth");
    try { await authApi.logout(); } catch { /* ignore */ }
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/");
  };

  const dotColor =
    gwStatus === "online"  ? "bg-green-500" :
    gwStatus === "offline" ? "bg-red-500"   : "bg-yellow-400";
  const label =
    gwStatus === "online"  ? "En línea"  :
    gwStatus === "offline" ? "Desconectado" : "...";

  return (
    <div className="flex justify-end items-center gap-3 mb-4">
      {/* Gateway status pill */}
      <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-gray-200 bg-white shadow-sm">
        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} />
        <span className="text-xs font-medium text-gray-600">{label}</span>
      </div>

      {/* User info */}
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-gray-600">
        <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
      </svg>
      <span className="text-sm text-gray-700">{user.name || "Nombre"}</span>
      <button
        onClick={handleLogout}
        title="Cerrar sesión"
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

export function FilterBar({ filter, setFilter, groupFilter, setGroupFilter, availableGroups = [] }) {
  return (
    <div className="flex gap-4 mb-6 items-center flex-wrap">
      <div className="flex gap-2">
        {["Todos", "active", "inactive"].map((f) => {
        let label = "Todos";
        if (f === "active") label = "Activo";
        if (f === "inactive") label = "Inactivo";

        return (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-full border text-sm capitalize transition-colors ${
              filter === f
                ? "border-gray-900 text-gray-900 font-medium"
                : "border-gray-400 text-gray-500 hover:border-gray-600"
            }`}
          >
            {label}
          </button>
        );
      })}
      </div>

      {availableGroups.length > 0 && (
        <div className="flex items-center gap-2 border-l border-gray-300 pl-4">
          <label htmlFor="group-select" className="text-sm text-gray-600 font-medium">Grupo:</label>
          <select
            id="group-select"
            value={groupFilter}
            onChange={(e) => setGroupFilter(e.target.value)}
            className="border border-gray-300 rounded-xl px-3 py-1.5 text-sm focus:border-gray-400 focus:ring-1 focus:ring-gray-400 transition-colors bg-white text-gray-700 outline-none cursor-pointer"
          >
            {availableGroups.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}

export default Dashboard;