import React from 'react';
import { useAuth } from './AuthProvider';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface RoleGuardProps {
  allowedRoles: string[];
  allowedSubRoles?: string[];
  children: React.ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ allowedRoles, allowedSubRoles, children }) => {
  const { user, switchRole } = useAuth();
  const navigate = useNavigate();

  const roleAllowed = user && allowedRoles.includes(user.role);
  // system_admin always has access to all admin operations
  const subRoleAllowed =
    !allowedSubRoles ||
    (user && (user.sub_role === 'system_admin' || allowedSubRoles.includes(user.sub_role || '')));

  if (!user || !roleAllowed || !subRoleAllowed) {
    return (
      <div className="min-h-screen bg-[#FFF4E9] flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-8 border border-red-200 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4 text-red-600">
            <ShieldAlert size={36} />
          </div>
          <h2 className="text-2xl font-bold text-[#345873] mb-2">Restricted Access</h2>
          <p className="text-gray-600 text-sm mb-4">
            Your current sub-role{' '}
            <span className="font-semibold text-[#345873] uppercase tracking-wide px-2 py-0.5 bg-gray-100 rounded">
              {user?.sub_role ? String(user.sub_role).replace(/_/g, ' ') : user?.role || 'Guest'}
            </span>{' '}
            is not authorized to access this specific module.
          </p>
          {allowedSubRoles && (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl p-3 mb-6">
              Only <strong>System Administrator</strong> or sub-roles{' '}
              <span className="font-mono font-bold">[{allowedSubRoles.join(', ')}]</span> have access.
            </p>
          )}

          <div className="space-y-3">
            <p className="text-xs text-gray-500 font-medium">Quick switch to an authorized demo role:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {allowedRoles.map((role) => (
                <button
                  key={role}
                  onClick={async () => {
                    await switchRole(role);
                    navigate(`/${role}`);
                  }}
                  className="px-4 py-2 bg-[#345873] text-white rounded-lg text-xs font-semibold hover:bg-[#253f54] transition cursor-pointer capitalize"
                >
                  Switch to {role}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-100">
            <button
              onClick={() => navigate(`/${user?.role || 'login'}`)}
              className="text-xs text-gray-500 flex items-center justify-center mx-auto hover:text-[#345873] font-medium"
            >
              <ArrowLeft size={14} className="mr-1" /> Return to my designated portal
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

