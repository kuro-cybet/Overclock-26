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

const DEFAULT_CHENNAI_ROUTES = [
  {
    id: 'rt-01',
    route_number: 'RT-01',
    route_name: 'Tambaram - Campus Express',
    origin: 'Tambaram West',
    destination: 'Main Academic Campus Gate',
    vehicle_number: 'TN-01-CP-4521',
    driver_name: 'R. Murugan',
    driver_phone: '+91 98401 22341',
    capacity: 52,
    operating_days: 'Mon - Sat',
    status: 'active',
    announcement: 'Morning pickup punctuality strictly maintained. Faculty priority seats reserved in rows 1-3.',
    stops: [
      { id: 'rt-01-1', stop_name: 'Tambaram Sanatorium', sequence_order: 1, pickup_time: '07:15 AM', drop_time: '05:45 PM', landmark: 'Opposite Railway Station' },
      { id: 'rt-01-2', stop_name: 'Chromepet MIT Bridge', sequence_order: 2, pickup_time: '07:25 AM', drop_time: '05:35 PM', landmark: 'Under MIT Flyover' },
      { id: 'rt-01-3', stop_name: 'Pallavaram Signal', sequence_order: 3, pickup_time: '07:35 AM', drop_time: '05:25 PM', landmark: 'GST Road Junction' },
      { id: 'rt-01-4', stop_name: 'Guindy Kathipara', sequence_order: 4, pickup_time: '07:50 AM', drop_time: '05:10 PM', landmark: 'Metro Station Gate 2' },
      { id: 'rt-01-5', stop_name: 'Campus Main Gate', sequence_order: 5, pickup_time: '08:20 AM', drop_time: '04:40 PM', landmark: 'Central Operations Porch' },
    ]
  },
  {
    id: 'rt-02',
    route_number: 'RT-02',
    route_name: 'Velachery - OMR Tech Corridor',
    origin: 'Velachery Vijaya Nagar',
    destination: 'Main Academic Campus Gate',
    vehicle_number: 'TN-02-CP-8832',
    driver_name: 'K. Senthil',
    driver_phone: '+91 98402 33452',
    capacity: 55,
    operating_days: 'Mon - Sat',
    status: 'active',
    announcement: 'Operating via Rajiv Gandhi IT Expressway with reserved bus bay boarding.',
    stops: [
      { id: 'rt-02-1', stop_name: 'Velachery Vijaya Nagar', sequence_order: 1, pickup_time: '07:10 AM', drop_time: '05:50 PM', landmark: 'Near MRTS Foot overbridge' },
      { id: 'rt-02-2', stop_name: 'Thoraipakkam Toll Plaza', sequence_order: 2, pickup_time: '07:25 AM', drop_time: '05:35 PM', landmark: '200ft Radial Road Intersection' },
      { id: 'rt-02-3', stop_name: 'Sholinganallur Junction', sequence_order: 3, pickup_time: '07:40 AM', drop_time: '05:20 PM', landmark: 'TCS Gateway Side' },
      { id: 'rt-02-4', stop_name: 'Siruseri IT Park Gate', sequence_order: 4, pickup_time: '07:55 AM', drop_time: '05:05 PM', landmark: 'SIPCOT Main Arch' },
      { id: 'rt-02-5', stop_name: 'Kelambakkam Junction', sequence_order: 5, pickup_time: '08:05 AM', drop_time: '04:55 PM', landmark: 'Hospital Bus Stop' },
      { id: 'rt-02-6', stop_name: 'Campus Main Gate', sequence_order: 6, pickup_time: '08:25 AM', drop_time: '04:40 PM', landmark: 'Central Operations Porch' },
    ]
  },
  {
    id: 'rt-03',
    route_number: 'RT-03',
    route_name: 'Adyar - ECR Coastal Route',
    origin: 'Adyar Depot',
    destination: 'Main Academic Campus Gate',
    vehicle_number: 'TN-06-CP-1904',
    driver_name: 'S. Prakash',
    driver_phone: '+91 98403 44563',
    capacity: 50,
    operating_days: 'Mon - Sat',
    status: 'active',
    announcement: 'Direct coastal arterial link servicing South Chennai faculty.',
    stops: [
      { id: 'rt-03-1', stop_name: 'Adyar Depot', sequence_order: 1, pickup_time: '07:15 AM', drop_time: '05:45 PM', landmark: 'Near Lattice Bridge Road' },
      { id: 'rt-03-2', stop_name: 'Thiruvanmiyur Bus Stand', sequence_order: 2, pickup_time: '07:25 AM', drop_time: '05:35 PM', landmark: 'Opposite Marundeeswarar Temple' },
      { id: 'rt-03-3', stop_name: 'Palavakkam', sequence_order: 3, pickup_time: '07:35 AM', drop_time: '05:25 PM', landmark: 'ECR Main Road' },
      { id: 'rt-03-4', stop_name: 'Neelankarai Signal', sequence_order: 4, pickup_time: '07:45 AM', drop_time: '05:15 PM', landmark: 'Near Police Station' },
      { id: 'rt-03-5', stop_name: 'Akkarai', sequence_order: 5, pickup_time: '07:55 AM', drop_time: '05:05 PM', landmark: 'ECR-OMR Link Junction' },
      { id: 'rt-03-6', stop_name: 'Campus Main Gate', sequence_order: 6, pickup_time: '08:20 AM', drop_time: '04:40 PM', landmark: 'Central Operations Porch' },
    ]
  },
  {
    id: 'rt-04',
    route_number: 'RT-04',
    route_name: 'Anna Nagar - Western Hub',
    origin: 'Anna Nagar Roundtana',
    destination: 'Main Academic Campus Gate',
    vehicle_number: 'TN-09-CP-6729',
    driver_name: 'M. Jayakumar',
    driver_phone: '+91 98404 55674',
    capacity: 55,
    operating_days: 'Mon - Sat',
    status: 'active',
    announcement: 'High-capacity transit vehicle equipped with emergency first aid.',
    stops: [
      { id: 'rt-04-1', stop_name: 'Anna Nagar Roundtana', sequence_order: 1, pickup_time: '07:05 AM', drop_time: '05:55 PM', landmark: 'Near Metro Entrance' },
      { id: 'rt-04-2', stop_name: 'Koyambedu CMBT', sequence_order: 2, pickup_time: '07:20 AM', drop_time: '05:40 PM', landmark: 'Rohini Theatre Flyover' },
      { id: 'rt-04-3', stop_name: 'Porur Roundabout', sequence_order: 3, pickup_time: '07:40 AM', drop_time: '05:20 PM', landmark: 'Mount-Poonamallee Road' },
      { id: 'rt-04-4', stop_name: 'Poonamallee Bypass', sequence_order: 4, pickup_time: '07:55 AM', drop_time: '05:05 PM', landmark: 'Kumananchavadi Junction' },
      { id: 'rt-04-5', stop_name: 'Campus Main Gate', sequence_order: 5, pickup_time: '08:25 AM', drop_time: '04:40 PM', landmark: 'Central Operations Porch' },
    ]
  },
  {
    id: 'rt-05',
    route_number: 'RT-05',
    route_name: 'Chengalpattu - GST South Line',
    origin: 'Chengalpattu New Bus Stand',
    destination: 'Main Academic Campus Gate',
    vehicle_number: 'TN-19-CP-3108',
    driver_name: 'V. Natarajan',
    driver_phone: '+91 98405 66785',
    capacity: 52,
    operating_days: 'Mon - Sat',
    status: 'active',
    announcement: 'South arterial connector for suburban staff along Grand Southern Trunk road.',
    stops: [
      { id: 'rt-05-1', stop_name: 'Chengalpattu New Bus Stand', sequence_order: 1, pickup_time: '07:00 AM', drop_time: '06:00 PM', landmark: 'Near Railway Station Road' },
      { id: 'rt-05-2', stop_name: 'Maraimalai Nagar Industrial Area', sequence_order: 2, pickup_time: '07:18 AM', drop_time: '05:42 PM', landmark: 'Ford Factory Junction' },
      { id: 'rt-05-3', stop_name: 'Guduvanchery Signal', sequence_order: 3, pickup_time: '07:32 AM', drop_time: '05:28 PM', landmark: 'Near EB Office' },
      { id: 'rt-05-4', stop_name: 'Vandalur Zoo Flyover', sequence_order: 4, pickup_time: '07:45 AM', drop_time: '05:15 PM', landmark: 'Outer Ring Road intersection' },
      { id: 'rt-05-5', stop_name: 'Campus Main Gate', sequence_order: 5, pickup_time: '08:15 AM', drop_time: '04:45 PM', landmark: 'Central Operations Porch' },
    ]
  }
];

