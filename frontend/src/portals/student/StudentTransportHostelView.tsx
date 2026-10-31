import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import {
  Bus,
  Home,
  MapPin,
  Clock,
  Phone,
  AlertTriangle,
  Search,
  RefreshCw,
  ShieldCheck,
  Megaphone,
  User
} from 'lucide-react';

const HOSTEL_BLOCKS = [
  { id: 'h-A', block: 'Cauvery Block (Men)', warden: 'Dr. K. Ramanathan', contact: '+91 94441 12345', rooms: 120, occupied: 114, facilities: 'Wi-Fi, High-Speed LAN, Laundry, 24h Generator', status: 'available' },
  { id: 'h-B', block: 'Krishna Block (Men)', warden: 'Prof. M. Selvam', contact: '+91 94442 23456', rooms: 120, occupied: 120, facilities: 'Wi-Fi, Study Hall, Solar Hot Water, CCTV', status: 'full' },
  { id: 'h-C', block: 'Vaigai Block (Women)', warden: 'Dr. S. Meenakshi', contact: '+91 94443 34567', rooms: 100, occupied: 92, facilities: 'Biometric Access, Reading Room, 24h Guard, Medical Bay', status: 'available' },
  { id: 'h-D', block: 'Bhavani Block (Women)', warden: 'Ms. R. Radhika', contact: '+91 94444 45678', rooms: 100, occupied: 100, facilities: 'Wi-Fi, Gymnasium, Laundry Facility, Cafeteria', status: 'full' },
  { id: 'h-E', block: 'Palar Block (PG & Research)', warden: 'Dr. T. Venkataraman', contact: '+91 94445 56789', rooms: 60, occupied: 48, facilities: 'AC Accommodations, High-Bandwidth Gigabit LAN, Quiet Zone', status: 'available' },
];

const MY_HOSTEL = {
  block: 'Vaigai Block (Women)',
  room: 'V-304',
  roommate: 'Divya Sundaram',
  warden: 'Dr. S. Meenakshi',
  contact: '+91 94443 34567',
  checkIn: '2026-07-15',
  checkOut: '2027-05-30',
  status: 'confirmed',
  rent: '₹9,500/month',
  messPlan: 'South Indian Veg & Non-Veg Multi-Cuisine',
};

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
    announcement: 'Morning pickup punctuality strictly maintained. Please board 5 minutes before scheduled departure.',
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
    announcement: 'Direct coastal arterial link servicing South Chennai scholars.',
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
    announcement: 'South arterial connector for suburban scholars along Grand Southern Trunk road.',
    stops: [
      { id: 'rt-05-1', stop_name: 'Chengalpattu New Bus Stand', sequence_order: 1, pickup_time: '07:00 AM', drop_time: '06:00 PM', landmark: 'Near Railway Station Road' },
      { id: 'rt-05-2', stop_name: 'Maraimalai Nagar Industrial Area', sequence_order: 2, pickup_time: '07:18 AM', drop_time: '05:42 PM', landmark: 'Ford Factory Junction' },
      { id: 'rt-05-3', stop_name: 'Guduvanchery Signal', sequence_order: 3, pickup_time: '07:32 AM', drop_time: '05:28 PM', landmark: 'Near EB Office' },
      { id: 'rt-05-4', stop_name: 'Vandalur Zoo Flyover', sequence_order: 4, pickup_time: '07:45 AM', drop_time: '05:15 PM', landmark: 'Outer Ring Road intersection' },
      { id: 'rt-05-5', stop_name: 'Campus Main Gate', sequence_order: 5, pickup_time: '08:15 AM', drop_time: '04:45 PM', landmark: 'Central Operations Porch' },
    ]
  }
];

