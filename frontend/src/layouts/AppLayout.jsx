import Sidebar from "./Sidebar";

function AppLayout({ children, pageTitle }) {
  return (
    <div className="h-screen bg-gray-200 flex flex-col overflow-hidden">
      {/* Top bar (Header) */}
      <div className="bg-gray-100 border-b border-gray-300 px-4 py-2 flex justify-between items-center shrink-0">
        <span className="text-gray-500 text-sm font-medium">{pageTitle}</span>
      </div>

      <div className="flex flex-1 p-6 gap-6 overflow-hidden">
        <Sidebar className="h-full overflow-y-auto" />
        <main className="flex-1 overflow-y-auto pb-6 pr-2">{children}</main>
      </div>
    </div>
  );
}

export default AppLayout;