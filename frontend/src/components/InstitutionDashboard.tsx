import React, { useEffect, useState } from "react";
import { Application, Obligation } from "../types";
import { apiRequest } from "../api";
import { Upload, CheckCircle2 } from "lucide-react";

export const InstitutionDashboard: React.FC = () => {
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<number | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [obs, apps] = await Promise.all([
        apiRequest<Obligation[]>("/obligations"),
        apiRequest<Application[]>("/applications"),
      ]);
      setObligations(obs);
      setApplications(apps);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSatisfy = async (id: number) => {
    try {
      setUploading(id);
      await apiRequest(`/obligations/${id}/satisfy`, { method: "POST" });
      await loadData();
    } catch (err: any) {
      alert("Failed to submit compliance: " + err.message);
    } finally {
      setUploading(null);
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-500 font-mono text-sm">Loading institutional compliance records...</div>;
  }

  const app = applications[0];

  return (
    <div className="p-6 space-y-6">
      {/* Institution Banner */}
      <div className="bg-white border border-slate-200 p-5 rounded shadow-xs flex justify-between items-center">
        <div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200">
            AICTE AFFILIATED TECHNICAL CAMPUS
          </span>
          <h1 className="text-lg font-bold text-slate-900 mt-1">Institutional Compliance & Document Upload Portal</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Application Status: <strong className="text-slate-800">{app?.status || "IN_PROGRESS"}</strong> (Stage: {app?.current_stage || "N/A"})
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-500">Application Reference</div>
          <div className="font-mono text-sm font-bold text-slate-800">{app?.application_number || "AICTE-2026-APP"}</div>
        </div>
      </div>

      {/* Deadlines & Obligations Table */}
      <div className="bg-white border border-slate-200 rounded shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
          <div>
            <h2 className="text-sm font-bold text-slate-800">My Mandatory Compliance Deadlines</h2>
            <p className="text-xs text-slate-500">Document submissions, deficiency rectifications, and lease renewal undertakings</p>
          </div>
          <span className="text-xs font-mono text-slate-500">n = {obligations.length} compliance items</span>
        </div>

        {obligations.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">No pending compliance obligations at this time.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-100 text-slate-600 font-semibold uppercase">
                  <th className="py-2.5 px-4">Compliance Requirement</th>
                  <th className="py-2.5 px-4">Obligation Type</th>
                  <th className="py-2.5 px-4">Deadline (UTC)</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4 text-right">Upload Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 font-mono">
                {obligations.map((ob) => (
                  <tr key={ob.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-sans font-medium text-slate-900">
                      <div>{ob.title}</div>
                      {ob.description && <div className="text-xs text-slate-500 mt-0.5">{ob.description}</div>}
                    </td>
                    <td className="py-3 px-4 text-slate-600">{ob.obligation_type}</td>
                    <td className="py-3 px-4 text-slate-900 font-semibold">
                      {new Date(ob.due_at).toLocaleDateString("en-IN", { timeZone: "UTC" })}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-xs border ${
                          ob.status === "SATISFIED"
                            ? "bg-emerald-50 text-emerald-800 border-emerald-300 font-medium"
                            : ob.status === "BREACHED"
                            ? "bg-red-50 text-red-800 border-red-300 font-bold"
                            : "bg-amber-50 text-amber-800 border-amber-300"
                        }`}
                      >
                        {ob.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {ob.status !== "SATISFIED" ? (
                        <button
                          onClick={() => handleSatisfy(ob.id)}
                          disabled={uploading === ob.id}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded inline-flex items-center gap-1 font-sans text-xs font-medium cursor-pointer disabled:opacity-50"
                          id={`btn-satisfy-${ob.id}`}
                        >
                          <Upload className="w-3 h-3" />
                          {uploading === ob.id ? "Submitting..." : "Submit Evidence"}
                        </button>
                      ) : (
                        <span className="text-emerald-700 inline-flex items-center gap-1 font-sans text-xs">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Satisfied
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
