import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Compass, Home, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../core/auth/AuthProvider';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleHomeClick = () => {
    if (user?.role) {
      navigate(`/${user.role}`);
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-[#FFF4E9] flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-lg bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden text-center p-8 sm:p-10">
        <div className="w-16 h-16 rounded-2xl bg-[#F29877]/20 text-[#d9673d] flex items-center justify-center mx-auto mb-5 shadow-xs">
          <Compass size={36} />
        </div>

        <span className="text-xs font-black tracking-widest uppercase px-3 py-1 bg-slate-100 text-slate-600 rounded-full">
          404 Not Found
        </span>

        <h1 className="text-2xl sm:text-3xl font-black text-[#345873] mt-4">
          Campus Page Not Found
        </h1>

        <p className="text-sm text-gray-500 mt-2 max-w-md mx-auto leading-relaxed">
          The requested page or resource could not be found. It may have been moved, renamed, or you may not have authorization to view it.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-8">
          <button
            onClick={() => navigate(-1)}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold transition flex items-center justify-center space-x-2 cursor-pointer"
          >
            <ArrowLeft size={16} />
            <span>Go Back</span>
          </button>

          <button
            onClick={handleHomeClick}
            className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-[#345873] hover:bg-[#253f54] text-white text-xs font-bold transition flex items-center justify-center space-x-2 shadow-xs cursor-pointer"
          >
            <Home size={16} />
            <span>{user ? 'Return to Dashboard' : 'Go to Login'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

