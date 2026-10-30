import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { StatusBadge } from '../../shared/components/StatusBadge';
import {
  ShieldAlert,
  AlertTriangle,
  Building,
  DoorOpen,
  GraduationCap,
  Users,
  Boxes,
  Clock,
  Wrench,
  CheckCircle2,
  RefreshCw,
  HelpCircle,
  Activity,
  Flame,
  ArrowRight
} from 'lucide-react';

export const OperationalIntelligenceView: React.FC = () => {
  const [assessment, setAssessment] = useState<any | null>(null);
  const [explanations, setExplanations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'explanations'>('overview');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [assessRes, explRes] = await Promise.all([
        api.getOperationalAssessment(),
        api.getDecisionExplanations()
      ]);
      setAssessment(assessRes);
      setExplanations(explRes);
    } catch (err) {
      console.error('Failed to load operational intelligence', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#345873] mx-auto mb-3" />
        <p className="text-xs text-gray-500 font-medium">Synthesizing cross-module operational intelligence...</p>
      </div>
    );
  }

  const findings = assessment?.findings || {};
  const metrics = assessment?.summary_metrics || {};
  const score = assessment?.systemic_readiness_score ?? 100;
  const status = assessment?.systemic_status ?? 'nominal';

  return (
    <div className="space-y-6">
      {/* Header & Sub-nav */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-rose-100 text-rose-700">
              Autonomous Intelligence
            </span>
            <span className="text-xs text-gray-500 font-medium">Real-time Cross-Module Risk Synthesis</span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Operational Intelligence Engine</h1>
        </div>

        <div className="flex items-center space-x-2">
          <div className="bg-[#FFF4E9] p-1 rounded-2xl flex border border-peach/50">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                activeTab === 'overview' ? 'bg-[#345873] text-white shadow-xs' : 'text-[#345873] hover:bg-white/50'
              }`}
            >
              Risk Assessment
            </button>
            <button
              onClick={() => setActiveTab('explanations')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                activeTab === 'explanations' ? 'bg-[#345873] text-white shadow-xs' : 'text-[#345873] hover:bg-white/50'
              }`}
            >
              Decision Explanations ({explanations.length})
            </button>
          </div>

          <button
            onClick={loadData}
            className="p-2 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition cursor-pointer text-[#345873]"
            title="Refresh Intelligence Data"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {activeTab === 'overview' ? (
        <>
          {/* Systemic Readiness Score Banner */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="flex items-center space-x-5">
              <div
                className={`w-16 h-16 rounded-2xl flex items-center justify-center font-black text-2xl shadow-inner ${
                  score >= 80 ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' :
                  score >= 50 ? 'bg-amber-50 text-amber-600 border border-amber-200' :
                  'bg-rose-50 text-rose-600 border border-rose-200'
                }`}
              >
                {score}%
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-black text-gray-800">Campus Systemic Operational Readiness</h3>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                      status === 'nominal' ? 'bg-emerald-100 text-emerald-800' :
                      status === 'degraded' ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
                    }`}
                  >
                    {status}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1 max-w-2xl">
                  Synthesizing real-time telemetry from {metrics.active_incident_clusters || 0} building clusters, {metrics.rooms_at_risk || 0} rooms at risk, {metrics.exams_at_risk || 0} threatened exams, and {metrics.overloaded_technicians || 0} overloaded staff shifts.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 w-full md:w-auto">
              <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                <p className="text-[10px] font-bold text-gray-400 uppercase">Clusters</p>
                <p className="text-base font-black text-[#345873]">{metrics.active_incident_clusters || 0}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                <p className="text-[10px] font-bold text-gray-400 uppercase">Room Risks</p>
                <p className="text-base font-black text-amber-600">{metrics.rooms_at_risk || 0}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                <p className="text-[10px] font-bold text-gray-400 uppercase">Exams</p>
                <p className="text-base font-black text-rose-600">{metrics.exams_at_risk || 0}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                <p className="text-[10px] font-bold text-gray-400 uppercase">Overloads</p>
                <p className="text-base font-black text-[#345873]">{metrics.overloaded_technicians || 0}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                <p className="text-[10px] font-bold text-gray-400 uppercase">Stock Gaps</p>
                <p className="text-base font-black text-rose-600">{metrics.critical_stock_shortages || 0}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                <p className="text-[10px] font-bold text-gray-400 uppercase">SLA Risks</p>
                <p className="text-base font-black text-amber-600">{metrics.sla_at_risk_incidents || 0}</p>
              </div>
            </div>
          </div>

          {/* Critical Risk Rows */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 1. Multi-Incident Building Clusters */}
            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="p-2 bg-rose-50 text-rose-600 rounded-xl">
                    <Building size={18} />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-gray-800">Building Incident Clusters</h3>
                    <p className="text-[11px] text-gray-500">Multiple concurrent failures indicating common root causes</p>
                  </div>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 bg-rose-100 text-rose-700 rounded-lg">
                  {findings.building_clusters?.length || 0} Active
                </span>
              </div>

              <div className="space-y-3">
                {findings.building_clusters && findings.building_clusters.length > 0 ? (
                  findings.building_clusters.map((c: any) => (
                    <div key={c.building_id} className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-black text-sm text-gray-800">{c.building_name} ({c.building_code})</span>
                        <span className="text-xs font-extrabold px-2 py-0.5 bg-rose-600 text-white rounded-md">
                          {c.active_incident_count} Incidents
                        </span>
                      </div>
                      <p className="text-xs text-gray-600">{c.recommended_action}</p>
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {c.categories?.map((cat: string) => (
                          <span key={cat} className="text-[10px] font-bold px-2 py-0.5 bg-white border border-slate-200 rounded-md text-gray-600">
                            {cat}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-400 py-4 text-center">No multi-incident building clusters detected.</p>
                )}
              </div>
            </div>

            {/* 2. Threatened Examinations */}
            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="p-2 bg-amber-50 text-amber-600 rounded-xl">
                    <GraduationCap size={18} />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-gray-800">Examinations at Risk</h3>
                    <p className="text-[11px] text-gray-500">Sessions scheduled in rooms with unresolved facility faults</p>
                  </div>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 bg-amber-100 text-amber-700 rounded-lg">
                  {findings.affected_examinations?.length || 0} Threats
                </span>
              </div>

              <div className="space-y-3">
                {findings.affected_examinations && findings.affected_examinations.length > 0 ? (
                  findings.affected_examinations.map((ex: any) => (
                    <div key={ex.booking_id} className="p-4 bg-amber-50/50 rounded-2xl border border-amber-200/80 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-black text-sm text-gray-800">{ex.exam_title}</span>
                        <span className="text-xs font-extrabold px-2 py-0.5 bg-amber-600 text-white rounded-md">
                          {ex.hours_until_exam}h remaining
                        </span>
                      </div>
                      <p className="text-xs text-amber-900 font-medium">
                        Hall: <strong>{ex.room_code}</strong> ({ex.building_name}) — Fault: {ex.incident_title}
                      </p>
                      <p className="text-[11px] text-gray-600">{ex.recommended_action}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-400 py-4 text-center">All upcoming examination halls operational.</p>
                )}
              </div>
            </div>

            {/* 3. Rooms at Risk */}
            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                    <DoorOpen size={18} />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-gray-800">Rooms with Unresolved Maintenance</h3>
                    <p className="text-[11px] text-gray-500">Classrooms with open tickets or blocked parts</p>
                  </div>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 bg-blue-100 text-blue-700 rounded-lg">
                  {findings.rooms_at_risk?.length || 0} Rooms
                </span>
              </div>

              <div className="space-y-2.5 max-h-80 overflow-y-auto">
                {findings.rooms_at_risk && findings.rooms_at_risk.length > 0 ? (
                  findings.rooms_at_risk.map((r: any) => (
                    <div key={r.room_id} className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between">
                      <div>
                        <span className="font-bold text-xs text-gray-800">{r.room_code} — {r.room_name}</span>
                        <p className="text-[11px] text-gray-500">{r.building_name} • Condition: {r.maintenance_status}</p>
                      </div>
                      <div className="text-right">
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${
                          r.risk_level === 'critical' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          {(r.risk_level ? String(r.risk_level) : 'HIGH').toUpperCase()}
                        </span>
                        {r.has_blocked_parts && (
                          <p className="text-[10px] text-rose-600 font-bold mt-0.5">Parts Blocked</p>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-400 py-4 text-center">No rooms currently flagged at risk.</p>
                )}
              </div>
            </div>

            {/* 4. SLA Breach Projections */}
            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="p-2 bg-amber-50 text-amber-600 rounded-xl">
                    <Clock size={18} />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-gray-800">SLA Breach Projections</h3>
                    <p className="text-[11px] text-gray-500">Incidents within 45 minutes of escalation deadline</p>
                  </div>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 bg-amber-100 text-amber-700 rounded-lg">
                  {findings.sla_projections?.length || 0} At Risk
                </span>
              </div>

              <div className="space-y-2.5 max-h-80 overflow-y-auto">
                {findings.sla_projections && findings.sla_projections.length > 0 ? (
                  findings.sla_projections.map((s: any) => (
                    <div key={s.incident_id} className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-bold text-xs text-[#345873]">{s.incident_code}</span>
                          <StatusBadge status={s.priority} />
                        </div>
                        <p className="text-xs font-semibold text-gray-700 mt-0.5">{s.title}</p>
                        <p className="text-[11px] text-gray-400">Assigned: {s.assigned_technician}</p>
                      </div>
                      <div className="text-right">
                        <span className={`text-[11px] font-black px-2 py-0.5 rounded-lg ${
                          s.is_breached ? 'bg-rose-600 text-white' : 'bg-amber-100 text-amber-800'
                        }`}>
                          {s.is_breached ? 'BREACHED' : `${s.minutes_remaining} min`}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-400 py-4 text-center">All active incidents within safe SLA margins.</p>
                )}
              </div>
            </div>
          </div>
        </>
      ) : (
        /* Explanations Tab */
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <h3 className="font-black text-base text-[#345873]">Explainable AI Decision Audit Log</h3>
              <p className="text-xs text-gray-500">Transparent algorithmic rationales for technician dispatch, recovery routing, and correlation</p>
            </div>
          </div>

          <div className="space-y-3">
            {explanations.map((e) => (
              <div key={e.id} className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase bg-[#345873] text-white">
                      {(e.decision_type ? String(e.decision_type) : 'Decision').replace(/_/g, ' ')}
                    </span>
                    <span className="font-bold text-xs text-gray-700">{e.entity_type}: {e.entity_id}</span>
                  </div>
                  <span className="text-[11px] text-gray-400">
                    Confidence: <strong>{Math.round(e.confidence_score * 100)}%</strong>
                  </span>
                </div>
                <p className="text-xs text-gray-800 font-medium">{e.explanation_text}</p>
                <div className="flex items-center justify-between pt-1 text-[11px] text-gray-400">
                  <span>Chosen: <strong>{e.chosen_option}</strong></span>
                  <span>{new Date(e.created_at).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

