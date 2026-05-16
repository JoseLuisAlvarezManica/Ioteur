import { useNavigate, useLocation } from "react-router-dom";

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

const mockDevices = [
  { id: 1, name: "Device #1" },
  { id: 2, name: "Device #2" },
  { id: 3, name: "Device #3" },
];

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { label: "Home", icon: <HomeIcon />, path: "/dashboard" },
    { label: "Devices", icon: <DevicesIcon />, path: "/devices" },
    { label: "Reports", icon: <ReportsIcon />, path: "/reports" },
    { label: "Notifications", icon: <BellIcon />, path: "/notifications" },
  ];

  return (
    <aside className="w-64 bg-gray-100 rounded-2xl p-5 flex flex-col gap-4 self-start min-h-[600px]">
      {/* Logo */}
<div className="flex items-center gap-3 mb-2">
  <div className="w-10 h-10 border-2 border-gray-800 rounded-xl flex items-center justify-center flex-shrink-0">
    <svg width="28" height="28" viewBox="0 0 80 80" fill="none">
      <circle cx="40" cy="34" r="4" fill="#1a1a1a"/>
      <path d="M28 25 Q40 13 52 25" fill="none" stroke="#1a1a1a" strokeWidth="2.5" strokeLinecap="round"/>
      <path d="M19 17 Q40 1 61 17" fill="none" stroke="#1a1a1a" strokeWidth="2.5" strokeLinecap="round"/>
      <polyline points="8,62 22,48 32,55 40,43 50,50 62,34 74,39" fill="none" stroke="#1a1a1a" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
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
                active ? "text-black font-semibold" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* My Devices expandable */}
      <div className="mt-1">
        <div className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 font-medium">
          <DevicesIcon />
          <span>My Devices</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="ml-auto">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
          </svg>
        </div>
        <div className="flex flex-col gap-1 ml-3 mt-1">
          {mockDevices.map((device) => {
            const active = location.pathname === `/devices/${device.id}`;
            return (
              <button
                key={device.id}
                onClick={() => navigate(`/devices/${device.id}`)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-left transition-colors ${
                  active ? "text-black font-semibold" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                <DeviceSmIcon />
                {device.name}
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;