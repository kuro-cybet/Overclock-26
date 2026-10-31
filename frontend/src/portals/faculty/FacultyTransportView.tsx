import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import {
  Bus,
  MapPin,
  Clock,
  Phone,
  RefreshCw,
  Search,
  Megaphone,
  ShieldCheck
} from 'lucide-react';

export const FacultyTransportView: React.FC = () => {
  const [routes, setRoutes] = useState<any[]>([]);
  const [allocation, setAllocation] = useState<any>(null);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [selectedRoute, setSelectedRoute] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [routesData, allocData, annData] = await Promise.all([
        api.getTransportRoutes(),
        api.getMyTransportAssignment(),
        api.getTransportAnnouncements()
      ]);
      setRoutes(routesData);
      setAllocation(allocData?.allocation || null);
      setAnnouncements(annData);
      if (routesData.length > 0 && !selectedRoute) {
        setSelectedRoute(routesData[0]);
      }
    } catch (err) {
      console.error('Failed to load faculty transport data', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredRoutes = routes.filter((r) => {
    const s = search.toLowerCase();
    return (
      r.route_number.toLowerCase().includes(s) ||
      r.route_name.toLowerCase().includes(s) ||
      r.origin.toLowerCase().includes(s) ||
      (r.stops && r.stops.some((st: any) => st.stop_name.toLowerCase().includes(s)))
    );
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-[#8EB9D8]/20 text-[#1f4a6e] flex items-center justify-center shrink-0">
            <Bus size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-[#345873]">Faculty Shuttle & Transit Services</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Dedicated staff commute routes, metropolitan Chennai boarding points, and transit alerts.
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          className="p-2.5 bg-white border border-slate-200 text-gray-600 rounded-2xl hover:bg-gray-50 transition cursor-pointer self-start sm:self-auto shadow-xs"
          title="Refresh Routes"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Advisory Announcement */}
      {announcements.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-3xl p-4 flex items-start space-x-3 text-blue-900">
          <Megaphone size={20} className="text-blue-700 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-extrabold text-xs uppercase tracking-wider">{announcements[0].title}</h4>
            <p className="text-xs text-blue-800 mt-0.5">{announcements[0].message}</p>
          </div>
        </div>
      )}

      {/* Faculty Allocated Route Card */}
      {allocation && (
        <div className="bg-gradient-to-r from-[#345873] to-[#1f4a6e] rounded-3xl p-6 text-white shadow-md">
          <span className="text-[10px] font-extrabold uppercase tracking-widest text-[#FFD6BA] block mb-1">
            Faculty Dedicated Transit Pass • Academic Year 2026-2027
          </span>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
            <div>
              <h3 className="text-base font-extrabold">{allocation.route?.route_name}</h3>
              <span className="font-mono text-xs text-blue-200 font-bold block mt-0.5">
                Route: {allocation.route?.route_number} • Bus: {allocation.route?.vehicle_number}
              </span>
              <p className="text-xs text-slate-200 mt-1">
                Driver: {allocation.route?.driver_name} ({allocation.route?.driver_phone})
              </p>
            </div>

            <div className="p-3 bg-white/10 rounded-2xl border border-white/15">
              <span className="text-[10px] uppercase font-bold text-slate-300 block">Staff Boarding Stop</span>
              <span className="font-extrabold text-sm text-white block mt-0.5">{allocation.stop?.stop_name}</span>
              <span className="text-xs text-slate-200 font-mono">
                AM: {allocation.stop?.pickup_time} • PM: {allocation.stop?.drop_time}
              </span>
            </div>

            <div className="flex flex-col justify-center items-start md:items-end">
              <span className="px-3 py-1 bg-amber-400 text-amber-950 rounded-full font-black text-xs uppercase tracking-wider">
                Staff Allocation Verified
              </span>
              <span className="text-[10px] text-slate-300 mt-1.5">Direct express shuttle to Faculty Wing</span>
            </div>
          </div>
        </div>
      )}

      {/* Search and Route Detail */}
      <div className="relative max-w-md">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
        <input
          type="text"
          placeholder="Search Chennai faculty pickup points (e.g. Adyar, Tambaram, Guindy, Anna Nagar)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-2xl text-xs text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#345873] shadow-xs transition"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Route List */}
        <div className="lg:col-span-1 space-y-3">
          <h2 className="text-sm font-extrabold text-[#345873] uppercase tracking-wider">
            All Routes ({filteredRoutes.length})
          </h2>
          {filteredRoutes.map((r) => (
            <div
              key={r.id}
              onClick={() => setSelectedRoute(r)}
              className={`p-4 rounded-3xl border transition cursor-pointer shadow-xs ${
                selectedRoute?.id === r.id
                  ? 'bg-[#EAF3F9] border-[#8EB9D8] ring-1 ring-[#8EB9D8]'
                  : 'bg-white border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono font-bold text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700">
                  {r.route_number}
                </span>
                <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full capitalize">
                  {r.status}
                </span>
              </div>
              <h3 className="font-black text-[#345873] text-sm">{r.route_name}</h3>
              <p className="text-xs text-gray-500 mt-0.5">{r.origin} ➔ {r.destination}</p>
            </div>
          ))}
        </div>

        {/* Selected Route Stops */}
        <div className="lg:col-span-2">
          {selectedRoute && (
            <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-base font-extrabold text-[#345873]">{selectedRoute.route_name}</h3>
                  <p className="text-xs text-gray-500">
                    Vehicle: {selectedRoute.vehicle_number} • Driver: {selectedRoute.driver_name} ({selectedRoute.driver_phone})
                  </p>
                </div>
                <span className="font-mono font-bold text-xs bg-slate-100 px-3 py-1 rounded-xl text-slate-700">
                  {selectedRoute.operating_days}
                </span>
              </div>

              <div className="space-y-3">
                {(selectedRoute.stops || []).map((stop: any) => (
                  <div key={stop.id} className="p-3 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-extrabold text-gray-800">{stop.sequence_order}. {stop.stop_name}</span>
                      {stop.landmark && <p className="text-[11px] text-gray-400 mt-0.5">{stop.landmark}</p>}
                    </div>
                    <div className="font-mono text-[#345873] font-bold">
                      <span>Pickup: {stop.pickup_time} • Return: {stop.drop_time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

