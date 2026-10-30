import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../core/auth/AuthProvider';
import {
  Shield,
  ArrowRight,
  UserCheck,
  Building2,
  Wrench,
  GraduationCap,
  Sparkles,
  Lock
} from 'lucide-react';
import { tokens } from '../design-system/tokens';

type RoleCategory = 'admin' | 'technician' | 'faculty' | 'student';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  // Active selected role tab for role-based access
  const [selectedRole, setSelectedRole] = useState<RoleCategory>('admin');
  const [email, setEmail] = useState('admin@campusops.edu');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const roleDefinitions = [
    {
      id: 'admin' as RoleCategory,
      title: 'Operations Admin',
      subtitle: 'Control Centre & Simulator',
      icon: <Building2 size={24} />,
      color: tokens.roleAccents.admin.color,
      defaultEmail: 'admin@campusops.edu',
      subRoles: [
        { name: 'System Administrator (Full Admin Powers)', email: 'admin@campusops.edu' },
        { name: 'Department Manager (Incidents, Approvals & Analytics)', email: 'dept_mgr@campusops.edu' },
        { name: 'Facilities Admin (Campus, Rooms & Work Orders)', email: 'facilities@campusops.edu' },
        { name: 'Procurement Approver (Inventory & Purchase Approvals)', email: 'procurement@campusops.edu' }
      ]
    },
    {
      id: 'technician' as RoleCategory,
      title: 'Technicians',
      subtitle: 'Field Tasks & Checklists',
      icon: <Wrench size={24} />,
      color: tokens.roleAccents.technician.color,
      defaultEmail: 'tech@campusops.edu',
      subRoles: [
        { name: 'Maintenance Technician (Hardware/Repairs)', email: 'tech@campusops.edu' },
        { name: 'Floor Incharge (Inspection Signoff)', email: 'floor_incharge@campusops.edu' },
        { name: 'Janitor (Sanitation & Hygiene)', email: 'janitor@campusops.edu' },
        { name: 'Room Incharge (Equipment Checks)', email: 'room_incharge@campusops.edu' }
      ]
    },
    {
      id: 'faculty' as RoleCategory,
      title: 'Faculty',
      subtitle: 'Timetables & Exam Rooms',
      icon: <GraduationCap size={24} />,
      color: tokens.roleAccents.faculty.color,
      defaultEmail: 'faculty@campusops.edu',
      subRoles: [
        { name: 'Prof. Finch (CS Exam Lead)', email: 'faculty@campusops.edu' },
        { name: 'Dr. Smith (Electrical Engineering)', email: 'prof.smith@campusops.edu' }
      ]
    },
    {
      id: 'student' as RoleCategory,
      title: 'Students',
      subtitle: 'Issue Intake & Live Alerts',
      icon: <UserCheck size={24} />,
      color: tokens.roleAccents.student.color,
      defaultEmail: 'student@campusops.edu',
      subRoles: [
        { name: 'Jordan Lee (CS Undergraduate)', email: 'student@campusops.edu' },
        { name: 'Samantha Green (EE Student)', email: 'student1@campusops.edu' }
      ]
    }
  ];

  const handleRoleSelect = (roleId: RoleCategory) => {
    setSelectedRole(roleId);
    const def = roleDefinitions.find((r) => r.id === roleId);
    if (def) {
      setEmail(def.defaultEmail);
    }
    setError(null);
  };

  const handleLogin = async (e?: React.FormEvent, customEmail?: string) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const targetEmail = customEmail || email;
      const user = await login(targetEmail, password);
      navigate(`/${user.role}`);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const activeDef = roleDefinitions.find((r) => r.id === selectedRole)!;

  return (
    <div className="min-h-screen bg-[#FFF4E9] flex flex-col justify-center items-center p-6 md:p-10">
      <div className="w-full max-w-5xl bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden">
        {/* Brand Bar */}
        <div className="bg-[#345873] px-8 py-6 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#436e8f]">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-[#F29877] flex items-center justify-center font-black text-white text-2xl shadow-sm">
              CO
            </div>
            <div>
              <h1 className="font-black text-2xl tracking-wider">CAMPUS<span className="text-[#F29877]">OPS</span></h1>
              <p className="text-xs text-[#8EB9D8] tracking-widest font-bold uppercase">
                Role-Based University Operations Platform
              </p>
            </div>
          </div>

          <div className="text-xs text-slate-300 font-medium">
            Select your assigned portal role to authenticate
          </div>
        </div>

        {/* Role-Based Selector Tabs */}
        <div className="p-8 border-b border-slate-100 bg-[#FFF4E9]/30">
          <p className="text-xs font-black uppercase tracking-wider text-[#345873] mb-4">
            Step 1: Choose Your Role Experience
          </p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {roleDefinitions.map((role) => {
              const isSelected = selectedRole === role.id;
              return (
                <button
                  key={role.id}
                  type="button"
                  onClick={() => handleRoleSelect(role.id)}
                  className={`p-5 rounded-2xl border text-left transition cursor-pointer flex flex-col justify-between group ${
                    isSelected
                      ? 'bg-white border-[#345873] ring-2 ring-[#345873]/20 shadow-md scale-[1.02]'
                      : 'bg-white/70 border-slate-200 hover:bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span
                      className="p-3 rounded-2xl transition"
                      style={{
                        backgroundColor: `${role.color}18`,
                        color: role.color
                      }}
                    >
                      {role.icon}
                    </span>
                    {isSelected && (
                      <span
                        className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider text-white"
                        style={{ backgroundColor: role.color }}
                      >
                        Active
                      </span>
                    )}
                  </div>
                  <div>
                    <h3 className="font-extrabold text-sm text-gray-900 group-hover:text-[#345873] transition">
                      {role.title}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">{role.subtitle}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Step 2: Credentials & Sub-Role Persona Selection */}
        <div className="p-8 grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* Sub-role pre-selection */}
          <div className="md:col-span-7 space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-black uppercase tracking-wider text-[#345873]">
                Step 2: Select {activeDef.title} Persona
              </p>
              <span className="text-xs text-gray-400">Preset Demo Credentials</span>
            </div>

            <div className="space-y-2.5">
              {activeDef.subRoles.map((sub, idx) => {
                const isCurrentEmail = email === sub.email;
                return (
                  <div
                    key={idx}
                    onClick={() => setEmail(sub.email)}
                    className={`p-3.5 rounded-2xl border text-xs flex items-center justify-between transition cursor-pointer ${
                      isCurrentEmail
                        ? 'bg-[#FFF4E9] border-[#345873] font-bold ring-1 ring-[#345873]/20'
                        : 'bg-white border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div>
                      <span className="text-gray-900 font-semibold text-xs block">{sub.name}</span>
                      <span className="text-[11px] font-mono text-gray-500">{sub.email}</span>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setEmail(sub.email);
                        handleLogin(undefined, sub.email);
                      }}
                      className="px-3.5 py-1.5 rounded-xl text-xs font-bold text-white transition cursor-pointer shadow-2xs"
                      style={{ backgroundColor: activeDef.color }}
                    >
                      Login Directly
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Form Sign In */}
          <div className="md:col-span-5 bg-slate-50/70 p-6 rounded-2xl border border-slate-200 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 text-[#345873] mb-1">
                <Lock size={16} />
                <h4 className="font-extrabold text-sm">Account Authentication</h4>
              </div>
              <p className="text-xs text-gray-500 mb-4">
                Sign into the <strong className="text-gray-700 capitalize">{selectedRole} Portal</strong>
              </p>

              {error && (
                <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-semibold">
                  {error}
                </div>
              )}

              <form onSubmit={(e) => handleLogin(e)} className="space-y-3.5">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">User Email</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs bg-white focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs bg-white focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 text-white rounded-xl text-xs font-bold transition shadow-sm cursor-pointer disabled:opacity-50 mt-2 flex items-center justify-center space-x-2"
                  style={{ backgroundColor: '#345873' }}
                >
                  <span>{loading ? 'Authenticating...' : `Enter ${activeDef.title} Portal`}</span>
                  <ArrowRight size={14} />
                </button>
              </form>
            </div>

            <p className="text-[11px] text-gray-400 text-center mt-4">
              Default password: <code className="font-mono font-bold text-gray-600">password123</code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
