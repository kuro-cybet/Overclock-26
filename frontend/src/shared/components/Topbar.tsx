import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../core/auth/AuthProvider';
import { Bell, Search, Shield, Eye } from 'lucide-react';
import { NotificationPanel } from './NotificationPanel';
import { tokens } from '../../design-system/tokens';

interface TopbarProps {
  onSearch?: (term: string) => void;
  portalName: string;
}

const PREVIEW_ROLES = [
  { value: 'technician', label: 'Technician' },
  { value: 'faculty', label: 'Faculty' },
  { value: 'student', label: 'Student' },
];

export const Topbar: React.FC<TopbarProps> = ({ onSearch, portalName }) => {
  const { user, isSystemAdmin, impersonate, logout } = useAuth();
  const navigate = useNavigate();
  const [notifOpen, setNotifOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [switching, setSwitching] = useState(false);

  const currentRoleAccent =
    tokens.roleAccents[user?.role as keyof typeof tokens.roleAccents] ||
    tokens.roleAccents.admin;

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    if (onSearch) onSearch(e.target.value);
  };

  const handlePortalChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const role = e.target.value;
    e.target.value = '';
    if (!role) return;

    setSwitching(true);
    try {
      await impersonate(role);
      navigate(`/${role}`, { replace: true });
    } catch (err: any) {
      alert(err?.message || 'Unable to open that portal.');
    } finally {
      setSwitching(false);
    }
  };

  return (
    <>
      <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-30 shadow-xs">
        {/* Left: Portal Title & Search */}
        <div className="flex items-center space-x-6 flex-1 max-w-xl">
          <div className="flex items-center space-x-2">
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: currentRoleAccent.color }}
            />
            <h2 className="text-lg font-extrabold text-[#345873] tracking-tight whitespace-nowrap">
              {portalName}
            </h2>
          </div>

          <div className="relative w-full max-w-md hidden md:block">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search incidents, rooms, assets, work orders..."
              value={searchTerm}
              onChange={handleSearchChange}
              className="w-full pl-10 pr-4 py-2 bg-[#FFF4E9]/50 border border-slate-200 rounded-xl text-xs text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#345873] focus:border-transparent transition"
            />
          </div>
        </div>

        {/* Right: Alerts & User Profile */}
        <div className="flex items-center space-x-3">
          {/* System administrator: portal preview switcher (only while not previewing) */}
          {isSystemAdmin && (
            <div className="hidden md:flex items-center space-x-2 bg-[#EAF3F9] px-3 py-1.5 rounded-xl border border-[#8EB9D8]/60">
              <Eye size={14} className="text-[#345873]" />
              <select
                value=""
                onChange={handlePortalChange}
                disabled={switching}
                title="Open another portal as that role"
                className="bg-transparent text-[11px] font-bold text-[#345873] uppercase tracking-wider focus:outline-none cursor-pointer disabled:opacity-50"
              >
                <option value="">{switching ? 'Opening…' : 'Switch portal…'}</option>
                {PREVIEW_ROLES.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Active Persona Badge */}
          <div className="hidden lg:flex items-center space-x-2 bg-[#FFF4E9] px-3.5 py-1.5 rounded-xl border border-peach/50">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: currentRoleAccent.color }}
            />
            <span className="text-xs font-bold text-[#345873] uppercase tracking-wider">
              {user?.role} {user?.sub_role ? `(${String(user.sub_role).replace(/_/g, ' ')})` : ''}
            </span>
          </div>

          {/* Notification Button */}
          <button
            onClick={() => setNotifOpen(true)}
            className="relative p-2 rounded-xl text-gray-600 hover:bg-[#FFF4E9] transition cursor-pointer"
            title="Open Notification Center"
          >
            <Bell size={20} />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full animate-pulse" />
          </button>

          {/* User badge */}
          <div className="flex items-center space-x-3 pl-3 border-l border-slate-200">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-white text-xs shadow-xs"
              style={{ backgroundColor: currentRoleAccent.color }}
            >
              {user?.name?.slice(0, 2).toUpperCase() || 'OP'}
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-xs font-bold text-[#345873] leading-tight">{user?.name}</p>
              <p className="text-[10px] text-gray-500 capitalize tracking-wide flex items-center">
                <Shield size={10} className="mr-0.5" />
                {user?.sub_role ? String(user.sub_role).replace(/_/g, ' ') : user?.role}
              </p>
            </div>
            <button
              onClick={logout}
              className="text-xs text-rose-500 hover:text-rose-700 font-semibold ml-2 cursor-pointer"
              title="Sign out"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <NotificationPanel isOpen={notifOpen} onClose={() => setNotifOpen(false)} />
    </>
  );
};
