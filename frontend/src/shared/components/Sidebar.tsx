import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../core/auth/AuthProvider';
import {
  LayoutDashboard,
  AlertTriangle,
  Building2,
  Wrench,
  Boxes,
  FileCheck2,
  Users,
  FlaskConical,
  BarChart3,
  Calendar,
  ClipboardList,
  CheckCircle2,
  MessageSquarePlus,
  Megaphone,
  Layers,
  Sparkles,
  ChevronRight,
  Bus,
  GraduationCap,
  BookOpen,
  X
} from 'lucide-react';

interface NavLinkItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  highlight?: boolean;
}

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen = false, onCloseMobile }) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const role = user?.role || 'admin';

  // Navigation menus customized per role and admin sub-role
  const allAdminLinks: (NavLinkItem & { allowedSubRoles?: string[] })[] = [
    { to: '/admin', label: 'Operations Centre', icon: <LayoutDashboard size={22} /> },
    { to: '/admin/intelligence', label: 'Operational Intelligence', icon: <Sparkles size={22} />, highlight: true, allowedSubRoles: ['system_admin', 'department_manager', 'facilities_admin'] },
    { to: '/admin/predictive', label: 'Predictive Maintenance', icon: <Layers size={22} />, allowedSubRoles: ['system_admin', 'facilities_admin'] },
    { to: '/admin/incidents', label: 'Incidents & Triage', icon: <AlertTriangle size={22} />, allowedSubRoles: ['system_admin', 'department_manager', 'facilities_admin'] },
    { to: '/admin/campus', label: 'Campus & Facilities', icon: <Building2 size={22} />, allowedSubRoles: ['system_admin', 'facilities_admin'] },
    { to: '/admin/timetable', label: 'Timetable & Attendance', icon: <Calendar size={22} />, allowedSubRoles: ['system_admin', 'department_manager', 'facilities_admin'] },
    { to: '/admin/transport', label: 'Transport Management', icon: <Bus size={22} />, allowedSubRoles: ['system_admin', 'facilities_admin'] },
    { to: '/admin/work-orders', label: 'Work Orders', icon: <Wrench size={22} />, allowedSubRoles: ['system_admin', 'facilities_admin'] },
    { to: '/admin/inventory', label: 'Inventory & Parts', icon: <Boxes size={22} />, allowedSubRoles: ['system_admin', 'procurement_approver'] },
    { to: '/admin/approvals', label: 'Pending Approvals', icon: <FileCheck2 size={22} />, allowedSubRoles: ['system_admin', 'department_manager', 'procurement_approver'] },
    { to: '/admin/staff', label: 'Staff & Skills Matrix', icon: <Users size={22} />, allowedSubRoles: ['system_admin'] },
    { to: '/admin/simulator', label: 'Scenario Simulator', icon: <FlaskConical size={22} />, highlight: true, allowedSubRoles: ['system_admin'] },
    { to: '/admin/analytics', label: 'Analytics & SLA', icon: <BarChart3 size={22} />, allowedSubRoles: ['system_admin', 'department_manager'] },
  ];

  // Scoped admin links: only system_admin gets all admin powers, other admin roles get only their own domain
  const adminLinks = allAdminLinks.filter((link) => {
    if (!link.allowedSubRoles) return true;
    const subRole = user?.sub_role || 'system_admin';
    if (subRole === 'system_admin') return true;
    return link.allowedSubRoles.includes(subRole);
  });

  const technicianLinks: NavLinkItem[] = [
    { to: '/technician', label: 'Technician Hub', icon: <LayoutDashboard size={22} /> },
    { to: '/technician/tasks', label: 'My Work Orders', icon: <Wrench size={22} /> },
    { to: '/technician/schedule', label: "Today's Schedule", icon: <Calendar size={22} /> },
    { to: '/technician/readiness', label: 'Room Readiness Checks', icon: <CheckCircle2 size={22} /> },
    { to: '/technician/parts', label: 'Parts Requisitions', icon: <Boxes size={22} /> },
  ];

  const facultyLinks: NavLinkItem[] = [
    { to: '/faculty', label: 'Academic Workspace', icon: <LayoutDashboard size={22} /> },
    { to: '/faculty/timetable', label: 'Teaching Schedule & Attendance', icon: <Calendar size={22} /> },
    { to: '/faculty/transport', label: 'Faculty Transport', icon: <Bus size={22} /> },
    { to: '/faculty/requests', label: 'My Support Requests', icon: <ClipboardList size={22} /> },
    { to: '/faculty/exam-support', label: 'Exam & Lab Support', icon: <Sparkles size={22} /> },
    { to: '/faculty/notices', label: 'Campus Notices', icon: <Megaphone size={22} /> },
  ];

  const studentLinks: NavLinkItem[] = [
    { to: '/student', label: 'Student Workspace', icon: <LayoutDashboard size={22} /> },
    { to: '/student/timetable', label: 'My Timetable', icon: <Calendar size={22} /> },
    { to: '/student/attendance', label: 'My Attendance', icon: <CheckCircle2 size={22} /> },
    { to: '/student/quick-report', label: 'Submit Issue Report', icon: <MessageSquarePlus size={22} /> },
    { to: '/student/requests', label: 'My Requests & Status', icon: <ClipboardList size={22} /> },
    { to: '/student/transport-hostel', label: 'Transport & Hostel', icon: <Bus size={22} /> },
    { to: '/student/notice-board', label: 'Notice Board', icon: <Megaphone size={22} /> },
    { to: '/student/admissions', label: 'Admissions', icon: <GraduationCap size={22} /> },
    { to: '/student/my-learning', label: 'My Learning', icon: <BookOpen size={22} /> },
  ];

  const links =
    role === 'admin'
      ? adminLinks
      : role === 'technician'
      ? technicianLinks
      : role === 'faculty'
      ? facultyLinks
      : studentLinks;

  const handleLinkClick = () => {
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs md:hidden"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container: Drawer on mobile (< 768px), static on desktop */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-[#1f2937] text-white flex flex-col justify-between border-r border-gray-800 transition-transform duration-300 ease-in-out md:static md:translate-x-0 ${
          mobileOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
        } shrink-0 min-h-screen overflow-y-auto`}
      >
        <div>
          {/* Brand Header */}
          <div className="h-20 flex items-center justify-between px-6 border-b border-gray-800">
            <div
              className="flex items-center space-x-3.5 cursor-pointer"
              onClick={() => {
                navigate(`/${role}`);
                handleLinkClick();
              }}
            >
              <div className="w-10 h-10 rounded-xl bg-[#F29877] flex items-center justify-center font-black text-white text-lg shadow-sm">
                CO
              </div>
              <div>
                <h1 className="font-extrabold text-lg tracking-wider text-white">
                  CAMPUS<span className="text-[#F29877]">OPS</span>
                </h1>
                <span className="text-xs text-[#8EB9D8] tracking-widest uppercase block font-bold">
                  One Unified Engine
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={onCloseMobile}
              className="md:hidden p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
              title="Close Navigation"
              aria-label="Close Navigation"
            >
              <X size={20} />
            </button>
          </div>



          {/* Navigation Items */}
          <nav className="p-4 space-y-2">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === `/${role}`}
                onClick={handleLinkClick}
                className={({ isActive }) =>
                  `flex items-center justify-between px-4 py-3 rounded-2xl text-base font-bold transition tracking-tight min-h-[44px] ${
                    isActive
                      ? 'bg-[#FFD6BA] text-[#1f2937] shadow-sm'
                      : 'text-slate-200 hover:bg-white/10 hover:text-white'
                  } ${link.highlight ? 'ring-1 ring-[#F29877]/60' : ''}`
                }
              >
                <div className="flex items-center space-x-3.5 truncate">
                  <span className="shrink-0">{link.icon}</span>
                  <span className="truncate">{link.label}</span>
                </div>
                <ChevronRight size={18} className="opacity-60 shrink-0 ml-2" />
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Footer information */}
        <div className="p-5 border-t border-gray-800 text-xs text-slate-400 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-semibold">Engine Status</span>
            <span className="flex items-center text-emerald-400 font-bold">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 mr-2 animate-pulse" />
              Connected
            </span>
          </div>
          <p className="text-xs text-slate-500">Database: SQLite (campusops.db)</p>
        </div>
      </aside>
    </>
  );
};
