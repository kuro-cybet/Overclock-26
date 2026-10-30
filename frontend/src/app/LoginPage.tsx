import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../core/auth/AuthProvider';
import { Building2, GraduationCap, ShieldCheck, UserCheck, Wrench } from 'lucide-react';

declare global {
  interface Window {
    google?: any;
  }
}

// Google Identity Services client ID. When it is missing the button cannot be
// rendered, so the page shows an explicit configuration notice instead.
const GOOGLE_CLIENT_ID = (import.meta.env.VITE_GOOGLE_CLIENT_ID || '').trim();

// Informational only: the signed-in Google account determines the role.
const WORKSPACES = [
  {
    role: 'admin',
    icon: <Building2 size={18} />,
    title: 'Operations Admin',
    description: 'Control centre, incidents, approvals and simulations.',
    color: '#345873',
  },
  {
    role: 'technician',
    icon: <Wrench size={18} />,
    title: 'Technician',
    description: 'Assigned tasks, checklists and parts requisitions.',
    color: '#F29877',
  },
  {
    role: 'faculty',
    icon: <GraduationCap size={18} />,
    title: 'Faculty',
    description: 'Timetables, room requests and exam readiness.',
    color: '#8EB9D8',
  },
  {
    role: 'student',
    icon: <UserCheck size={18} />,
    title: 'Student',
    description: 'Issue intake, notices and campus services.',
    color: '#5B8C6E',
  },
];

export const LoginPage: React.FC = () => {
  const { loginWithGoogle, user } = useAuth();
  const navigate = useNavigate();

  const [googleReady, setGoogleReady] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const googleButtonRef = useRef<HTMLDivElement>(null);
  const googleCallbackRef = useRef<(response: any) => void>(() => {});

  // Already signed in: go straight to the portal tied to this account's role.
  useEffect(() => {
    if (user) navigate(`/${user.role}`, { replace: true });
  }, [user, navigate]);

  // Load Google Identity Services once, only when a client ID is configured.
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const scriptId = 'google-gsi-client';
    const handleLoad = () => setGoogleReady(true);
    const handleError = () =>
      setError('Could not load Google sign-in. Check your connection and reload the page.');
    const existing = document.getElementById(scriptId) as HTMLScriptElement | null;

    if (existing) {
      if (window.google?.accounts?.id) handleLoad();
      else {
        existing.addEventListener('load', handleLoad);
        existing.addEventListener('error', handleError);
      }
      return () => {
        existing.removeEventListener('load', handleLoad);
        existing.removeEventListener('error', handleError);
      };
    }

    const script = document.createElement('script');
    script.id = scriptId;
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.addEventListener('load', handleLoad);
    script.addEventListener('error', handleError);
    document.head.appendChild(script);
    return () => {
      script.removeEventListener('load', handleLoad);
      script.removeEventListener('error', handleError);
    };
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
      setError(
        err?.message ||
          'Google sign-in failed. Make sure this Google account has been assigned a CampusOps role.'
      );
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
            Sign in with the Google account issued to you by your administrator
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12">
          {/* Workspaces */}
          <div className="md:col-span-6 p-8 bg-[#FFF4E9]/40 border-b md:border-b-0 md:border-r border-slate-100">
            <p className="text-xs font-black uppercase tracking-wider text-[#345873] mb-1">
              Four dedicated workspaces
            </p>
            <p className="text-[11px] text-gray-500 mb-4">
              Your assigned Google account opens the matching workspace automatically.
            </p>
            <div className="space-y-3">
              {WORKSPACES.map((workspace) => (
                <div
                  key={workspace.role}
                  className="w-full flex items-start space-x-3 bg-white/80 border border-slate-200 rounded-2xl p-3.5"
                >
                  <span
                    className="p-2 rounded-xl shrink-0"
                    style={{ backgroundColor: `${workspace.color}18`, color: workspace.color }}
                  >
                    {workspace.icon}
                  </span>
                  <div className="flex-1">
                    <p className="text-xs font-extrabold text-gray-900">{workspace.title}</p>
                    <p className="text-[11px] text-gray-500 mt-0.5">{workspace.description}</p>
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-5 text-[11px] leading-relaxed text-gray-500">
              Your account is bound to a single role and portal. System administrators can preview
              other portals after signing in.
            </p>
          </div>

          {/* Google sign-in */}
          <div className="md:col-span-6 p-8 flex flex-col justify-center">
            <div className="flex items-center space-x-2 text-[#345873] mb-1">
              <ShieldCheck size={16} />
              <h2 className="font-extrabold text-sm">Account Authentication</h2>
            </div>
            <p className="text-xs text-gray-500 mb-5">
              Continue with the Google account an administrator assigned to CampusOps.
            </p>

            {error && (
              <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-semibold">
                {error}
              </div>
            )}

            {GOOGLE_CLIENT_ID ? (
              <>
                <div className="flex justify-center">
                  <div
                    ref={googleButtonRef}
                    aria-label="Continue with Google"
                    className={googleLoading ? 'opacity-50 pointer-events-none' : ''}
                  />
                </div>

                {googleLoading && (
                  <p className="mt-3 text-center text-[11px] font-bold text-gray-500">
                    Signing in with Google…
                  </p>
                )}

                <p className="mt-4 text-center text-[10px] text-gray-400">
                  Only Google accounts assigned a CampusOps role can sign in. Your role is applied
                  by the server.
                </p>
              </>
            ) : (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 font-semibold">
                Google sign-in is not configured for this deployment. Set
                {' '}
                <code className="font-mono">VITE_GOOGLE_CLIENT_ID</code> and redeploy the frontend.
              </div>
            )}

            <p className="mt-6 text-[11px] text-gray-400 flex items-start space-x-1.5">
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
