import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../../types';
import { api } from '../api/client';

const TOKEN_KEY = 'campusops_token';
const PREVIEW_KEY = 'campusops_preview_admin';

interface PreviewSession {
  token: string;
  user: User;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  /** Set while a system_admin is previewing another portal as that role. */
  previewOf: User | null;
  isSystemAdmin: boolean;
  login: (email: string, password?: string) => Promise<User>;
  loginWithGoogle: (credential: string) => Promise<User>;
  logout: () => void;
  impersonate: (role: string) => Promise<User>;
  exitPreview: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function readPreviewSession(): PreviewSession | null {
  try {
    const raw = localStorage.getItem(PREVIEW_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PreviewSession;
    if (parsed?.token && parsed?.user?.id) return parsed;
  } catch {
    // Corrupt entry: fall through and clear it below.
  }
  localStorage.removeItem(PREVIEW_KEY);
  return null;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem(TOKEN_KEY));
  const [previewOf, setPreviewOf] = useState<User | null>(() => readPreviewSession()?.user ?? null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      if (!token) {
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
        setPreviewOf(null);
        setLoading(false);
        return;
      }

      try {
        const userData = await api.getMe();
        if (cancelled) return;

        setUser(userData);

        const preview = readPreviewSession();
        if (preview && preview.user.id !== userData.id) {
          setPreviewOf(preview.user);
        } else {
          if (preview) localStorage.removeItem(PREVIEW_KEY);
          setPreviewOf(null);
        }
        setLoading(false);
      } catch {
        if (cancelled) return;

        // An expired preview token silently returns the admin to their own session.
        const preview = readPreviewSession();
        if (preview) {
          localStorage.removeItem(PREVIEW_KEY);
          localStorage.setItem(TOKEN_KEY, preview.token);
          setPreviewOf(null);
          setToken(preview.token);
          return;
        }

        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
        setLoading(false);
      }
    }

    loadUser();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = async (email: string, password: string = ''): Promise<User> => {
    const res = await api.login({ email, password });

    // A fresh sign-in always starts a normal (non-preview) session.
    localStorage.removeItem(PREVIEW_KEY);
    localStorage.setItem(TOKEN_KEY, res.access_token);

    setPreviewOf(null);
    setToken(res.access_token);
    setUser(res.user);
    setLoading(false);
    return res.user;
  };

  const loginWithGoogle = async (credential: string): Promise<User> => {
    const res = await api.googleLogin(credential);

    localStorage.removeItem(PREVIEW_KEY);
    localStorage.setItem(TOKEN_KEY, res.access_token);

    setPreviewOf(null);
    setToken(res.access_token);
    setUser(res.user);
    setLoading(false);
    return res.user;
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(PREVIEW_KEY);
    setToken(null);
    setUser(null);
    setPreviewOf(null);
  };

  const impersonate = async (role: string): Promise<User> => {
    if (!user || !token) {
      throw new Error('You must be signed in to switch portals.');
    }
    if (!(user.role === 'admin' && user.sub_role === 'system_admin')) {
      throw new Error('Only a system administrator can switch between portals.');
    }
    if (previewOf) {
      throw new Error('Exit the current portal preview before switching again.');
    }

    // Persist the real admin session *before* the request so that a refresh while
    // the impersonation is in flight cannot strand the user inside the preview.
    localStorage.setItem(PREVIEW_KEY, JSON.stringify({ token, user }));

    let res;
    try {
      res = await api.impersonate(role);
    } catch (err) {
      localStorage.removeItem(PREVIEW_KEY);
      throw err;
    }

    localStorage.setItem(TOKEN_KEY, res.access_token);

    setPreviewOf(user);
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const exitPreview = () => {
    const session = readPreviewSession();
    localStorage.removeItem(PREVIEW_KEY);
    setPreviewOf(null);

    if (!session) return;

    localStorage.setItem(TOKEN_KEY, session.token);
    setToken(session.token);
    setUser(session.user);
  };

  const isSystemAdmin =
    !!user && user.role === 'admin' && user.sub_role === 'system_admin' && !previewOf;

  return (
    <AuthContext.Provider
      value={{ user, token, loading, previewOf, isSystemAdmin, login, loginWithGoogle, logout, impersonate, exitPreview }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
