import React, { useState } from 'react';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { Bus, Home, MapPin, Clock, Phone, AlertTriangle } from 'lucide-react';

const BUS_ROUTES = [
  { id: 'rt-01', route: 'Route 1 — City Centre Loop', stops: 'Main Gate → City Mall → Central Station → Main Gate', timing: '07:30 / 17:30 / 20:00', seats: 50, available: 12, status: 'on_time' },
  { id: 'rt-02', route: 'Route 2 — North District', stops: 'Main Gate → Riverside → North Park → Uptown', timing: '07:00 / 17:00 / 19:30', seats: 45, available: 0, status: 'full' },
  { id: 'rt-03', route: 'Route 3 — South Residential', stops: 'Main Gate → Garden Colony → South Market → Lake View', timing: '07:15 / 17:15 / 20:30', seats: 40, available: 7, status: 'on_time' },
  { id: 'rt-04', route: 'Route 4 — Airport Express', stops: 'Main Gate → Highway Junction → Airport Terminal', timing: '05:30 / 22:00', seats: 30, available: 18, status: 'on_time' },
  { id: 'rt-05', route: 'Route 5 — East Suburbs', stops: 'Main Gate → Tech Park → East Colony → Old Town', timing: '07:45 / 17:45', seats: 40, available: 3, status: 'delayed' },
];

const HOSTEL_BLOCKS = [
  { id: 'h-A', block: 'Block A (Boys)', warden: 'Mr. Rajan Kumar', contact: '+91-9001-000-1A', rooms: 80, occupied: 78, facilities: 'Wi-Fi, Laundry, Common Room, 24h Security', status: 'available' },
  { id: 'h-B', block: 'Block B (Boys)', warden: 'Mr. Suresh Pillai', contact: '+91-9001-000-1B', rooms: 80, occupied: 80, facilities: 'Wi-Fi, Laundry, Gym, CCTV', status: 'full' },
  { id: 'h-C', block: 'Block C (Girls)', warden: 'Ms. Priya Menon', contact: '+91-9001-000-1C', rooms: 60, occupied: 55, facilities: 'Wi-Fi, Laundry, Common Room, Biometric Entry', status: 'available' },
  { id: 'h-D', block: 'Block D (Girls)', warden: 'Ms. Anita Sharma', contact: '+91-9001-000-1D', rooms: 60, occupied: 60, facilities: 'Wi-Fi, Laundry, Common Room, 24h Security', status: 'full' },
  { id: 'h-E', block: 'Block E (Mixed PG)', warden: 'Dr. Kavya Nair', contact: '+91-9001-000-1E', rooms: 40, occupied: 30, facilities: 'Wi-Fi, AC Rooms, Study Hall, Cafeteria', status: 'available' },
];

const MY_HOSTEL = {
  block: 'Block C (Girls)',
  room: 'C-214',
  roommate: 'Aisha Patel',
  warden: 'Ms. Priya Menon',
  contact: '+91-9001-000-1C',
  checkIn: '2026-07-15',
  checkOut: '2027-05-30',
  status: 'confirmed',
  rent: '₹8,500/month',
  messPlan: 'Full Board (Breakfast + Lunch + Dinner)',
};

const COMPLAINTS = [
  { id: 'hc-001', category: 'Maintenance', description: 'Ceiling fan not working in C-214', raised: '2026-10-25', status: 'in_progress' },
  { id: 'hc-002', category: 'Cleanliness', description: 'Common bathroom floor needs cleaning', raised: '2026-10-28', status: 'resolved' },
];

