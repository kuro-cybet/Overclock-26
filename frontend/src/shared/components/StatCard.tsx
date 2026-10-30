import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: string;
  accentColor?: string;
  isAlert?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  accentColor = '#345873',
  isAlert = false
}) => {
  return (
    <div
      className={`bg-white rounded-2xl p-5 border shadow-sm transition hover:shadow-md relative overflow-hidden ${
        isAlert ? 'border-red-300 ring-2 ring-red-100' : 'border-slate-100'
      }`}
    >
      <div
        className="absolute top-0 left-0 h-1 w-full"
        style={{ backgroundColor: accentColor }}
      />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{title}</p>
          <h3 className="text-2xl font-extrabold text-[#345873] mt-1">{value}</h3>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
          {trend && (
            <p className="text-xs text-emerald-600 font-semibold mt-2 flex items-center">
              <span>{trend}</span>
            </p>
          )}
        </div>
        <div
          className="p-3 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: `${accentColor}15`, color: accentColor }}
        >
          {icon}
        </div>
      </div>
    </div>
  );
};

