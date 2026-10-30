import React from 'react';
import { useRouteError, isRouteErrorResponse, useNavigate } from 'react-router-dom';
import { AlertTriangle, RefreshCw, Home, LogOut, ArrowLeft } from 'lucide-react';

export const RouteErrorBoundary: React.FC = () => {
  const error = useRouteError();
  const navigate = useNavigate();

  let errorMessage = 'An unexpected application error occurred.';
  let errorStatus: number | string = 'Error';
  let errorDetails = '';

  if (isRouteErrorResponse(error)) {
    errorStatus = error.status;
    errorMessage = error.statusText || error.data?.message || 'Page or resource not found.';
  } else if (error instanceof Error) {
    errorMessage = error.message;
    errorDetails = error.stack || '';
  } else if (typeof error === 'string') {
    errorMessage = error;
  }

  const handleLogout = () => {
    localStorage.removeItem('campusops_token');
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-[#FFF4E9] flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-xl bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden">
        {/* Header Bar */}
        <div className="bg-[#345873] px-8 py-6 text-white flex items-center justify-between border-b border-[#436e8f]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[#F29877] flex items-center justify-center font-black text-white text-lg shadow-sm">
              CO
            </div>
            <div>
              <h2 className="font-black text-lg tracking-wider">
                CAMPUS<span className="text-[#F29877]">OPS</span>
              </h2>
              <p className="text-[10px] text-[#8EB9D8] tracking-widest font-bold uppercase">
                Application Stability Guard
              </p>
            </div>
          </div>
          <span className="text-xs font-mono bg-white/10 px-2.5 py-1 rounded-lg border border-white/20">
            {errorStatus}
          </span>
        </div>

        {/* Content Body */}
        <div className="p-8 space-y-6">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center shrink-0">
              <AlertTriangle size={24} />
            </div>
            <div>
              <h3 className="font-extrabold text-base text-gray-900">
                Workspace Encountered an Issue
              </h3>
              <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                The current view encountered an unexpected runtime condition. You can reload the page, return to your portal dashboard, or re-authenticate.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-700 break-words max-h-40 overflow-y-auto">
            <p className="font-bold text-rose-700 mb-1">{errorMessage}</p>
            {errorDetails && (
              <pre className="text-[10px] text-gray-500 whitespace-pre-wrap font-sans mt-2">
                {errorDetails.split('\n').slice(0, 5).join('\n')}
              </pre>
            )}
          </div>

          {/* Action Recovery Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2.5 rounded-xl bg-[#345873] hover:bg-[#253f54] text-white text-xs font-bold transition flex items-center justify-center space-x-2 shadow-xs cursor-pointer"
            >
              <RefreshCw size={14} />
              <span>Reload Page</span>
            </button>

            <button
              onClick={() => navigate('/')}
              className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-gray-800 text-xs font-bold transition flex items-center justify-center space-x-2 border border-slate-200 cursor-pointer"
            >
              <Home size={14} />
              <span>Dashboard</span>
            </button>

            <button
              onClick={handleLogout}
              className="px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold transition flex items-center justify-center space-x-2 border border-rose-200 cursor-pointer"
            >
              <LogOut size={14} />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

