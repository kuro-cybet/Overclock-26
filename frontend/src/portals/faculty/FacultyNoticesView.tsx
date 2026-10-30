import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import {
  Megaphone,
  Bell,
  CheckCheck,
  AlertTriangle,
  Info,
  CheckCircle2,
  RefreshCw,
  Clock,
  ExternalLink
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const FacultyNoticesView: React.FC = () => {
  const [notices, setNotices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread' | 'urgent'>('all');
  const navigate = useNavigate();

  useEffect(() => {
    loadNotices();
  }, []);

  const loadNotices = async () => {
    setLoading(true);
    try {
      const data = await api.getNotifications();
      setNotices(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const markAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      await loadNotices();
    } catch (err) {
      console.error(err);
    }
  };

  const markSingleRead = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.markNotificationRead(id);
      await loadNotices();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredNotices = notices.filter((n) => {
    if (filter === 'unread') return !n.read;
    if (filter === 'urgent') return n.type === 'warning' || n.type === 'critical';
    return true;
  });

  const unreadCount = notices.filter((n) => !n.read).length;

  const cols = [
    {
      header: 'Type',
      render: (r: any) => {
        if (r.type === 'warning' || r.type === 'critical') {
          return (
            <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <AlertTriangle size={18} />
            </div>
          );
        }
        if (r.type === 'success') {
          return (
            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 size={18} />
            </div>
          );
        }
        return (
          <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Info size={18} />
          </div>
        );
      }
    },
    {
      header: 'Notice Title & Message',
      render: (r: any) => (
        <div className="max-w-xl">
          <div className="flex items-center space-x-2">
            <span className={`text-xs font-bold ${r.read ? 'text-gray-700' : 'text-[#345873]'}`}>
              {r.title}
            </span>
            {!r.read && (
              <span className="w-2 h-2 rounded-full bg-[#F29877]" title="Unread Notice" />
            )}
          </div>
          <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-2">{r.message}</p>
        </div>
      )
    },
    {
      header: 'Published',
      accessor: 'created_at' as const,
      render: (r: any) => (
        <span className="text-[11px] text-gray-400 font-mono">
          {new Date(r.created_at).toLocaleDateString()} {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      )
    },
    {
      header: 'Status',
      accessor: 'read' as const,
      render: (r: any) => (
        <span
          className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
            r.read ? 'bg-slate-100 text-slate-600' : 'bg-[#FFD6BA] text-[#8c431b]'
          }`}
        >
          {r.read ? 'Acknowledged' : 'New Notice'}
        </span>
      )
    },
    {
      header: 'Action',
      render: (r: any) => (
        <div className="flex items-center space-x-2">
          {!r.read && (
            <button
              onClick={(e) => markSingleRead(r.id, e)}
              className="px-2.5 py-1 text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-bold transition cursor-pointer"
            >
              Mark Read
            </button>
          )}
          {r.link_url && (
            <button
              onClick={() => navigate(r.link_url)}
              className="p-1.5 text-gray-400 hover:text-[#345873] rounded-lg hover:bg-slate-100 transition cursor-pointer"
              title="Open Reference Link"
            >
              <ExternalLink size={14} />
            </button>
          )}
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-[#8EB9D8]/30 text-[#1f4a6e]">
              Campus Operational Bulletins
            </span>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#F29877]/20 text-[#a34423]">
                {unreadCount} Unread
              </span>
            )}
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Campus Notices & Alerts</h1>
          <p className="text-xs text-gray-500 mt-1">
            Official university bulletins on room readiness, scheduled electrical maintenance, and exam hall protocols.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {unreadCount > 0 && (
            <button
              onClick={markAllRead}
              className="flex items-center space-x-2 px-4 py-2.5 bg-[#FFF4E9] border border-peach hover:bg-[#ffe3cf] text-[#345873] rounded-2xl text-xs font-bold transition cursor-pointer"
            >
              <CheckCheck size={16} />
              <span>Mark All as Read</span>
            </button>
          )}
          <button
            onClick={loadNotices}
            className="p-2.5 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
            filter === 'all'
              ? 'bg-[#345873] text-white'
              : 'text-gray-600 hover:bg-slate-100'
          }`}
        >
          All Notices ({notices.length})
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
            filter === 'unread'
              ? 'bg-[#345873] text-white'
              : 'text-gray-600 hover:bg-slate-100'
          }`}
        >
          Unread Only ({unreadCount})
        </button>
        <button
          onClick={() => setFilter('urgent')}
          className={`px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
            filter === 'urgent'
              ? 'bg-[#345873] text-white'
              : 'text-gray-600 hover:bg-slate-100'
          }`}
        >
          Priority / Alerts
        </button>
      </div>

      {/* Notices Table */}
      <DataTable
        columns={cols}
        data={filteredNotices}
        keyField="id"
        pageSize={10}
        emptyMessage="No notices found for this filter."
      />
    </div>
  );
};