const DEFAULT_FACULTY_ALLOCATION = {
  allocation_id: 'alloc-fac-primary',
  status: 'active',
  fee_status: 'institutional_pass',
  academic_year: '2026-2027',
  route: {
    id: 'rt-01',
    route_number: 'RT-01',
    route_name: 'Tambaram - Campus Express',
    vehicle_number: 'TN-01-CP-4521',
    driver_name: 'R. Murugan',
    driver_phone: '+91 98401 22341',
    status: 'active',
  },
  stop: {
    id: 'rt-01-1',
    stop_name: 'Tambaram Sanatorium',
    pickup_time: '07:15 AM',
    drop_time: '05:45 PM',
    landmark: 'Opposite Railway Station',
  }
};

export const FacultyTransportView: React.FC = () => {
  const [routes, setRoutes] = useState<any[]>(DEFAULT_CHENNAI_ROUTES);
  const [allocation, setAllocation] = useState<any>(DEFAULT_FACULTY_ALLOCATION);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [selectedRoute, setSelectedRoute] = useState<any>(DEFAULT_CHENNAI_ROUTES[0]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [routesData, allocData, annData] = await Promise.all([
        api.getTransportRoutes().catch(() => null),
        api.getMyTransportAssignment().catch(() => null),
        api.getTransportAnnouncements().catch(() => null)
      ]);
      const validRoutes = (Array.isArray(routesData) && routesData.length > 0) ? routesData : DEFAULT_CHENNAI_ROUTES;
      setRoutes(validRoutes);
      setAllocation(allocData?.allocation || DEFAULT_FACULTY_ALLOCATION);
      if (Array.isArray(annData) && annData.length > 0) {
        setAnnouncements(annData);
      }
      setSelectedRoute(validRoutes[0]);
    } catch (err) {
      console.error('Failed to load faculty transport data', err);
      setRoutes(DEFAULT_CHENNAI_ROUTES);
      setAllocation(DEFAULT_FACULTY_ALLOCATION);
      setSelectedRoute(DEFAULT_CHENNAI_ROUTES[0]);
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

