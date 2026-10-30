import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import {
  Wrench,
  ShieldCheck,
  AlertTriangle,
  Clock,
  RefreshCw,
  Calendar,
  Activity,
  Layers,
  CheckCircle2,
  Cpu,
  Package
} from 'lucide-react';

export const PredictiveMaintenanceView: React.FC = () => {
  const [fleetData, setFleetData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTier, setActiveTier] = useState<'high_risk' | 'attention' | 'healthy' | 'schedules'>('high_risk');

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    setLoading(true);
    try {
      const res = await api.getPredictiveFleetOverview();
      setFleetData(res);
    } catch (err) {
      console.error('Failed to load predictive maintenance data', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#287D70] mx-auto mb-3" />
        <p className="text-xs text-gray-500 font-medium">Computing asset health scores & failure hazard curves...</p>
      </div>
    );
  }

  const summary = fleetData?.summary || {
    total_assets: 0,
    healthy_count: 0,
    attention_count: 0,
    high_risk_count: 0,
    upcoming_pm_count: 0
  };

  const highRisk = fleetData?.high_risk_assets || [];
  const attention = fleetData?.attention_required_assets || [];
  const healthy = fleetData?.healthy_assets || [];
  const schedules = fleetData?.upcoming_schedules || [];

  const currentList =
    activeTier === 'high_risk' ? highRisk :
    activeTier === 'attention' ? attention :
    activeTier === 'healthy' ? healthy : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-emerald-100 text-[#287D70]">
              Empirical Fleet Telemetry
            </span>
            <span className="text-xs text-gray-500 font-medium">Statistical Health & 30-Day Failure Forecasting</span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Predictive Maintenance Hub</h1>
        </div>

        <button
          onClick={loadOverview}
          className="p-2 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition cursor-pointer text-[#345873] self-start sm:self-auto flex items-center space-x-1.5 text-xs font-bold"
        >
          <RefreshCw size={14} />
          <span>Recalculate Health</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Monitored Fleet</p>
          <p className="text-2xl font-black text-gray-800 mt-1">{summary.total_assets}</p>
          <span className="text-[10px] text-gray-500 font-semibold">Active campus assets</span>
        </div>

        <div
          onClick={() => setActiveTier('high_risk')}
          className={`p-5 rounded-3xl border transition cursor-pointer ${
            activeTier === 'high_risk'
              ? 'bg-rose-50 border-rose-300 ring-2 ring-rose-400'
              : 'bg-white border-slate-200 hover:border-rose-200'
          }`}
        >
          <p className="text-xs font-bold text-rose-600 uppercase tracking-wider">High Risk</p>
          <p className="text-2xl font-black text-rose-700 mt-1">{summary.high_risk_count}</p>
          <span className="text-[10px] text-rose-500 font-semibold">Health &lt; 50 (Imminent)</span>
        </div>

        <div
          onClick={() => setActiveTier('attention')}
          className={`p-5 rounded-3xl border transition cursor-pointer ${
            activeTier === 'attention'
              ? 'bg-amber-50 border-amber-300 ring-2 ring-amber-400'
              : 'bg-white border-slate-200 hover:border-amber-200'
          }`}
        >
          <p className="text-xs font-bold text-amber-600 uppercase tracking-wider">Attention Required</p>
          <p className="text-2xl font-black text-amber-700 mt-1">{summary.attention_count}</p>
          <span className="text-[10px] text-amber-600 font-semibold">Health 50–74</span>
        </div>

        <div
          onClick={() => setActiveTier('healthy')}
          className={`p-5 rounded-3xl border transition cursor-pointer ${
            activeTier === 'healthy'
              ? 'bg-emerald-50 border-emerald-300 ring-2 ring-emerald-400'
              : 'bg-white border-slate-200 hover:border-emerald-200'
          }`}
        >
          <p className="text-xs font-bold text-emerald-600 uppercase tracking-wider">Healthy Assets</p>
          <p className="text-2xl font-black text-emerald-700 mt-1">{summary.healthy_count}</p>
          <span className="text-[10px] text-emerald-600 font-semibold">Health &ge; 75</span>
        </div>

        <div
          onClick={() => setActiveTier('schedules')}
          className={`p-5 rounded-3xl border transition cursor-pointer ${
            activeTier === 'schedules'
              ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-400'
              : 'bg-white border-slate-200 hover:border-blue-200'
          }`}
        >
          <p className="text-xs font-bold text-blue-600 uppercase tracking-wider">Upcoming PMs</p>
          <p className="text-2xl font-black text-blue-700 mt-1">{summary.upcoming_pm_count}</p>
          <span className="text-[10px] text-blue-600 font-semibold">Next 30 days</span>
        </div>
      </div>

      {/* Main Content Area */}
      {activeTier !== 'schedules' ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-extrabold text-base text-gray-800">
              {activeTier === 'high_risk' && 'High Risk Assets Requiring Immediate Intervention'}
              {activeTier === 'attention' && 'Assets Requiring Routine Maintenance / Recalibration'}
              {activeTier === 'healthy' && 'Nominal & Verified Fleet Assets'}
              <span className="text-xs font-bold text-gray-400 ml-2">({currentList.length} items)</span>
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {currentList.map((asset: any) => (
              <div
                key={asset.asset_id}
                className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4 flex flex-col justify-between"
              >
                <div>
                  {/* Top: Tag & Health Gauge */}
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-mono text-xs font-bold text-[#287D70]">{asset.asset_tag}</span>
                      <h4 className="font-extrabold text-sm text-gray-800 mt-0.5">{asset.name}</h4>
                      <p className="text-[11px] text-gray-500">{asset.location}</p>
                    </div>

                    <div className="text-right">
                      <div
                        className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black text-base shadow-xs ${
                          asset.health_score >= 75
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : asset.health_score >= 50
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {asset.health_score}
                      </div>
                      <span className="text-[9px] font-bold text-gray-400 uppercase">Health Score</span>
                    </div>
                  </div>

                  {/* 30-Day Failure Risk Meter */}
                  <div className="mt-4 p-3 bg-slate-50 rounded-2xl border border-slate-100 space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-bold">
                      <span className="text-gray-600">30-Day Failure Risk:</span>
                      <span
                        className={
                          asset.failure_probability_30d > 0.4
                            ? 'text-rose-600'
                            : asset.failure_probability_30d > 0.2
                            ? 'text-amber-600'
                            : 'text-emerald-600'
                        }
                      >
                        {Math.round(asset.failure_probability_30d * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full ${
                          asset.failure_probability_30d > 0.4
                            ? 'bg-rose-500'
                            : asset.failure_probability_30d > 0.2
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(100, asset.failure_probability_30d * 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Operational Metrics */}
                  <div className="grid grid-cols-3 gap-2 text-center mt-3 text-[11px]">
                    <div className="p-2 bg-slate-50 rounded-xl">
                      <span className="text-gray-400 block text-[9px] uppercase font-bold">Age</span>
                      <strong className="text-gray-700">{asset.metrics?.age_years} yrs</strong>
                    </div>
                    <div className="p-2 bg-slate-50 rounded-xl">
                      <span className="text-gray-400 block text-[9px] uppercase font-bold">Failures</span>
                      <strong className="text-gray-700">{asset.metrics?.failure_count}</strong>
                    </div>
                    <div className="p-2 bg-slate-50 rounded-xl">
                      <span className="text-gray-400 block text-[9px] uppercase font-bold">Unserviced</span>
                      <strong className="text-gray-700">{asset.metrics?.days_since_service}d</strong>
                    </div>
                  </div>

                  {/* Prescription */}
                  <div className="mt-3.5 space-y-1">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#287D70]">
                      Prescribed Action
                    </span>
                    <p className="text-xs text-gray-700 font-medium leading-relaxed">{asset.recommended_action}</p>
                  </div>
                </div>

                {/* Suggested Parts */}
                {asset.suggested_parts && asset.suggested_parts.length > 0 && (
                  <div className="pt-2 border-t border-slate-100 flex flex-wrap gap-1.5 items-center">
                    <Package size={12} className="text-gray-400" />
                    {asset.suggested_parts.map((p: string) => (
                      <span
                        key={p}
                        className="text-[10px] font-bold px-2 py-0.5 bg-slate-100 rounded-md text-gray-600"
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Upcoming PM Schedules Tab */
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <h3 className="font-black text-base text-gray-800">Scheduled Preventive Maintenance Sweeps</h3>
              <p className="text-xs text-gray-500">Upcoming cyclical inspections configured across university facilities</p>
            </div>
          </div>

          <div className="space-y-3">
            {schedules.map((s: any) => (
              <div
                key={s.schedule_id}
                className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 flex items-center justify-between"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2.5 bg-blue-100 text-blue-700 rounded-xl">
                    <Calendar size={18} />
                  </div>
                  <div>
                    <span className="font-mono text-xs font-bold text-[#287D70]">{s.asset_tag}</span>
                    <p className="font-extrabold text-sm text-gray-800">{s.asset_name}</p>
                    <p className="text-[11px] text-gray-500">Frequency: Every {s.frequency_days} days</p>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-xs font-extrabold px-3 py-1 bg-blue-50 text-blue-700 rounded-xl border border-blue-200">
                    Due in {s.days_remaining} days ({s.next_due_at})
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

