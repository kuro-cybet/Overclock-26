import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../core/auth/AuthProvider';
import {
  ArrowRight,
  Building2,
  GraduationCap,
  Lock,
  ShieldCheck,
  UserCheck,
  Wrench,
} from 'lucide-react';

declare global {
  interface Window {
    google?: any;
  }
}

// Rendered only when a client ID is configured; the button itself is Google's
// official "Continue with Google" widget (text: 'continue_with').
const GOOGLE_CLIENT_ID = (import.meta.env.VITE_GOOGLE_CLIENT_ID || '').trim();

// Demo credentials for the seeded accounts, one per portal. Clicking a portal
// card signs straight in with that account instead of typing the credentials.
const DEMO_PASSWORD = 'password123';

const PORTALS = [
  {
    role: 'admin',
    email: 'rajesekersudharsan@gmail.com',
    icon: <Building2 size={18} />,
    title: 'Operations Admin',
    description: 'Control centre, incidents, approvals and simulations.',
    color: '#345873',
  },
  {
    role: 'technician',
    email: 'techtroveversion3@gmail.com',
    icon: <Wrench size={18} />,
    title: 'Technician',
    description: 'Assigned tasks, checklists and parts requisitions.',
    color: '#F29877',
  },
  {
    role: 'faculty',
    email: 'susen469@gmail.com',
    icon: <GraduationCap size={18} />,
    title: 'Faculty',
    description: 'Timetables, room requests and exam readiness.',
    color: '#8EB9D8',
  },
  {
    role: 'student',
    email: '192573020.simats@saveetha.com',
    icon: <UserCheck size={18} />,
    title: 'Student',
    description: 'Issue intake, notices and campus services.',
    color: '#5B8C6E',
  },
];

type Portal = (typeof PORTALS)[number];

