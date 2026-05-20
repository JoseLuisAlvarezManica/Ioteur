import Sidebar from "./Sidebar";
import { useAppContext } from "../context/AppContext";

function AppLayout({ children, pageTitle }) {
  const { globalRefresh, loadingDevices } = useAppContext();

  return (
    <div className="h-screen bg-gray-200 flex flex-col overflow-hidden">
      {/* Top bar (Header) */}
      <div className="bg-gray-100 border-b border-gray-300 px-4 py-2 flex justify-between items-center shrink-0">
        <span className="text-gray-500 text-sm font-medium">{pageTitle}</span>
        
        <button
          onClick={globalRefresh}
          disabled={loadingDevices}
          className="flex items-center gap-2 px-3 py-1 rounded border border-gray-300 bg-white text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
          title="Refrescar datos globally"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={loadingDevices ? "animate-spin" : ""}>
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
          {loadingDevices ? "Refrescando..." : "Refrescar"}
        </button>
      </div>

      <div className="flex flex-1 p-6 gap-6 overflow-hidden">
        <Sidebar className="h-full overflow-y-auto" />
        <main className="flex-1 overflow-y-auto pb-6 pr-2">{children}</main>
      </div>
    </div>
  );
}

export default AppLayout;