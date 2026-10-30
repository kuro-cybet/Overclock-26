import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { Megaphone, Bell, BellOff, Filter } from 'lucide-react';

export const StudentNoticeBoardView: React.FC = () => {
  const [notices, setNotices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread' | 'urgent'>('all');

  useEffect(() => {
    loadNotices();
  }, []);

  const loadNotices = async () => {
    setLoading(true);
    try {
      const res = await api.getNotifications();
      setNotices(res || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = notices.filter((n) => {
    if (filter === 'unread') return !n.is_read;
    if (filter === 'urgent') return n.priority === 'critical' || n.priority === 'high';
    return true;
  });

  // Augment with simulated campus bulletin data
  const bulletins = [
    { id: 'b1', title: 'Semester Examination Schedule Published', body: 'End-semester exams begin 18 Nov 2026. Check the academic calendar for room allocations.', category: 'Academic', priority: 'high', date: '2026-10-28', is_read: false },
    { id: 'b2', title: 'Campus Wi-Fi Maintenance — Block C', body: 'Scheduled maintenance on 2 Nov 2026 from 02:00–06:00. Expect temporary outages in Block C.', category: 'Infrastructure', priority: 'medium', date: '2026-10-27', is_read: false },
    { id: 'b3', title: 'Library Extended Hours (Exam Season)', body: 'The main library will remain open until 11 PM from 1 Nov to 30 Nov 2026.', category: 'Facilities', priority: 'low', date: '2026-10-26', is_read: true },
    { id: 'b4', title: 'Cafeteria Menu Update — New Vegan Options', body: 'The campus cafeteria has introduced a new plant-based meal menu starting 1 Nov 2026.', category: 'Campus Life', priority: 'low', date: '2026-10-25', is_read: true },
    { id: 'b5', title: 'Fire Drill — All Blocks — 5 Nov 2026', body: 'Mandatory campus-wide fire evacuation drill at 10:00 AM on 5 Nov. All students must participate.', category: 'Safety', priority: 'critical', date: '2026-10-24', is_read: false },
    { id: 'b6', title: 'Sports Complex Closure for Renovation', body: 'The indoor sports complex will be closed from 10 Nov – 20 Nov 2026 for floor resurfacing.', category: 'Facilities', priority: 'medium', date: '2026-10-23', is_read: true },
    { id: 'b7', title: 'Hostel Curfew Reminder — 11 PM', body: 'All residents are reminded that the hostel gate closes at 11 PM. Late returns require warden approval.', category: 'Hostel', priority: 'medium', date: '2026-10-22', is_read: true },
    { id: 'b8', title: 'Scholarship Applications Open — Merit Round', body: 'Students with CGPA ≥ 8.0 can apply for the merit scholarship before 15 Nov 2026.', category: 'Academic', priority: 'high', date: '2026-10-21', is_read: false },
    { id: 'b9', title: 'Printing Lab — New Printer Installed', body: 'A new high-speed A3 printer is now available in Lab 204, Block A. Quota: 50 pages/week.', category: 'Infrastructure', priority: 'low', date: '2026-10-20', is_read: true },
    { id: 'b10', title: 'Emergency Contact Numbers Updated', body: 'Please save the updated campus security and emergency helpline: +91-9000-CAMPUS.', category: 'Safety', priority: 'high', date: '2026-10-19', is_read: false },
  ];

  const filteredBulletins = bulletins.filter((b) => {
    if (filter === 'unread') return !b.is_read;
    if (filter === 'urgent') return b.priority === 'critical' || b.priority === 'high';
    return true;
  });

  const cols = [
    {
      header: 'Notice',
      accessor: 'title' as const,
      render: (r: any) => (
        <div className="flex items-start space-x-2">
          {!r.is_read && <span className="mt-1 w-2 h-2 rounded-full bg-[#A58ACF] shrink-0" />}
          <div>
            <p className={`text-sm font-bold ${r.is_read ? 'text-gray-600' : 'text-[#345873]'}`}>{r.title}</p>
            <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{r.body}</p>
          </div>
        </div>
      )
    },
    {
      header: 'Category',
      accessor: 'category' as const,
      render: (r: any) => (
        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">{r.category}</span>
      )
    },
    {
      header: 'Priority',
      accessor: 'priority' as const,
      render: (r: any) => <StatusBadge status={r.priority} />
    },
    {
      header: 'Date',
      accessor: 'date' as const,
      render: (r: any) => <span className="text-xs text-gray-400 font-mono">{r.date}</span>
    },
    {
      header: 'Status',
      accessor: 'is_read' as const,
      render: (r: any) => (
        <span className={`text-xs font-bold ${r.is_read ? 'text-gray-400' : 'text-[#A58ACF]'}`}>
          {r.is_read ? 'Read' : 'Unread'}
        </span>
      )
    }
  ];

  const unreadCount = bulletins.filter((b) => !b.is_read).length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-[#A58ACF]/15 text-[#A58ACF] flex items-center justify-center">
            <Megaphone size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-[#345873]">Notice Board</h1>
            <p className="text-xs text-gray-500 mt-0.5">Campus-wide announcements, alerts and bulletins</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {unreadCount > 0 && (
            <span className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-[#A58ACF]/15 text-[#543b7a] text-xs font-bold">
              <Bell size={13} />
              <span>{unreadCount} unread</span>
            </span>
          )}
        </div>
      </div>

      {/* Demonstration Dataset Banner */}
      <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl flex items-center gap-3 text-xs text-amber-900">
        <span className="px-2 py-0.5 rounded-md bg-amber-200 font-black text-[10px] tracking-wide text-amber-900 shrink-0">
          DEMONSTRATION DATASET
        </span>
        <p>
          The campus bulletins and announcement items listed below are simulated for demonstration and preview purposes. Live system alerts are delivered via your real-time notification feed.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center space-x-2">
        <Filter size={14} className="text-gray-400" />
        {(['all', 'unread', 'urgent'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition capitalize ${
              filter === f
                ? 'bg-[#A58ACF] text-white shadow'
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Notices Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-extrabold text-sm text-[#345873]">Campus Bulletins & Announcements</h3>
          <span className="text-xs text-gray-400">{filteredBulletins.length} notices</span>
        </div>
        <div className="p-4">
          <DataTable
            columns={cols}
            data={filteredBulletins}
            keyField="id"
            emptyMessage="No notices match the selected filter."
          />
        </div>
      </div>
    </div>
  );
};

