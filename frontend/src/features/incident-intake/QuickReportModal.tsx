import React, { useState } from 'react';
import { api } from '../../core/api/client';
import { Sparkles, Send, X, CheckCircle, AlertCircle } from 'lucide-react';

interface QuickReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitted?: () => void;
  defaultBuildingId?: string;
  defaultRoomId?: string;
}

export const QuickReportModal: React.FC<QuickReportModalProps> = ({
  isOpen,
  onClose,
  onSubmitted,
  defaultBuildingId,
  defaultRoomId
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('network');
  const [urgency, setUrgency] = useState('medium');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedReport, setSubmittedReport] = useState<any | null>(null);

  // Quick sample templates
  const sampleReports = [
    {
      title: "Wi-Fi down in Computer Lab A before exam",
      desc: "Wi-Fi isn't working in Computer Lab A. We have an exam in 30 minutes.",
      cat: "network",
      urg: "critical"
    },
    {
      title: "Projector lamp burnt out in Seminar 203",
      desc: "4K Laser Projector in Science Seminar Room 203 will not power on.",
      cat: "classroom",
      urg: "high"
    },
    {
      title: "Restroom faucet leaking in Humanities",
      desc: "Water is continuously running from the sensor tap on Floor 1.",
      cat: "cleanliness",
      urg: "medium"
    }
  ];

  const applySample = (sample: typeof sampleReports[0]) => {
    setTitle(sample.title);
    setDescription(sample.desc);
    setCategory(sample.cat);
    setUrgency(sample.urg);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !description) return;

    setIsSubmitting(true);
    try {
      const res = await api.submitReport({
        title,
        description,
        category,
        urgency,
        building_id: defaultBuildingId,
        room_id: defaultRoomId,
      });
      setSubmittedReport(res);
      // Deliberately do NOT call onSubmitted here. Parents typically refetch and
      // briefly unmount this modal, which would throw away the success screen and
      // remount an empty form. The refresh runs when the user dismisses the result.
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetAndClose = () => {
    const wasSubmitted = !!submittedReport;
    setTitle('');
    setDescription('');
    setCategory('network');
    setUrgency('medium');
    setSubmittedReport(null);
    onClose();
    if (wasSubmitted && onSubmitted) onSubmitted();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-3xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 relative animate-scale-up">
        <button
          onClick={handleResetAndClose}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-700 cursor-pointer"
        >
          <X size={20} />
        </button>

        {!submittedReport ? (
          <div>
            <div className="flex items-center space-x-2 text-[#345873] mb-1">
              <Sparkles size={20} className="text-[#F29877]" />
              <h3 className="text-xl font-extrabold">Campus Issue Intake</h3>
            </div>
            <p className="text-xs text-gray-500 mb-4">
              Describe the problem naturally. Our operational intake engine extracts facility entities, correlates duplicates, and alerts responders.
            </p>

            {/* Quick Presets */}
            <div className="mb-4 bg-[#FFF4E9]/60 p-3 rounded-2xl border border-peach/50">
              <p className="text-[11px] font-bold text-gray-600 mb-2 uppercase tracking-wide">
                Try Blueprint Test Cases:
              </p>
              <div className="flex flex-wrap gap-2">
                {sampleReports.map((s, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => applySample(s)}
                    className="text-[11px] bg-white text-[#345873] px-3 py-1.5 rounded-xl border border-slate-200 font-semibold hover:border-[#345873] transition cursor-pointer shadow-2xs"
                  >
                    {s.title}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Issue Headline</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Wi-Fi isn't working in Computer Lab A"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Details & Description</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Include specific room, symptoms, and if any examination or class is starting soon..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Category Override</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none capitalize font-medium"
                  >
                    <option value="network">Network / Wi-Fi</option>
                    <option value="classroom">Classroom / AV</option>
                    <option value="electrical">Electrical & Power</option>
                    <option value="cleanliness">Cleanliness & Hygiene</option>
                    <option value="safety">Safety & Hazard</option>
                    <option value="equipment">Specialized Equipment</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Reported Urgency</label>
                  <select
                    value={urgency}
                    onChange={(e) => setUrgency(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none capitalize font-medium"
                  >
                    <option value="critical">Critical (Exam / Active Class)</option>
                    <option value="high">High (Major Degradation)</option>
                    <option value="medium">Medium (Standard)</option>
                    <option value="low">Low (Cosmetic / Routine)</option>
                  </select>
                </div>
              </div>

              <div className="pt-2 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={handleResetAndClose}
                  className="px-4 py-2 text-xs font-bold text-gray-600 hover:text-gray-900 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2.5 bg-[#345873] hover:bg-[#284459] text-white rounded-xl text-xs font-bold flex items-center space-x-2 transition cursor-pointer shadow-sm disabled:opacity-50"
                >
                  <Send size={14} />
                  <span>{isSubmitting ? 'Processing...' : 'Submit to Engine'}</span>
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="text-center py-4">
            <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-3">
              <CheckCircle size={32} />
            </div>
            <h3 className="text-lg font-bold text-[#345873]">Report Dispatched Successfully</h3>
            <p className="text-xs text-gray-500 mt-1 mb-4">
              Ticket code <span className="font-mono font-bold text-[#345873]">{submittedReport.report_code}</span> has been processed and saved to the database.
            </p>

            {/* AI Extraction Preview */}
            {submittedReport.ai_extracted_meta && (
              <div className="bg-[#FFF4E9] p-4 rounded-2xl text-left border border-peach mb-5">
                <div className="flex items-center space-x-1.5 text-[#345873] font-bold text-xs mb-2">
                  <Sparkles size={14} className="text-[#F29877]" />
                  <span>AI Extraction & Classification Result</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-500 block text-[10px]">Category:</span>
                    <span className="font-semibold text-gray-800 capitalize">{submittedReport.category}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[10px]">Urgency:</span>
                    <span className="font-semibold text-gray-800 capitalize">{submittedReport.urgency}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[10px]">Engine Status:</span>
                    <span className="font-semibold text-gray-800 capitalize">{submittedReport.status}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[10px]">Correlation:</span>
                    <span className="font-semibold text-gray-800">
                      {submittedReport.incident_id ? 'Linked to Active Outage' : 'New Incident Stream'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={handleResetAndClose}
              className="w-full py-2.5 bg-[#345873] text-white rounded-xl text-xs font-bold hover:bg-[#284459] transition cursor-pointer"
            >
              Done & View Portal
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

