import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { StatusBadge } from '../../shared/components/StatusBadge';
import {
  Play,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  ShieldAlert,
  Boxes,
  Wifi,
  UserX,
  FileCheck2
} from 'lucide-react';

export const ScenarioSimulatorView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'exam' | 'technician' | 'stock' | 'wifi'>('exam');
  const [running, setRunning] = useState(false);
  const [simResult, setSimResult] = useState<any | null>(null);
  const [recoveryExecution, setRecoveryExecution] = useState<any | null>(null);
  const [resetting, setResetting] = useState(false);

  const scenarios = [
    {
      id: 'exam',
      apiName: 'exam_room_unavailable',
      title: 'Examination Room Unavailable',
      icon: <AlertTriangle size={18} className="text-[#F29877]" />,
      summary: 'Mark exam room unavailable shortly before exam; inspect exam dependency; search capacity/features; check timetable conflicts; obtain required approval.',
      expected: 'Feasible alternative room is proposed and validated; affected faculty/students receive targeted updates.'
    },
    {
      id: 'technician',
      apiName: 'technician_unavailable',
      title: 'Technician Unavailable',
      icon: <UserX size={18} className="text-[#287D70]" />,
      summary: 'Mark assigned technician absent; recalculate eligible staff using skills, workload and shift; reassign within policy.',
      expected: 'Qualified replacement is assigned; SLA deadline is preserved; escalate if no qualified person exists.'
    },
    {
      id: 'stock',
      apiName: 'stock_shortage',
      title: 'Critical Part Out of Stock',
      icon: <Boxes size={18} className="text-rose-500" />,
      summary: 'Attempt reservation when stock is unavailable; block work; create purchase request; simulate approval and receipt.',
      expected: 'No false completion; work remains blocked until stock and feasibility are revalidated.'
    },
    {
      id: 'wifi',
      apiName: 'wifi_outage',
      title: 'Multiple Wi-Fi Complaints',
      icon: <Wifi size={18} className="text-blue-500" />,
      summary: 'Submit multiple similar reports from one outage; run correlation; retain individual complaint records.',
      expected: 'One canonical incident links the reports; affected users receive relevant status updates.'
    }
  ];

  const currentScenario = scenarios.find((s) => s.id === activeTab)!;

  const handleRunSimulation = async () => {
    setRunning(true);
    setRecoveryExecution(null);
    try {
      const res = await api.triggerSimulation(currentScenario.apiName);
      setSimResult(res);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const handleExecuteRecoveryOption = async (option: any) => {
    try {
      const res = await api.executeRecovery({
        option_id: option.option_id,
        target_action: option.target_action,
        action_payload: option.action_payload,
        approval_override: true
      });
      setRecoveryExecution(res);
      alert(`Recovery Executed: ${res.message}`);
    } catch (err: any) {
      alert(`Recovery execution failed: ${err.message}`);
    }
  };

  const handleResetToBaseline = async () => {
    setResetting(true);
    try {
      await api.resetSimulation();
      setSimResult(null);
      setRecoveryExecution(null);
      alert('Clean baseline university state restored. All temporary test records reset.');
    } catch (err: any) {
      alert(`Reset failed: ${err.message}`);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Blueprint Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-rose-100 text-rose-700">
              Disruption Simulator
            </span>
            <span className="text-xs text-gray-400 font-medium">Deterministic Validation Suite</span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Disruption Scenario Simulator</h1>
          <p className="text-xs text-gray-500 mt-1">
            Validate system safety, re-routing, auto-reassignment, and inventory locks across the 4 Blueprint test scenarios.
          </p>
        </div>

        <button
          onClick={handleResetToBaseline}
          disabled={resetting}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-bold transition cursor-pointer self-start md:self-auto"
        >
          <RotateCcw size={14} className={resetting ? 'animate-spin' : ''} />
          <span>{resetting ? 'Restoring Seed State...' : 'Reset Baseline State'}</span>
        </button>
      </div>

      {/* 4 Scenario Selector Tabs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {scenarios.map((sc) => {
          const isActive = activeTab === sc.id;
          return (
            <button
              key={sc.id}
              onClick={() => {
                setActiveTab(sc.id as any);
                setSimResult(null);
                setRecoveryExecution(null);
              }}
              className={`p-4 rounded-2xl border text-left transition cursor-pointer flex flex-col justify-between ${
                isActive
                  ? 'bg-white border-[#345873] ring-2 ring-[#345873]/20 shadow-sm'
                  : 'bg-white/60 border-slate-200 hover:bg-white'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="p-2 bg-slate-50 rounded-xl">{sc.icon}</span>
                {isActive && (
                  <span className="w-2 h-2 rounded-full bg-[#345873] animate-pulse" />
                )}
              </div>
              <div>
                <h4 className="font-bold text-xs text-gray-900">{sc.title}</h4>
                <p className="text-[10px] text-gray-400 mt-1 line-clamp-2">{sc.summary}</p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Scenario Execution Box */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-lg font-black text-[#345873]">{currentScenario.title}</h3>
            <p className="text-xs text-gray-600 mt-1">{currentScenario.summary}</p>
            <p className="text-xs text-emerald-700 font-semibold mt-1">
              Expected Target: {currentScenario.expected}
            </p>
          </div>

          <button
            onClick={handleRunSimulation}
            disabled={running}
            className="flex items-center space-x-2 px-6 py-3 rounded-2xl bg-[#345873] hover:bg-[#253f54] text-white text-xs font-bold transition shadow-sm cursor-pointer disabled:opacity-50 self-start sm:self-auto shrink-0"
          >
            <Play size={16} fill="white" />
            <span>{running ? 'Executing Simulation...' : 'Trigger Disruption'}</span>
          </button>
        </div>

        {/* Live Simulation Results */}
        {simResult && (
          <div className="space-y-6 animate-fade-in">
            {/* Before vs After State Comparison Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Before State */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                    State Before Trigger
                  </span>
                  <span className="px-2 py-0.5 bg-gray-200 text-gray-700 text-[10px] font-bold rounded">
                    Baseline
                  </span>
                </div>
                <pre className="text-[11px] font-mono text-gray-700 overflow-x-auto p-2 bg-white rounded-xl border border-slate-200">
                  {JSON.stringify(simResult.before_state, null, 2)}
                </pre>
              </div>

              {/* After State */}
              <div className="p-4 rounded-2xl bg-rose-50/50 border border-rose-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-rose-700">
                    State After Disruption
                  </span>
                  <span className="px-2 py-0.5 bg-rose-200 text-rose-800 text-[10px] font-bold rounded">
                    Disrupted State
                  </span>
                </div>
                <pre className="text-[11px] font-mono text-rose-900 overflow-x-auto p-2 bg-white rounded-xl border border-rose-100">
                  {JSON.stringify(simResult.after_state, null, 2)}
                </pre>
              </div>
            </div>

            {/* Generated Recovery Plan & Feasible Options */}
            {simResult.recovery_options && simResult.recovery_options.length > 0 && (
              <div className="bg-[#FFF4E9]/60 p-5 rounded-2xl border border-peach space-y-3">
                <div className="flex items-center space-x-2">
                  <Sparkles size={18} className="text-[#F29877]" />
                  <h4 className="font-bold text-[#345873] text-sm">
                    Automated Recovery Engine: Feasible Alternatives
                  </h4>
                </div>
                <p className="text-xs text-gray-600">
                  The engine dynamically evaluates schedule conflicts, required equipment, and room capacity:
                </p>

                <div className="space-y-2.5">
                  {simResult.recovery_options.map((opt: any, idx: number) => (
                    <div
                      key={idx}
                      className="bg-white p-4 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                    >
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-gray-900 text-xs">{opt.title}</span>
                          <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded">
                            Score: {Math.round(opt.feasibility_score * 100)}%
                          </span>
                        </div>
                        <p className="text-gray-600 text-[11px] mt-1">{opt.description}</p>
                        <p className="text-[10px] text-gray-400 mt-0.5 italic">{opt.impact_assessment}</p>
                      </div>

                      <button
                        onClick={() => handleExecuteRecoveryOption(opt)}
                        className="px-4 py-2 bg-[#F29877] text-white rounded-xl font-bold hover:bg-[#e07b55] transition cursor-pointer self-start sm:self-auto shrink-0 shadow-2xs"
                      >
                        Execute Option
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Execution Confirmation Output */}
            {recoveryExecution && (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center space-x-3 text-xs text-emerald-800">
                <CheckCircle size={20} className="text-emerald-600 shrink-0" />
                <div>
                  <p className="font-bold">Recovery Execution Successful</p>
                  <p className="text-[11px] text-emerald-700">{recoveryExecution.message}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

