import { useState, useEffect } from "react";
import AppLayout from "../layouts/AppLayout";
import { notificationsApi } from "../api/notifications";
import { UserBar } from "./Dashboard";

const severityStyles = {
  info:     { dot: "bg-blue-400",   badge: "bg-blue-50 text-blue-700 border-blue-200" },
  warning:  { dot: "bg-yellow-400", badge: "bg-yellow-50 text-yellow-700 border-yellow-200" },
  critical: { dot: "bg-red-500",    badge: "bg-red-50 text-red-700 border-red-200" },
};

function NotificationItem({ notif }) {
  const styles = severityStyles[notif.severity] || severityStyles.info;

  return (
    <div className="flex items-start gap-4 p-4 rounded-2xl border bg-white border-gray-100 transition-colors">

      {/* Severity dot */}
      <div className="mt-1 flex-shrink-0">
        <span className={`w-2.5 h-2.5 rounded-full block ${styles.dot}`} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border capitalize ${styles.badge}`}>
            {notif.severity}
          </span>
        </div>
        <p className="text-sm text-gray-800 font-medium">{notif.reason}</p>
        <p className="text-sm text-gray-500 mt-0.5 break-words">{notif.message}</p>
        <p className="text-xs text-gray-400 mt-1">
          {new Date(notif.created_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
}

function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading]             = useState(true);
  const [error, setError]                 = useState(null);
  const [filter, setFilter]               = useState("all");

  useEffect(() => {
    notificationsApi.list()
      .then(setNotifications)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = notifications.filter((n) => {
    if (filter === "all") return true;
    return n.severity === filter;
  });

  return (
    <AppLayout pageTitle="Notificaciones">
      <UserBar />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Notificaciones</h2>
          {notifications.length > 0 && (
            <p className="text-sm text-gray-500 mt-0.5">
              {notifications.length} notificación{notifications.length > 1 ? "es" : ""}
            </p>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {["all", "info", "warning", "critical"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-full border text-sm capitalize transition-colors ${
              filter === f
                ? "border-gray-900 text-gray-900 font-medium"
                : "border-gray-400 text-gray-500 hover:border-gray-600"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-gray-400">Cargando notificaciones...</p>}
      {error   && <p className="text-sm text-red-500">{error}</p>}

      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-gray-400">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mb-3">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 01-3.46 0"/>
          </svg>
          <p className="text-sm">No hay notificaciones</p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="flex flex-col gap-3">
          {filtered.map((n) => (
            <NotificationItem key={n.id} notif={n} />
          ))}
        </div>
      )}
    </AppLayout>
  );
}

export default Notifications;