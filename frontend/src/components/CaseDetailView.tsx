import React, { useEffect, useState } from "react";
import { Application } from "../types";
import { apiRequest } from "../api";
import { ArrowLeft, Check, RotateCcw } from "lucide-react";

interface Props {
  appId: number;
  onBack: () => void;
}

export const CaseDetailView: React.FC<Props> = ({ appId, onBack }) => {
  const [app, setApp] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [reverting, setReverting] = useState(false);
  const [revertReason, setRevertReason] = useState("");
  const [revertError, setRevertError] = useState<string | null>(null);
  const [advancing, setAdvancing] = useState(false);

  const fetchDetail = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<Application>(`/applications/${appId}`);
      setApp(data);
    } catch (err: any) {
      alert("Error loading case: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [appId]);

  const handleAdvance = async () => {
    if (!app || !app.suggested_action) return;
    try {
      setAdvancing(true);
      await apiRequest(`/applications/${app.id}/advance`, {
        method: "POST",
        body: JSON.stringify({ target_stage: app.suggested_action }),
      });
      await fetchDetail();
    } catch (err: any) {
      alert("Advance failed: " + err.message);
    } finally {
      setAdvancing(false);
    }
  };

  const handleRevert = async (e: React.FormEvent) => {
    e.preventDefault();
    setRevertError(null);
    if (!revertReason.trim()) {
      setRevertError("A non-empty reason is mandatory to revert this application.");
      return;
    }

    try {
      setAdvancing(true);
      await apiRequest(`/applications/${appId}/revert`, {
        method: "POST",
        body: JSON.stringify({
          target_stage: "REVERTED_TO_DEFICIENCY",
          reason: revertReason,
        }),
      });
      setReverting(false);
      setRevertReason("");
      await fetchDetail();
    } catch (err: any) {
      setRevertError(err.message || "Revert failed");
    } finally {
      setAdvancing(false);
    }
  };

  if (loading || !app) {
    return <div className="p-8 text-slate-500 font-mono text-sm">Loading case details #{appId}...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-1.5 hover:bg-slate-100 rounded text-slate-600 border border-slate-300"
            id="btn-back-to-queue"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-base font-bold text-slate-900 font-mono">{app.application_number}</h1>
            <p className="text-xs text-slate-500">Academic Year: {app.academic_year} | Region ID: #{app.region_id}</p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {app.status === "IN_PROGRESS" && (
            <>
              <button
                onClick={() => setReverting(true)}
                className="bg-white hover:bg-red-50 text-red-700 border border-red-300 px-3 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 cursor-pointer"
                id="btn-open-revert"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Revert to Deficiency
              </button>

              {app.suggested_action && (
                <button
                  onClick={handleAdvance}
                  disabled={advancing}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  id="btn-confirm-advance"
                >
                  <Check className="w-3.5 h-3.5" />
                  Approve Suggested Action: {app.suggested_action}
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Revert Modal Dialog */}
      {reverting && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded border border-slate-300 p-6 max-w-md w-full shadow-lg">
            <h3 className="text-sm font-bold text-slate-900 mb-2">Revert Application with Deficiency Reason</h3>
            <p className="text-xs text-slate-500 mb-4">
              AICTE regulatory standard: Every stage revert requires an explicit, audited reason before communication to the institution.
            </p>

            <form onSubmit={handleRevert} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Deficiency / Revert Reason <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={revertReason}
                  onChange={(e) => setRevertReason(e.target.value)}
                  placeholder="e.g. Inadequate laboratory equipment and missing occupancy certificate for Block C."
                  rows={4}
                  className="w-full text-xs border border-slate-300 rounded p-2.5 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  id="revert-reason-input"
                />
              </div>

              {revertError && (
                <div className="p-2 bg-red-50 border border-red-200 text-red-700 text-xs rounded" id="revert-error-msg">
                  {revertError}
                </div>
              )}

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setReverting(false);
                    setRevertReason("");
                    setRevertError(null);
                  }}
                  className="px-3 py-1.5 rounded text-xs text-slate-600 border border-slate-300 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={advancing}
                  className="px-4 py-1.5 rounded text-xs text-white bg-red-600 hover:bg-red-700 disabled:opacity-50"
                  id="btn-submit-revert"
                >
                  Confirm Revert
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Case Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase">Current Stage</div>
          <div className="text-base font-bold text-slate-900 mt-1 font-mono">{app.current_stage}</div>
          <div className="text-xs text-slate-400 mt-1">Status: {app.status}</div>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase">Engine Suggested Action</div>
          <div className="text-base font-bold text-blue-700 mt-1 font-mono">
            {app.suggested_action || "Awaiting Human Decision"}
          </div>
          <div className="text-xs text-slate-400 mt-1">Authorized role verification active</div>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase">Submission Timestamp</div>
          <div className="text-sm font-semibold text-slate-900 mt-1 font-mono">
            {new Date(app.created_at).toLocaleString("en-IN", { timeZone: "UTC" })} UTC
          </div>
          <div className="text-xs text-slate-400 mt-1">Deterministically audited</div>
        </div>
      </div>

      {/* Associated Obligations */}
      <div className="bg-white border border-slate-200 rounded shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50">
          <h2 className="text-sm font-bold text-slate-800">Tracked Obligations for Application</h2>
          <p className="text-xs text-slate-500">All stage SLAs, EVC reports, and undertakings for this record</p>
        </div>

        <div className="p-4">
          {app.obligations && app.obligations.length > 0 ? (
            <div className="divide-y divide-slate-100 font-mono text-xs">
              {app.obligations.map((ob) => (
                <div key={ob.id} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="font-sans font-medium text-slate-900">{ob.title}</div>
                    <div className="text-slate-500 text-xs">
                      Type: {ob.obligation_type} | Due: {new Date(ob.due_at).toLocaleDateString("en-IN", { timeZone: "UTC" })}
                    </div>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-xs border ${
                      ob.status === "SATISFIED"
                        ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                        : ob.status === "BREACHED"
                        ? "bg-red-50 text-red-800 border-red-300 font-bold"
                        : "bg-amber-50 text-amber-800 border-amber-300"
                    }`}
                  >
                    {ob.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-slate-400 text-xs py-4 text-center">No open obligations for this case.</div>
          )}
        </div>
      </div>
    </div>
  );
};
