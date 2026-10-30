import React, { useState, useEffect } from 'react';
import { useAuth } from '../../core/auth/AuthProvider';
import { api } from '../../core/api/client';
import type { Notification } from '../../types';
import { Bell, Check, ExternalLink, X } from 'lucide-react';

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationPanel: React.FC<NotificationPanelProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadNotifications();
    }
  }, [isOpen]);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await api.getNotifications();
      setNotifications(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
    } catch {
      // ignore
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch {
      // ignore
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs"
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm bg-white h-full shadow-2xl flex flex-col border-l border-gray-200 animate-slide-left"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 bg-[#345873] text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bell size={18} />
            <h3 className="font-bold text-sm tracking-wide">Live Dispatch & Alerts</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 transition cursor-pointer min-h-[36px] min-w-[36px] flex items-center justify-center"
            title="Close Alerts"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-3 bg-gray-50 border-b flex items-center justify-between text-xs">
          <span className="text-gray-500 font-medium">Targeted for {user?.role}</span>
          <button
            onClick={handleMarkAllRead}
            className="text-[#345873] hover:underline font-semibold flex items-center cursor-pointer min-h-[36px] px-2"
          >
            <Check size={14} className="mr-1" /> Mark all read
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
          {loading ? (
            <div className="p-8 text-center text-gray-400 text-xs">Fetching alerts...</div>
          ) : notifications.length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-xs">No active alerts for your role.</div>
          ) : (
            notifications.map((n) => {
              const isCrit = n.type === 'critical' || n.type === 'warning';
              return (
                <div
                  key={n.id}
                  className={`p-3 rounded-xl border text-xs transition ${
                    n.read
                      ? 'bg-white border-gray-100 opacity-75'
                      : isCrit
                      ? 'bg-rose-50 border-rose-200'
                      : 'bg-blue-50/50 border-blue-100'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <span
                      className={`font-bold ${
                        isCrit ? 'text-rose-800' : 'text-[#345873]'
                      }`}
                    >
                      {n.title}
                    </span>
                    {!n.read && (
                      <button
                        onClick={() => handleMarkRead(n.id)}
                        className="text-[10px] text-gray-400 hover:text-gray-700 ml-2 shrink-0 cursor-pointer p-1"
                        title="Mark read"
                      >
                        <Check size={12} />
                      </button>
                    )}
                  </div>
                  <p className="text-gray-600 mt-1">{n.message}</p>
                  <div className="flex items-center justify-between mt-2 pt-1 border-t border-gray-100/60 text-[10px] text-gray-400">
                    <span>
                      {new Date(n.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    {n.link_url && (
                      <a
                        href={n.link_url}
                        className="text-[#345873] hover:underline font-semibold flex items-center"
                      >
                        View <ExternalLink size={10} className="ml-0.5" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
