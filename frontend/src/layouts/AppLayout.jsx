import Sidebar from "./Sidebar";

function AppLayout({ children, pageTitle }) {
  return (
    <div className="min-h-screen bg-gray-200 flex flex-col">
      {/* Top bar */}
      <div className="bg-gray-100 border-b border-gray-300 px-4 py-2">
        <span className="text-gray-500 text-sm">{pageTitle}</span>
      </div>

      <div className="flex flex-1 p-6 gap-6">
        <Sidebar />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}

export default AppLayout;