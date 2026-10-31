import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import {
  Bus,
  PlusCircle,
  RefreshCw,
  Search,
  CheckCircle,
  AlertCircle,
  MapPin,
  Clock,
  Phone,
  X
} from 'lucide-react';

export const AdminTransportManagementView: React.FC = () => {
  const [routes, setRoutes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedRoute, setSelectedRoute] = useState<any>(null);

  // New Route Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [routeNum, setRouteNum] = useState('');
  const [routeName, setRouteName] = useState('');
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('Campus Main Gate');
  const [vehicleNum, setVehicleNum] = useState('');
  const [driverName, setDriverName] = useState('');
  const [driverPhone, setDriverPhone] = useState('');
  const [capacity, setCapacity] = useState(50);
  const [status, setStatus] = useState('active');
  const [announcement, setAnnouncement] = useState('');

  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadRoutes();
  }, []);

  const loadRoutes = async () => {
    setLoading(true);
    try {
      const data = await api.getTransportRoutes();
      setRoutes(data);
      if (data.length > 0 && !selectedRoute) {
        setSelectedRoute(data[0]);
      }
    } catch (err) {
      console.error('Failed to load transport management routes', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveRoute = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);
    setSubmitting(true);

    try {
      await api.saveTransportRoute({
        route_number: routeNum,
        route_name: routeName,
        origin,
        destination,
        vehicle_number: vehicleNum,
        driver_name: driverName,
        driver_phone: driverPhone,
        capacity,
        operating_days: 'Mon-Sat',
        status,
        announcement: announcement || null,
        is_published: true
      });

      setFormSuccess('Campus transit route saved successfully!');
      await loadRoutes();
      setTimeout(() => {
        setModalOpen(false);
        setFormSuccess(null);
        setRouteNum('');
        setRouteName('');
        setOrigin('');
        setVehicleNum('');
        setDriverName('');
        setDriverPhone('');
      }, 1500);
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save transport route.');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredRoutes = routes.filter((r) =>
    r.route_number.toLowerCase().includes(search.toLowerCase()) ||
    r.route_name.toLowerCase().includes(search.toLowerCase()) ||
    r.origin.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Campus Transportation & Transit Control</h1>
          <p className="text-xs text-gray-500 mt-1">
            Chennai metropolitan bus routes, fleet vehicle allocations, driver duty records, and stop sequence schedules.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center space-x-1.5 px-4 py-2.5 bg-[#345873] hover:bg-[#253f54] text-white rounded-2xl text-xs font-bold transition shadow-xs cursor-pointer"
          >
            <PlusCircle size={16} />
            <span>Add Route</span>
          </button>
          <button
            onClick={loadRoutes}
            className="p-2.5 bg-white border border-slate-200 text-gray-600 rounded-2xl hover:bg-gray-50 transition cursor-pointer shadow-xs"
            title="Refresh"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Routes Overview Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
            <input
              type="text"
              placeholder="Search routes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
            />
          </div>

          <div className="space-y-2">
            {filteredRoutes.map((r) => (
              <div
                key={r.id}
                onClick={() => setSelectedRoute(r)}
                className={`p-3.5 rounded-2xl border transition cursor-pointer ${
                  selectedRoute?.id === r.id
                    ? 'bg-[#FFF4E9] border-[#F29877] ring-1 ring-[#F29877]'
                    : 'bg-white border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                    {r.route_number}
                  </span>
                  <span className="text-[10px] font-bold text-emerald-600 uppercase bg-emerald-50 px-2 py-0.5 rounded-full">
                    {r.status}
                  </span>
                </div>
                <h4 className="font-extrabold text-[#345873] text-xs">{r.route_name}</h4>
                <p className="text-[11px] text-gray-500 mt-0.5">{r.origin} ➔ {r.destination}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Route Details */}
        <div className="lg:col-span-2">
          {selectedRoute ? (
            <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-base font-extrabold text-[#345873]">
                    {selectedRoute.route_number} — {selectedRoute.route_name}
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Vehicle: {selectedRoute.vehicle_number} • Capacity: {selectedRoute.capacity} Seats
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold text-gray-700 block">{selectedRoute.driver_name}</span>
                  <span className="text-[11px] font-mono text-gray-400">{selectedRoute.driver_phone}</span>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-extrabold uppercase text-gray-400 mb-3 tracking-wider">
                  Sequential Stops & Designated Landmarks
                </h4>
                <div className="space-y-2">
                  {(selectedRoute.stops || []).map((stop: any) => (
                    <div
                      key={stop.id}
                      className="p-3 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="w-5 h-5 rounded-full bg-[#345873] text-white flex items-center justify-center font-bold text-[10px]">
                          {stop.sequence_order}
                        </span>
                        <div>
                          <span className="font-bold text-gray-800 block">{stop.stop_name}</span>
                          <span className="text-[10px] text-gray-400">{stop.landmark || 'Designated Stop'}</span>
                        </div>
                      </div>
                      <div className="font-mono text-[#345873] font-bold text-xs">
                        AM: {stop.pickup_time} • PM: {stop.drop_time}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-3xl p-8 border border-slate-200 text-center text-gray-400 text-sm">
              Select a route to view its vehicle details and stops.
            </div>
          )}
        </div>
      </div>

      {/* ADD ROUTE MODAL */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-extrabold text-[#345873]">Add Chennai Transit Route</h3>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-gray-600 cursor-pointer">
                <X size={18} />
              </button>
            </div>

            {formError && (
              <div className="mt-3 p-3 bg-red-50 text-red-700 text-xs rounded-xl border border-red-200 font-semibold flex items-center">
                <AlertCircle size={16} className="mr-2 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            {formSuccess && (
              <div className="mt-3 p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl border border-emerald-200 font-semibold flex items-center">
                <CheckCircle size={16} className="mr-2 shrink-0" />
                <span>{formSuccess}</span>
              </div>
            )}

            <form onSubmit={handleSaveRoute} className="space-y-3 mt-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Route Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. RT-06"
                    value={routeNum}
                    onChange={(e) => setRouteNum(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Capacity</label>
                  <input
                    type="number"
                    min="10"
                    required
                    value={capacity}
                    onChange={(e) => setCapacity(parseInt(e.target.value) || 50)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Route Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Porur - Campus Shuttle"
                  value={routeName}
                  onChange={(e) => setRouteName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Origin Point</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Porur Junction"
                    value={origin}
                    onChange={(e) => setOrigin(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Destination</label>
                  <input
                    type="text"
                    required
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Vehicle Plate No</label>
                  <input
                    type="text"
                    required
                    placeholder="TN-01-CP-XXXX"
                    value={vehicleNum}
                    onChange={(e) => setVehicleNum(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Driver Phone</label>
                  <input
                    type="text"
                    required
                    placeholder="+91 9840X XXXXX"
                    value={driverPhone}
                    onChange={(e) => setDriverPhone(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Driver Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. K. Sundaram"
                  value={driverName}
                  onChange={(e) => setDriverName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div className="pt-3 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-gray-500 hover:bg-gray-100 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl bg-[#345873] text-white text-xs font-bold hover:bg-[#253f54] transition cursor-pointer disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : 'Add Route'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

