import React, { useState } from 'react';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { GraduationCap, FileText, CheckCircle2, Clock, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

const ADMISSIONS_DATA = [
  { id: 'adm-001', programme: 'B.Tech Computer Science', type: 'Undergraduate', deadline: '2027-01-15', status: 'open', seats: 120, filled: 94 },
  { id: 'adm-002', programme: 'M.Tech Data Science', type: 'Postgraduate', deadline: '2027-01-20', status: 'open', seats: 60, filled: 41 },
  { id: 'adm-003', programme: 'B.Tech Electronics & Comm.', type: 'Undergraduate', deadline: '2027-01-15', status: 'open', seats: 80, filled: 73 },
  { id: 'adm-004', programme: 'MBA Technology Management', type: 'Postgraduate', deadline: '2026-12-30', status: 'closing_soon', seats: 45, filled: 38 },
  { id: 'adm-005', programme: 'PhD Artificial Intelligence', type: 'Doctoral', deadline: '2026-11-30', status: 'closing_soon', seats: 12, filled: 9 },
  { id: 'adm-006', programme: 'B.Sc Physics', type: 'Undergraduate', deadline: '2027-02-01', status: 'open', seats: 60, filled: 22 },
  { id: 'adm-007', programme: 'M.Sc Biotechnology', type: 'Postgraduate', deadline: '2026-11-15', status: 'closed', seats: 40, filled: 40 },
];

const MY_DOCUMENTS = [
  { id: 'doc-1', name: '10th Grade Marksheet', required: true, status: 'verified' },
  { id: 'doc-2', name: '12th Grade Marksheet', required: true, status: 'verified' },
  { id: 'doc-3', name: 'Entrance Exam Scorecard', required: true, status: 'pending' },
  { id: 'doc-4', name: 'Passport-size Photographs (×4)', required: true, status: 'missing' },
  { id: 'doc-5', name: 'Character Certificate', required: false, status: 'verified' },
  { id: 'doc-6', name: 'Medical Fitness Certificate', required: true, status: 'pending' },
];

const TIMELINE = [
  { event: 'Application Portal Opens', date: '1 Oct 2026', done: true },
  { event: 'Document Submission Deadline', date: '15 Nov 2026', done: false },
  { event: 'Entrance Exam / Interview', date: '25 Nov 2026', done: false },
  { event: 'Merit List Published', date: '5 Dec 2026', done: false },
  { event: 'Fee Payment & Confirmation', date: '15 Dec 2026', done: false },
  { event: 'Semester Commencement', date: '10 Jan 2027', done: false },
];

export const StudentAdmissionsView: React.FC = () => {
  const [expandFaq, setExpandFaq] = useState<string | null>(null);

  const progCols = [
    { header: 'Programme', accessor: 'programme' as const, render: (r: any) => <span className="font-bold text-sm text-[#345873]">{r.programme}</span> },
    { header: 'Type', accessor: 'type' as const, render: (r: any) => <span className="text-xs text-gray-500 font-semibold">{r.type}</span> },
    { header: 'Deadline', accessor: 'deadline' as const, render: (r: any) => <span className="font-mono text-xs text-gray-600">{r.deadline}</span> },
    {
      header: 'Status', accessor: 'status' as const,
      render: (r: any) => <StatusBadge status={r.status} />
    },
    {
      header: 'Seats Filled', accessor: 'filled' as const,
      render: (r: any) => {
        const pct = Math.round((r.filled / r.seats) * 100);
        return (
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-slate-100 rounded-full h-1.5 w-20">
              <div
                className="h-1.5 rounded-full transition-all"
                style={{ width: `${pct}%`, backgroundColor: pct > 90 ? '#ef4444' : pct > 70 ? '#f59e0b' : '#10b981' }}
              />
            </div>
            <span className="text-xs font-bold text-gray-500">{r.filled}/{r.seats}</span>
          </div>
        );
      }
    },
  ];

  const docCols = [
    { header: 'Document', accessor: 'name' as const, render: (r: any) => <span className="font-semibold text-sm text-gray-800">{r.name}</span> },
    { header: 'Required', accessor: 'required' as const, render: (r: any) => <span className={`text-xs font-bold ${r.required ? 'text-red-500' : 'text-gray-400'}`}>{r.required ? 'Mandatory' : 'Optional'}</span> },
    { header: 'Status', accessor: 'status' as const, render: (r: any) => <StatusBadge status={r.status} /> },
  ];

  const faqs = [
    { q: 'What is the eligibility for B.Tech admission?', a: 'Candidates must have passed 10+2 with Physics, Chemistry and Mathematics with a minimum aggregate of 60% and a valid JEE score.' },
    { q: 'Is there a management quota?', a: 'Yes. 15% of seats are reserved under management quota. Contact the admissions office for the NRI/management fee structure.' },
    { q: 'Can I change my programme after admission?', a: 'Programme changes are allowed within the first 30 days of the semester, subject to seat availability and a valid reason submitted to the Academic Dean.' },
    { q: 'When will the merit list be published?', a: 'The merit list is published on 5 Dec 2026 on the student portal and notice board.' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center space-x-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div className="w-12 h-12 rounded-2xl bg-[#345873]/10 text-[#345873] flex items-center justify-center">
          <GraduationCap size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Admissions</h1>
          <p className="text-xs text-gray-500 mt-0.5">Programme listings, document tracker and admission timeline</p>
        </div>
      </div>


      {/* Admission Timeline */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs p-6">
        <h3 className="font-extrabold text-sm text-[#345873] mb-4">Admission Timeline — AY 2026–27</h3>
        <div className="flex flex-wrap gap-4">
          {TIMELINE.map((t, i) => (
            <div key={i} className="flex items-center space-x-2">
              {t.done
                ? <CheckCircle2 size={16} className="text-emerald-500 shrink-0" />
                : <Clock size={16} className="text-amber-400 shrink-0" />}
              <div>
                <p className="text-xs font-bold text-gray-700">{t.event}</p>
                <p className="text-[11px] text-gray-400">{t.date}</p>
              </div>
              {i < TIMELINE.length - 1 && <span className="hidden sm:block text-gray-200 font-bold px-2">→</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Open Programmes */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="font-extrabold text-sm text-[#345873]">Available Programmes & Seat Matrix</h3>
        </div>
        <div className="p-4">
          <DataTable columns={progCols} data={ADMISSIONS_DATA} keyField="id" emptyMessage="No programmes available." />
        </div>
      </div>

      {/* My Documents */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-extrabold text-sm text-[#345873]">My Document Checklist</h3>
          <span className="text-xs text-gray-400">
            {MY_DOCUMENTS.filter(d => d.status === 'verified').length}/{MY_DOCUMENTS.length} verified
          </span>
        </div>
        <div className="p-4">
          <DataTable columns={docCols} data={MY_DOCUMENTS} keyField="id" emptyMessage="No documents found." />
        </div>
      </div>

      {/* FAQ */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs p-6 space-y-3">
        <h3 className="font-extrabold text-sm text-[#345873] mb-2">Frequently Asked Questions</h3>
        {faqs.map((faq, i) => (
          <div key={i} className="border border-slate-100 rounded-2xl overflow-hidden">
            <button
              onClick={() => setExpandFaq(expandFaq === faq.q ? null : faq.q)}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 transition"
            >
              <span className="text-sm font-bold text-gray-700">{faq.q}</span>
              {expandFaq === faq.q ? <ChevronUp size={16} className="text-gray-400 shrink-0" /> : <ChevronDown size={16} className="text-gray-400 shrink-0" />}
            </button>
            {expandFaq === faq.q && (
              <div className="px-4 pb-3 text-xs text-gray-500 leading-relaxed border-t border-slate-100">{faq.a}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