export const LoginPage: React.FC = () => {
  const { login, loginWithGoogle, user } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [portalLoading, setPortalLoading] = useState<string | null>(null);
  const [googleReady, setGoogleReady] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const googleButtonRef = useRef<HTMLDivElement>(null);
  const googleCallbackRef = useRef<(response: any) => void>(() => {});

  const busy = loading || portalLoading !== null || googleLoading;

  // Already signed in: go straight to the portal tied to this account's role.
  useEffect(() => {
    if (user) navigate(`/${user.role}`, { replace: true });
  }, [user, navigate]);

  // Load Google Identity Services once, only when a client ID is configured.
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const scriptId = 'google-gsi-client';
    const handleLoad = () => setGoogleReady(true);
    const existing = document.getElementById(scriptId) as HTMLScriptElement | null;

    if (existing) {
      if (window.google?.accounts?.id) handleLoad();
      else existing.addEventListener('load', handleLoad);
      return () => existing.removeEventListener('load', handleLoad);
    }

    const script = document.createElement('script');
    script.id = scriptId;
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.addEventListener('load', handleLoad);
    document.head.appendChild(script);
    return () => script.removeEventListener('load', handleLoad);
  }, []);

  const handleGoogleCredential = async (response: { credential?: string }) => {
    if (!response?.credential) {
      setError('Google did not return a credential. Please try again.');
      return;
    }
    setGoogleLoading(true);
    setError(null);
    try {
      const signedIn = await loginWithGoogle(response.credential);
      navigate(`/${signedIn.role}`, { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Google sign-in failed. Use your CampusOps password instead.');
    } finally {
      setGoogleLoading(false);
    }
  };

  // Keep the callback fresh without re-rendering Google's widget.
  googleCallbackRef.current = handleGoogleCredential;

  useEffect(() => {
    if (!googleReady || !GOOGLE_CLIENT_ID) return;
    const google = window.google;
    if (!google?.accounts?.id || !googleButtonRef.current) return;

    google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: (response: any) => googleCallbackRef.current(response),
      ux_mode: 'popup',
      auto_select: false,
    });
    google.accounts.id.renderButton(googleButtonRef.current, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      shape: 'pill',
      text: 'continue_with',
      logo_alignment: 'left',
      width: 320,
    });
  }, [googleReady]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const signedIn = await login(email.trim(), password);
      navigate(`/${signedIn.role}`, { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Unable to sign in. Check your credentials and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePortalLogin = async (portal: Portal) => {
    if (busy) return;
    setPortalLoading(portal.role);
    setError(null);
    try {
      const signedIn = await login(portal.email, DEMO_PASSWORD);
      navigate(`/${signedIn.role}`, { replace: true });
    } catch (err: any) {
      setError(
        err?.message ||
          `Could not sign in to the ${portal.title} portal. Use the form below instead.`
      );
    } finally {
      setPortalLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFF4E9] flex flex-col justify-center items-center p-6 md:p-10">
      <div className="w-full max-w-4xl bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden">
        {/* Brand bar */}
        <div className="bg-[#345873] px-8 py-6 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#436e8f]">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-[#F29877] flex items-center justify-center font-black text-white text-2xl shadow-sm">
              CO
            </div>
            <div>
              <h1 className="font-black text-2xl tracking-wider">
                CAMPUS<span className="text-[#F29877]">OPS</span>
              </h1>
              <p className="text-xs text-[#8EB9D8] tracking-widest font-bold uppercase">
                Role-Based University Operations Platform
              </p>
            </div>
          </div>
          <p className="text-xs text-slate-300 font-medium">
            Sign in with the account issued to you by your administrator
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12">
          {/* Portal quick sign-in */}
          <div className="md:col-span-6 p-8 bg-[#FFF4E9]/40 border-b md:border-b-0 md:border-r border-slate-100">
            <p className="text-xs font-black uppercase tracking-wider text-[#345873] mb-1">
              Four dedicated workspaces
            </p>
            <p className="text-[11px] text-gray-500 mb-4">
              Click a workspace to sign in to it directly.
            </p>
            <div className="space-y-3">
              {PORTALS.map((portal) => {
                const isPortalLoading = portalLoading === portal.role;
                return (
                  <button
                    type="button"
                    key={portal.role}
                    onClick={() => handlePortalLogin(portal)}
                    disabled={busy}
                    aria-label={`Sign in to the ${portal.title} portal`}
                    title={`Sign in as ${portal.email}`}
                    className="group w-full text-left flex items-start space-x-3 bg-white/80 border border-slate-200 rounded-2xl p-3.5 transition cursor-pointer hover:border-[#345873]/50 hover:bg-white hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#345873] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:border-slate-200 disabled:hover:bg-white/80 disabled:hover:shadow-none"
                  >
                    <span
                      className="p-2 rounded-xl shrink-0"
                      style={{ backgroundColor: `${portal.color}18`, color: portal.color }}
                    >
                      {portal.icon}
                    </span>
                    <div className="flex-1">
                      <p className="text-xs font-extrabold text-gray-900">{portal.title}</p>
                      <p className="text-[11px] text-gray-500 mt-0.5">{portal.description}</p>
                    </div>
                    <span className="self-center shrink-0 text-[10px] font-bold text-[#345873]">
                      {isPortalLoading ? (
                        'Signing in…'
                      ) : (
                        <ArrowRight
                          size={14}
                          className="opacity-0 group-hover:opacity-100 transition"
                        />
                      )}
                    </span>
                  </button>
                );
              })}
            </div>
            <p className="mt-5 text-[11px] leading-relaxed text-gray-500">
              Your account is bound to a single role and portal. System administrators can preview
              other portals after signing in.
            </p>
          </div>

          {/* Credentials */}
          <div className="md:col-span-6 p-8 flex flex-col justify-center">
            <div className="flex items-center space-x-2 text-[#345873] mb-1">
              <Lock size={16} />
              <h2 className="font-extrabold text-sm">Account Authentication</h2>
            </div>
            <p className="text-xs text-gray-500 mb-5">
              Enter your university email address and password.
            </p>

            {error && (
              <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-semibold">
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-xs font-bold text-gray-700 mb-1">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  autoComplete="username"
                  placeholder="name@campusops.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs bg-white focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-xs font-bold text-gray-700 mb-1">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs bg-white focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={busy}
                className="w-full py-3 bg-[#345873] text-white rounded-xl text-xs font-bold transition shadow-sm cursor-pointer disabled:opacity-50 mt-1 flex items-center justify-center space-x-2 hover:bg-[#253f54]"
              >
                <span>{loading ? 'Signing in…' : 'Sign in'}</span>
                {!loading && <ArrowRight size={14} />}
              </button>
            </form>

            {GOOGLE_CLIENT_ID && (
              <div className="mt-5">
                <div className="flex items-center space-x-3">
                  <span className="h-px flex-1 bg-slate-200" />
                  <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                    or
                  </span>
                  <span className="h-px flex-1 bg-slate-200" />
                </div>

                <div className="mt-4 flex justify-center">
                  <div
                    ref={googleButtonRef}
                    aria-label="Continue with Google"
                    className={googleLoading ? 'opacity-50 pointer-events-none' : ''}
                  />
                </div>

                {googleLoading && (
                  <p className="mt-2 text-center text-[11px] font-bold text-gray-500">
                    Signing in with Google…
                  </p>
                )}

                <p className="mt-2 text-center text-[10px] text-gray-400">
                  Only Google accounts assigned a CampusOps role can sign in.
                </p>
              </div>
            )}

            <p className="mt-5 text-[11px] text-gray-400 flex items-start space-x-1.5">
              <ShieldCheck size={13} className="mt-0.5 shrink-0" />
              <span>
                Access is restricted to your assigned role. Contact your system administrator if you
                cannot sign in.
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
