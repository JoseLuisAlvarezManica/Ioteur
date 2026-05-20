import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useAppContext } from "../context/AppContext";
import { AddDeviceModal } from "../pages/Dashboard";

const HomeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
);
const DevicesIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="2" y="3" width="8" height="8" rx="1"/><rect x="14" y="3" width="8" height="8" rx="1"/>
    <rect x="2" y="13" width="8" height="8" rx="1"/><rect x="14" y="13" width="8" height="8" rx="1"/>
  </svg>
);
const ReportsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="8" y1="12" x2="8" y2="16"/>
    <line x1="12" y1="8" x2="12" y2="16"/><line x1="16" y1="10" x2="16" y2="16"/>
  </svg>
);
const BellIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>
  </svg>
);
const DeviceSmIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
  </svg>
);



function Sidebar() {
  const { user } = useAuth();
  const { devices, fetchDevices } = useAppContext();
  const navigate = useNavigate();
  const location = useLocation();
  const [showModal, setShowModal] = useState(false);

  const navItems = [
    { label: "Inicio", icon: <HomeIcon />, path: "/dashboard" },
    { label: "Reportes", icon: <ReportsIcon />, path: "/reports" },
    { label: "Notificaciones", icon: <BellIcon />, path: "/notifications" },
  ];

  const adminNavItems = [
    { label: "Panel de Administrador", icon: <HomeIcon />, path: "/admin/dashboard" },
    { label: "Gestionar Usuarios", icon: <DevicesIcon />, path: "/admin/users" },
    { label: "Gestionar Dispositivos", icon: <DeviceSmIcon />, path: "/admin/devices" },
  ];

  return (
    <aside className={`w-64 bg-gray-100 rounded-2xl p-5 flex flex-col gap-4 self-start max-h-full overflow-y-auto`}>
      {/* Logo */}
<div className="flex items-center gap-3 mb-2">
  {/* Logo */}
  <div className="w-18 h-18 bg-gradient-to-tr from-white to-purple-200 shadow-lg rounded-3xl flex items-center justify-center text-white p-4">
    <img src="/logoioteur.svg" alt="Logo" className="w-10 h-10"/>
  </div>
  <div>
    <span className="text-lg font-bold text-gray-900 tracking-tight">
      <span className="font-bold">iot</span>
      <span className="font-normal text-gray-500">eur</span>
    </span>
    <p className="text-xs text-gray-400 leading-none">IoT monitoring</p>
  </div>
</div>

      {/* Nav items */}
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => {
          const active = location.pathname === item.path;
          return (
            <button
              key={item.label}
              onClick={() => navigate(item.path)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-left transition-colors ${
                active ? "text-black font-semibold bg-purple-200" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          );
        })}
      </nav>

      {user?.role === "admin" && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Admin</p>
          <nav className="flex flex-col gap-1">
            {adminNavItems.map((item) => {
              const active = location.pathname === item.path;
              return (
                <button
                  key={item.label}
                  onClick={() => navigate(item.path)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-left transition-colors ${
                    active ? "text-red-700 font-semibold bg-red-50" : "text-gray-500 hover:text-red-600 hover:bg-red-50"
                  }`}
                >
                  {item.icon}
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      )}

      {/* Dispositivos expandable */}
      <div className="mt-1">
        <div className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 font-medium">
          <DevicesIcon />
          <span>Dispositivos</span>
          <button 
            onClick={() => setShowModal(true)}
            className="ml-auto hover:text-black transition-colors"
            title="Agregar dispositivo"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="cursor-pointer">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
            </svg>
          </button>
        </div>
        <div className="flex flex-col gap-1 ml-3 mt-1">
          {devices.map((device) => {
            const active = location.pathname === `/devices/${device.device_uuid}`;
            return (
              <button
                key={device.device_uuid}
                onClick={() => navigate(`/devices/${device.device_uuid}`)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-left transition-colors ${
                  active ? "text-black font-semibold bg-purple-200" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                <DeviceSmIcon />
                {device.device_name}
              </button>
            );
          })}
        </div>
      </div>

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
    </aside>
  );
}

export default Sidebar;