export const StudentTransportHostelView: React.FC = () => {
  const [tab, setTab] = useState<'transport' | 'hostel'>('transport');

  const busCols = [
    { header: 'Route', accessor: 'route' as const, render: (r: any) => <span className="font-bold text-sm text-[#345873]">{r.route}</span> },
    { header: 'Key Stops', accessor: 'stops' as const, render: (r: any) => <span className="text-xs text-gray-500 line-clamp-1">{r.stops}</span> },
    { header: 'Timings', accessor: 'timing' as const, render: (r: any) => <span className="text-xs font-mono text-gray-600">{r.timing}</span> },
    {
      header: 'Seats Available', accessor: 'available' as const,
      render: (r: any) => (
        <span className={`text-xs font-bold ${r.available === 0 ? 'text-red-500' : r.available < 5 ? 'text-amber-500' : 'text-emerald-600'}`}>
          {r.available} / {r.seats}
        </span>
      )
    },
    { header: 'Status', accessor: 'status' as const, render: (r: any) => <StatusBadge status={r.status} /> },
  ];

  const hostelCols = [
    { header: 'Block', accessor: 'block' as const, render: (r: any) => <span className="font-bold text-sm text-[#345873]">{r.block}</span> },
    { header: 'Warden', accessor: 'warden' as const, render: (r: any) => <span className="text-xs text-gray-600">{r.warden}</span> },
    { header: 'Contact', accessor: 'contact' as const, render: (r: any) => <span className="font-mono text-xs text-gray-500">{r.contact}</span> },
    {
      header: 'Occupancy', accessor: 'occupied' as const,
      render: (r: any) => {
        const pct = Math.round((r.occupied / r.rooms) * 100);
        return (
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-slate-100 rounded-full h-1.5 w-16">
              <div className="h-1.5 rounded-full" style={{ width: `${pct}%`, backgroundColor: pct >= 100 ? '#ef4444' : '#10b981' }} />
            </div>
            <span className="text-xs font-bold text-gray-500">{r.occupied}/{r.rooms}</span>
          </div>
        );
      }
    },
    { header: 'Status', accessor: 'status' as const, render: (r: any) => <StatusBadge status={r.status} /> },
  ];

  const complaintCols = [
    { header: 'Category', accessor: 'category' as const, render: (r: any) => <span className="font-bold text-xs text-gray-700">{r.category}</span> },
    { header: 'Description', accessor: 'description' as const, render: (r: any) => <span className="text-xs text-gray-500">{r.description}</span> },
    { header: 'Raised', accessor: 'raised' as const, render: (r: any) => <span className="font-mono text-xs text-gray-400">{r.raised}</span> },
    { header: 'Status', accessor: 'status' as const, render: (r: any) => <StatusBadge status={r.status} /> },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center space-x-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div className="w-12 h-12 rounded-2xl bg-[#F29877]/15 text-[#F29877] flex items-center justify-center">
          {tab === 'transport' ? <Bus size={24} /> : <Home size={24} />}
        </div>
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Transport & Hostel</h1>
          <p className="text-xs text-gray-500 mt-0.5">Campus bus routes, hostel allocations and facility info</p>
        </div>
      </div>

      {/* Demonstration Dataset Banner */}
      <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl flex items-center gap-3 text-xs text-amber-900">
        <span className="px-2 py-0.5 rounded-md bg-amber-200 font-black text-[10px] tracking-wide text-amber-900 shrink-0">
          DEMONSTRATION DATASET
        </span>
        <p>
          Bus shuttle schedules, seat capacity trackers, and hostel room assignments shown below are demonstration datasets for campus logistics.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2">
        {(['transport', 'hostel'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex items-center space-x-2 px-5 py-2 rounded-full text-xs font-bold transition capitalize ${
              tab === t ? 'bg-[#345873] text-white shadow' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            }`}
          >
            {t === 'transport' ? <Bus size={14} /> : <Home size={14} />}
            <span>{t === 'transport' ? 'Campus Transport' : 'Hostel'}</span>
          </button>
        ))}
      </div>

      {tab === 'transport' && (
        <>
          {/* Alert */}
          <div className="flex items-center space-x-3 bg-amber-50 border border-amber-200 rounded-2xl px-4 py-3">
            <AlertTriangle size={16} className="text-amber-500 shrink-0" />
            <p className="text-xs text-amber-700 font-semibold">Route 5 is currently running 15 minutes late due to highway maintenance near East Suburbs junction.</p>
          </div>

          {/* Bus Routes Table */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h3 className="font-extrabold text-sm text-[#345873]">Campus Bus Routes & Seat Availability</h3>
            </div>
            <div className="p-4">
              <DataTable columns={busCols} data={BUS_ROUTES} keyField="id" emptyMessage="No routes available." />
            </div>
          </div>

          {/* Info Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { icon: <MapPin size={18} />, title: 'Bus Pick-up Point', body: 'All campus buses depart from Gate 1 (Main Entrance). Please be at the stop 5 minutes before scheduled time.' },
              { icon: <Clock size={18} />, title: 'Late Night Return', body: 'Special late-night return buses run at 22:00 from City Centre on Fri/Sat. Pre-booking required via the transport office.' },
              { icon: <Phone size={18} />, title: 'Transport Office', body: 'Block A, Ground Floor. Phone: +91-9001-TRANS. Email: transport@campusops.edu. Open 8 AM – 6 PM, Mon–Sat.' },
            ].map((card, i) => (
              <div key={i} className="bg-white rounded-3xl border border-slate-200 shadow-xs p-5">
                <div className="w-9 h-9 rounded-xl bg-[#345873]/10 text-[#345873] flex items-center justify-center mb-3">{card.icon}</div>
                <h4 className="font-bold text-sm text-gray-800 mb-1">{card.title}</h4>
                <p className="text-xs text-gray-500 leading-relaxed">{card.body}</p>
              </div>
            ))}
          </div>
        </>
      )}

      {tab === 'hostel' && (
        <>
          {/* My Allocation Card */}
          <div className="bg-white rounded-3xl border border-[#345873]/30 shadow-xs p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-extrabold text-sm text-[#345873]">My Hostel Allocation</h3>
              <StatusBadge status={MY_HOSTEL.status} />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              {[
                { label: 'Block', value: MY_HOSTEL.block },
                { label: 'Room No.', value: MY_HOSTEL.room },
                { label: 'Roommate', value: MY_HOSTEL.roommate },
                { label: 'Warden', value: MY_HOSTEL.warden },
                { label: 'Check-in', value: MY_HOSTEL.checkIn },
                { label: 'Check-out', value: MY_HOSTEL.checkOut },
                { label: 'Monthly Rent', value: MY_HOSTEL.rent },
                { label: 'Mess Plan', value: MY_HOSTEL.messPlan },
              ].map((item, i) => (
                <div key={i}>
                  <p className="text-gray-400 font-semibold uppercase tracking-wide text-[10px]">{item.label}</p>
                  <p className="font-bold text-gray-700 mt-0.5">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* All Blocks */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h3 className="font-extrabold text-sm text-[#345873]">All Hostel Blocks — Occupancy Overview</h3>
            </div>
            <div className="p-4">
              <DataTable columns={hostelCols} data={HOSTEL_BLOCKS} keyField="id" emptyMessage="No hostel data." />
            </div>
          </div>

          {/* My Complaints */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h3 className="font-extrabold text-sm text-[#345873]">My Hostel Complaints</h3>
            </div>
            <div className="p-4">
              <DataTable columns={complaintCols} data={COMPLAINTS} keyField="id" emptyMessage="No complaints raised." />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

