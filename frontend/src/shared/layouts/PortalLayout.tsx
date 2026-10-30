import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { Topbar } from '../components/Topbar';

interface PortalLayoutProps {
  portalName: string;
}

export const PortalLayout: React.FC<PortalLayoutProps> = ({ portalName }) => {
  return (
    <div className="flex min-h-screen bg-[#FFF4E9]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar portalName={portalName} />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

