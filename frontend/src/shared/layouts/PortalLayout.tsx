import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Eye, LogOut } from 'lucide-react';
import { Sidebar } from '../components/Sidebar';
import { Topbar } from '../components/Topbar';
import { useAuth } from '../../core/auth/AuthProvider';

interface PortalLayoutProps {
  portalName: string;
}

export const PortalLayout: React.FC<PortalLayoutProps> = ({ portalName }) => {
  const { user, previewOf, exitPreview } = useAuth();
  const navigate = useNavigate();

  const handleExitPreview = () => {
    exitPreview();
    navigate('/admin', { replace: true });
  };

  return (
    <div className="flex min-h-screen bg-[#FFF4E9]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        {/* Always-visible preview strip: guarantees a way out of a preview on any screen size. */}
        {previewOf && (
          <div className="z-40 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 bg-amber-400 text-amber-950 px-4 py-2 text-xs font-bold">
            <Eye size={14} className="shrink-0" />
            <span className="truncate">
              Previewing the {user?.role} portal as {user?.name}
            </span>
            <button
              type="button"
              onClick={handleExitPreview}
              title={`Return to ${previewOf.name}'s admin session`}
              className="inline-flex items-center gap-1.5 rounded-lg bg-amber-950/10 px-2.5 py-1 font-black uppercase tracking-wide hover:bg-amber-950/20 cursor-pointer"
            >
              <LogOut size={12} />
              <span>Exit preview</span>
            </button>
          </div>
        )}
        <Topbar portalName={portalName} />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