const DEFAULT_ALLOCATION = {
  allocation_id: 'alloc-stu-primary',
  status: 'active',
  fee_status: 'paid',
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

export const StudentTransportHostelView: React.FC = () => {
  const [tab, setTab] = useState<'transport' | 'hostel'>('transport');
  const [routes, setRoutes] = useState<any[]>(DEFAULT_CHENNAI_ROUTES);
  const [allocation, setAllocation] = useState<any>(DEFAULT_ALLOCATION);
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
      setAllocation(allocData?.allocation || DEFAULT_ALLOCATION);
      if (Array.isArray(annData) && annData.length > 0) {
        setAnnouncements(annData);
      }
      setSelectedRoute(validRoutes[0]);
    } catch (err) {
      console.error('Failed to load transport data', err);
      setRoutes(DEFAULT_CHENNAI_ROUTES);
      setAllocation(DEFAULT_ALLOCATION);
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
          <div className="w-12 h-12 rounded-2xl bg-[#F29877]/15 text-[#F29877] flex items-center justify-center shrink-0">
            {tab === 'transport' ? <Bus size={24} /> : <Home size={24} />}
          </div>
          <div>
            <h1 className="text-2xl font-black text-[#345873]">Campus Transport & Residential Services</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Chennai metropolitan bus routes, scheduled boarding stops, transport passes, and hostel blocks.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex bg-slate-100 p-1 rounded-2xl border border-slate-200">
            <button
              onClick={() => setTab('transport')}
              className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                tab === 'transport' ? 'bg-[#345873] text-white shadow-xs' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Bus size={14} />
              <span>Chennai Transit Routes</span>
            </button>
            <button
              onClick={() => setTab('hostel')}
              className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                tab === 'hostel' ? 'bg-[#345873] text-white shadow-xs' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Home size={14} />
              <span>Campus Hostels</span>
            </button>
          </div>

          <button
            onClick={loadData}
            className="p-2.5 bg-white border border-slate-200 text-gray-600 rounded-2xl hover:bg-gray-50 transition cursor-pointer shadow-xs"
            title="Refresh"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* TAB 1: TRANSPORT */}
      {tab === 'transport' && (
        <div className="space-y-6">
          {/* Active Announcements */}
          {announcements.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-3xl p-4 flex items-start space-x-3 text-amber-900">
              <Megaphone size={20} className="text-amber-700 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-extrabold text-xs uppercase tracking-wider">{announcements[0].title}</h4>
                <p className="text-xs text-amber-800 mt-0.5">{announcements[0].message}</p>
              </div>
            </div>
          )}

          {/* MY TRANSPORT ALLOCATION CARD */}
          {allocation && (
            <div className="bg-gradient-to-r from-[#287D70] to-[#345873] rounded-3xl p-6 text-white shadow-md">
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-[#FFD6BA] block mb-1">
                My Official Transport Allocation • Term 2026-2027
              </span>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
                <div>
                  <h3 className="text-base font-extrabold">{allocation.route?.route_name}</h3>
                  <span className="font-mono text-xs text-emerald-200 font-bold block mt-0.5">
                    Route Code: {allocation.route?.route_number} • Bus: {allocation.route?.vehicle_number}
                  </span>
                  <p className="text-xs text-slate-200 mt-1">
                    Driver: {allocation.route?.driver_name} ({allocation.route?.driver_phone})
                  </p>
                </div>

                <div className="p-3 bg-white/10 rounded-2xl border border-white/15">
                  <span className="text-[10px] uppercase font-bold text-slate-300 block">Designated Boarding Stop</span>
                  <span className="font-extrabold text-sm text-white block mt-0.5">{allocation.stop?.stop_name}</span>
                  <span className="text-xs text-slate-200 font-mono">
                    Pickup: {allocation.stop?.pickup_time} • Drop: {allocation.stop?.drop_time}
                  </span>
                </div>

                <div className="flex flex-col justify-center items-start md:items-end">
                  <span className="px-3 py-1 bg-emerald-400 text-emerald-950 rounded-full font-black text-xs uppercase tracking-wider">
                    {allocation.status} Pass • {allocation.fee_status}
                  </span>
                  <span className="text-[10px] text-slate-300 mt-1.5">Show QR code or digital ID to coach attender</span>
                </div>
              </div>
            </div>
          )}

          {/* Search bar */}
          <div className="relative max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search Chennai stops or hubs (e.g. Tambaram, Guindy, Velachery, Porur)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-2xl text-xs text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#345873] shadow-xs transition"
            />
          </div>

          {/* Routes Grid & Stops Expansion */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Route List */}
            <div className="lg:col-span-1 space-y-3">
              <h2 className="text-sm font-extrabold text-[#345873] uppercase tracking-wider">
                Available Campus Bus Routes ({filteredRoutes.length})
              </h2>
              {filteredRoutes.map((r) => (
                <div
                  key={r.id}
                  onClick={() => setSelectedRoute(r)}
                  className={`p-4 rounded-3xl border transition cursor-pointer shadow-xs ${
                    selectedRoute?.id === r.id
                      ? 'bg-[#FFF4E9] border-[#F29877] ring-1 ring-[#F29877]'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono font-bold text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700">
                      {r.route_number}
                    </span>
                    <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full capitalize">
                      {r.status}
                    </span>
                  </div>
                  <h3 className="font-black text-[#345873] text-sm leading-tight">{r.route_name}</h3>
                  <p className="text-xs text-gray-500 mt-1 line-clamp-1">
                    {r.origin} ➔ {r.destination}
                  </p>
                  <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-gray-500">
                    <span>{r.operating_days}</span>
                    <span>{r.capacity} Seats • {r.stops?.length || 0} Stops</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Selected Route Detailed Stop Timings */}
            <div className="lg:col-span-2">
              {selectedRoute ? (
                <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-black text-sm text-[#345873] bg-[#FFF4E9] px-2.5 py-1 rounded-xl">
                          {selectedRoute.route_number}
                        </span>
                        <h2 className="text-lg font-black text-[#345873]">{selectedRoute.route_name}</h2>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Vehicle No: <span className="font-mono font-bold text-gray-800">{selectedRoute.vehicle_number}</span> • Driver: <span className="font-bold text-gray-800">{selectedRoute.driver_name}</span> ({selectedRoute.driver_phone})
                      </p>
                    </div>

                    <div className="text-right">
                      <span className="text-xs font-bold text-slate-500 block">Scheduled Bus Line</span>
                      <span className="text-[11px] text-emerald-600 font-bold uppercase tracking-wider">Fixed Punctual Service</span>
                    </div>
                  </div>

                  {selectedRoute.announcement && (
                    <div className="p-3.5 bg-blue-50/70 border border-blue-100 rounded-2xl text-xs text-blue-900 font-medium">
                      {selectedRoute.announcement}
                    </div>
                  )}

                  {/* Stops Sequence Flow */}
                  <div className="space-y-4">
                    <h3 className="text-xs font-extrabold uppercase tracking-wider text-gray-400">
                      Sequential Stop Schedule & Pick-up/Drop Timings
                    </h3>

                    <div className="space-y-3 relative before:absolute before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-200">
                      {(selectedRoute.stops || []).map((stop: any, idx: number) => (
                        <div key={stop.id || idx} className="relative flex items-start space-x-4 pl-1">
                          <div className="w-6 h-6 rounded-full bg-[#345873] text-white flex items-center justify-center text-[10px] font-black shrink-0 z-10 shadow-xs">
                            {stop.sequence_order}
                          </div>
                          <div className="flex-1 bg-slate-50 p-3.5 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <div>
                              <span className="font-extrabold text-xs text-gray-800 block">{stop.stop_name}</span>
                              {stop.landmark && (
                                <span className="text-[11px] text-gray-400">{stop.landmark}</span>
                              )}
                            </div>
                            <div className="flex items-center space-x-3 text-xs font-mono font-bold text-[#345873] shrink-0">
                              <span className="bg-white px-2.5 py-1 rounded-xl border border-slate-200">
                                AM: {stop.pickup_time}
                              </span>
                              <span className="bg-white px-2.5 py-1 rounded-xl border border-slate-200">
                                PM: {stop.drop_time}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-3xl p-10 border border-slate-200 text-center text-gray-400 text-sm">
                  Select a route from the list to view its complete Chennai stop schedule.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: HOSTEL */}
      {tab === 'hostel' && (
        <div className="space-y-6">
          {/* Student's Current Hostel Allocation */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
            <h2 className="text-base font-extrabold text-[#345873] mb-4">My Residential Allocation</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div className="p-4 bg-slate-50 rounded-2xl">
                <span className="text-gray-400 font-bold block">Assigned Hostel</span>
                <span className="text-sm font-extrabold text-[#345873] mt-0.5 block">{MY_HOSTEL.block}</span>
                <span className="text-gray-500 text-[11px]">Room {MY_HOSTEL.room}</span>
              </div>
              <div className="p-4 bg-slate-50 rounded-2xl">
                <span className="text-gray-400 font-bold block">Roommate</span>
                <span className="text-sm font-extrabold text-gray-800 mt-0.5 block">{MY_HOSTEL.roommate}</span>
                <span className="text-gray-500 text-[11px]">Enrolled Student</span>
              </div>
              <div className="p-4 bg-slate-50 rounded-2xl">
                <span className="text-gray-400 font-bold block">Resident Warden</span>
                <span className="text-sm font-extrabold text-gray-800 mt-0.5 block">{MY_HOSTEL.warden}</span>
                <span className="text-gray-500 font-mono text-[11px]">{MY_HOSTEL.contact}</span>
              </div>
              <div className="p-4 bg-slate-50 rounded-2xl">
                <span className="text-gray-400 font-bold block">Mess & Boarding</span>
                <span className="text-sm font-extrabold text-emerald-700 mt-0.5 block">{MY_HOSTEL.rent}</span>
                <span className="text-gray-500 text-[11px]">{MY_HOSTEL.messPlan}</span>
              </div>
            </div>
          </div>

          {/* Campus Hostels Table */}
          <div className="space-y-3">
            <h2 className="text-base font-extrabold text-[#345873]">Campus Residential Hostels</h2>
            <DataTable
              columns={[
                {
                  header: 'Hostel Block',
                  accessor: 'block' as const,
                  render: (r: any) => <span className="font-extrabold text-sm text-[#345873]">{r.block}</span>
                },
                {
                  header: 'Resident Warden',
                  accessor: 'warden' as const,
                  render: (r: any) => (
                    <div>
                      <span className="font-bold text-xs text-gray-800 block">{r.warden}</span>
                      <span className="font-mono text-[10px] text-gray-400">{r.contact}</span>
                    </div>
                  )
                },
                {
                  header: 'Facilities & Security',
                  accessor: 'facilities' as const,
                  render: (r: any) => <span className="text-xs text-gray-500">{r.facilities}</span>
                },
                {
                  header: 'Occupancy',
                  render: (r: any) => {
                    const pct = Math.round((r.occupied / r.rooms) * 100);
                    return (
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div className={`h-1.5 rounded-full ${pct >= 100 ? 'bg-red-500' : 'bg-emerald-500'}`} style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-xs font-mono font-bold text-gray-600">{r.occupied}/{r.rooms}</span>
                      </div>
                    );
                  }
                },
                {
                  header: 'Status',
                  accessor: 'status' as const,
                  render: (r: any) => <StatusBadge status={r.status} />
                }
              ]}
              data={HOSTEL_BLOCKS}
              keyField="id"
            />
          </div>
        </div>
      )}
    </div>
  );
};
