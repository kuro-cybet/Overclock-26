import React, { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthProvider';
import { ShieldAlert, ArrowLeft, Eye, LogOut, Loader2 } from 'lucide-react';

interface RoleGuardProps {
  allowedRoles: string[];
  allowedSubRoles?: string[];
  children: React.ReactNode;
}

const ROLE_LABELS: Record<string, string> = {
  admin: 'Operations Admin',
  technician: 'Technician',
  faculty: 'Faculty',
  student: 'Student',
};

export const RoleGuard: React.FC<RoleGuardProps> = ({ allowedRoles, allowedSubRoles, children }) => {
  const { user, previewOf, impersonate, exitPreview } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const roleAllowed = allowedRoles.includes(user.role);
  const subRoleAllowed =
    !allowedSubRoles ||
    user.sub_role === 'system_admin' ||
    allowedSubRoles.includes(user.sub_role || '');

  if (roleAllowed && subRoleAllowed) {
    return <>{children}</>;
  }

  const isSystemAdmin = user.role === 'admin' && user.sub_role === 'system_admin';
  const isPreviewing = !!previewOf;
  const previewableRole = allowedRoles.find((role) => role !== 'admin');
  const homePath = `/${user.role}`;

  const handlePreview = async () => {
    if (!previewableRole) return;
    setBusy(previewableRole);
    setError(null);
    try {
      await impersonate(previewableRole);
      navigate(`/${previewableRole}`, { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Unable to open that portal.');
    } finally {
      setBusy(null);
    }
  };

  const handleExitPreview = () => {
    exitPreview();
    navigate('/admin', { replace: true });
  };

  // A system_admin who is not already previewing can open another portal as that role.
  if (isSystemAdmin && previewableRole && !isPreviewing) {
    return (
      <div className="min-h-screen bg-[#FFF4E9] flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-8 border border-[#8EB9D8]/50 text-center">
          <div className="w-16 h-16 bg-[#EAF3F9] rounded-full flex items-center justify-center mx-auto mb-4 text-[#345873]">
            <Eye size={34} />
          </div>
          <h2 className="text-2xl font-bold text-[#345873] mb-2">Restricted Access</h2>
          <p className="text-gray-600 text-sm mb-4">
            Your current sub-role{' '}
            <span className="font-semibold text-[#345873] uppercase tracking-wide px-2 py-0.5 bg-gray-100 rounded">
              {user?.sub_role ? String(user.sub_role).replace(/_/g, ' ') : user?.role || 'Guest'}
            </span>{' '}
            portal. Open it as a {previewableRole} to see exactly what that role sees. Your admin
            session stays active and can be restored at any time.
          </p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-semibold">
              {error}
            </div>
          )}

          <button
            onClick={handlePreview}
            disabled={!!busy}
            className="w-full py-3 bg-[#345873] text-white rounded-xl text-sm font-bold hover:bg-[#253f54] transition cursor-pointer disabled:opacity-60 flex items-center justify-center space-x-2"
          >
            {busy ? <Loader2 size={16} className="animate-spin" /> : <Eye size={16} />}
            <span>{busy ? 'Opening portal…' : `Open as ${previewableRole}`}</span>
          </button>

          <button
            onClick={() => navigate('/admin')}
            className="mt-4 text-xs text-gray-500 flex items-center justify-center mx-auto hover:text-[#345873] font-medium cursor-pointer"
          >
            <ArrowLeft size={14} className="mr-1" /> Back to Admin Portal
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FFF4E9] flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-8 border border-red-200 text-center">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4 text-red-600">
          <ShieldAlert size={36} />
        </div>
        <h2 className="text-2xl font-bold text-[#345873] mb-2">
          {isPreviewing ? 'Preview Boundary' : 'Access Denied'}
        </h2>

        {isPreviewing ? (
          <p className="text-gray-600 text-sm mb-6">
            You are previewing CampusOps as{' '}
            <span className="font-semibold text-[#345873]">
              {user.name} ({ROLE_LABELS[user.role] || user.role})
            </span>
            . This area belongs to a different portal. Exit the preview to return to your
            administrator session.
          </p>
        ) : (
          <>
            <p className="text-gray-600 text-sm mb-4">
              Your account role{' '}
              <span className="font-semibold text-[#345873] uppercase tracking-wide px-2 py-0.5 bg-gray-100 rounded">
                {user.sub_role ? user.sub_role.replace(/_/g, ' ') : user.role}
              </span>{' '}
              is not authorized to access this module.
            </p>
            {allowedSubRoles && (
              <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl p-3 mb-6">
                Only <strong>System Administrator</strong> or sub-roles{' '}
                <span className="font-mono font-bold">[{allowedSubRoles.join(', ')}]</span> have
                access.
              </p>
            )}
          </>
        )}

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-semibold">
            {error}
          </div>
        )}

        <div className="mt-2">
          {isPreviewing ? (
            <button
              onClick={handleExitPreview}
              className="w-full py-3 bg-[#345873] text-white rounded-xl text-sm font-bold hover:bg-[#253f54] transition cursor-pointer flex items-center justify-center space-x-2"
            >
              <LogOut size={16} />
              <span>Exit preview and return to Admin</span>
            </button>
          ) : (
            <button
              onClick={() => navigate(homePath)}
              className="w-full py-3 bg-[#345873] text-white rounded-xl text-sm font-bold hover:bg-[#253f54] transition cursor-pointer flex items-center justify-center space-x-2"
            >
              <ArrowLeft size={16} />
              <span>Return to my portal</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
