import React, { useEffect, useState } from "react";
import { Application, Obligation } from "../types";
import { apiRequest } from "../api";
import { ArrowRight } from "lucide-react";

interface Props {
  onSelectApplication: (id: number) => void;
}

export const RegionalDashboard: React.FC<Props> = ({ onSelectApplication }) => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [apps, obs] = await Promise.all([
        apiRequest<Application[]>("/applications"),
        apiRequest<Obligation[]>("/obligations"),
      ]);
      setApplications(apps);
      setObligations(obs);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const pendingObs = obligations.filter((o) => o.status === "PENDING");
  const breachedObs = obligations.filter((o) => o.status === "BREACHED");

  if (loading) {
    return (
      <div className="p-8 text-slate-500 font-mono text-sm" id="loading-state">
        Loading regional queue and compliance obligations...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 text-red-700 text-sm rounded m-6" id="error-state">
        <strong>Error:</strong> {error}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Assigned Applications</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{applications.length}</div>
          <div className="text-xs text-slate-400 mt-1">Under regional jurisdiction</div>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Stage SLAs</div>
          <div className="text-2xl font-bold text-blue-700 mt-1">{pendingObs.length}</div>
          <div className="text-xs text-slate-400 mt-1">Pending review / scrutiny</div>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Breached Deadlines</div>
          <div className="text-2xl font-bold text-red-600 mt-1">{breachedObs.length}</div>
          <div className="text-xs text-slate-400 mt-1">Requiring immediate escalation</div>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Scrutiny Backlog</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {applications.filter((a) => a.current_stage === "SCRUTINY_PENDING").length}
          </div>
          <div className="text-xs text-slate-400 mt-1">In scrutiny committee queue</div>
        </div>
      </div>

      {/* Main Queue Table */}
      <div className="bg-white border border-slate-200 rounded shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
          <div>
            <h2 className="text-sm font-bold text-slate-800">Regional Application Queue</h2>
            <p className="text-xs text-slate-500">Applications and current stage progress requiring regional action</p>
          </div>
          <span className="text-xs font-mono text-slate-500">n = {applications.length} applications</span>
        </div>

        {applications.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm" id="empty-state">
            No applications currently assigned to this region.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider">
                  <th className="py-2.5 px-4">Application Number</th>
                  <th className="py-2.5 px-4">Academic Year</th>
                  <th className="py-2.5 px-4">Current Stage</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4">Suggested Action</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 font-mono">
                {applications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">{app.application_number}</td>
                    <td className="py-3 px-4 text-slate-600">{app.academic_year}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-800 border border-slate-300">
                        {app.current_stage}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-xs border ${
                          app.status === "APPROVED"
                            ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                            : app.status === "REJECTED"
                            ? "bg-red-50 text-red-800 border-red-300"
                            : "bg-blue-50 text-blue-800 border-blue-300"
                        }`}
                      >
                        {app.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {app.suggested_action ? (
                        <span className="text-slate-800 font-medium">{app.suggested_action}</span>
                      ) : (
                        <span className="text-slate-400">None</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onSelectApplication(app.id)}
                        className="bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 px-3 py-1 rounded inline-flex items-center gap-1 font-sans text-xs font-medium cursor-pointer"
                        id={`btn-view-${app.id}`}
                      >
                        View Case
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Obligations & Escalation List */}
      <div className="bg-white border border-slate-200 rounded shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
          <div>
            <h2 className="text-sm font-bold text-slate-800">Assigned Compliance Obligations (Single Obligation Table)</h2>
            <p className="text-xs text-slate-500">Stage SLAs, undertakings, and lease renewals tracked by engine</p>
          </div>
          <span className="text-xs font-mono text-slate-500">n = {obligations.length} total obligations</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider">
                <th className="py-2.5 px-4">Title / Scope</th>
                <th className="py-2.5 px-4">Type</th>
                <th className="py-2.5 px-4">Owner Role</th>
                <th className="py-2.5 px-4">Due Date (UTC)</th>
                <th className="py-2.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 font-mono">
              {obligations.slice(0, 15).map((ob) => (
                <tr key={ob.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-sans font-medium text-slate-900">{ob.title}</td>
                  <td className="py-3 px-4 text-slate-600">{ob.obligation_type}</td>
                  <td className="py-3 px-4 text-slate-600">{ob.owner_role}</td>
                  <td className="py-3 px-4 text-slate-900">
                    {new Date(ob.due_at).toLocaleDateString("en-IN", { timeZone: "UTC" })}
                  </td>
                  <td className="py-3 px-4">
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
