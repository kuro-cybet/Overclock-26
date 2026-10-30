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
    <div className="fixed inset-0 z-50 flex justify-end bg-black/20 backdrop-blur-xs">
      <div className="w-full max-w-sm bg-white h-full shadow-2xl flex flex-col border-l border-gray-200 animate-slide-left">
        <div className="p-4 bg-[#345873] text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bell size={18} />
            <h3 className="font-bold text-sm tracking-wide">Live Dispatch & Alerts</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 transition cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-3 bg-gray-50 border-b flex items-center justify-between text-xs">
          <span className="text-gray-500 font-medium">Targeted for {user?.role}</span>
          <button
            onClick={handleMarkAllRead}
            className="text-[#345873] hover:underline font-semibold flex items-center cursor-pointer"
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
                    <h4 className="font-bold text-gray-800">{n.title}</h4>
                    {!n.read && (
                      <span className="w-2 h-2 rounded-full bg-rose-500 shrink-0 mt-1" />
                    )}
                  </div>
                  <p className="text-gray-600 mt-1 leading-relaxed">{n.message}</p>
                  <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-gray-100">
                    <span className="text-[10px] text-gray-400">
                      {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <div className="flex space-x-2">
                      {!n.read && (
                        <button
                          onClick={() => handleMarkRead(n.id)}
                          className="text-[11px] text-gray-500 hover:text-gray-800 cursor-pointer"
                        >
                          Dismiss
                        </button>
                      )}
                      {n.link_url && (
                        <a
                          href={n.link_url}
                          className="text-[11px] text-[#345873] font-semibold flex items-center hover:underline"
                        >
                          View <ExternalLink size={10} className="ml-0.5" />
                        </a>
                      )}
                    </div>
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

