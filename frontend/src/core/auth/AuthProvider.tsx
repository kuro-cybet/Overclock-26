import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../../types';
import { api } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password?: string) => Promise<User>;
  logout: () => void;
  switchRole: (role: string, subRole?: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('campusops_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadUser() {
      if (token) {
        try {
          const userData = await api.getMe();
          setUser(userData);
        } catch {
          localStorage.removeItem('campusops_token');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    }
    loadUser();
  }, [token]);

  const login = async (email: string, password: string = 'password123'): Promise<User> => {
    const res = await api.login({ email, password });
    localStorage.setItem('campusops_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const logout = () => {
    localStorage.removeItem('campusops_token');
    setToken(null);
    setUser(null);
  };

  const switchRole = async (targetRole: string) => {
    const roleEmailMap: Record<string, string> = {
      admin: 'admin@campusops.edu',
      technician: 'tech@campusops.edu',
      faculty: 'faculty@campusops.edu',
      student: 'student@campusops.edu',
      department_manager: 'dept_mgr@campusops.edu',
      facilities_admin: 'facilities@campusops.edu',
      procurement_approver: 'procurement@campusops.edu',
      floor_incharge: 'floor_incharge@campusops.edu',
      janitor: 'janitor@campusops.edu',
      room_incharge: 'room_incharge@campusops.edu',
    };

    const targetEmail = roleEmailMap[targetRole] || `${targetRole}@campusops.edu`;
    await login(targetEmail, 'password123');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, switchRole }}>
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

