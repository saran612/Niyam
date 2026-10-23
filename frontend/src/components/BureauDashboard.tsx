import React, { useEffect, useState } from "react";
import { Application, Obligation } from "../types";
import { apiRequest } from "../api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { ShieldAlert, Layers } from "lucide-react";

export const BureauDashboard: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const [apps, obs] = await Promise.all([
          apiRequest<Application[]>("/applications"),
          apiRequest<Obligation[]>("/obligations"),
        ]);
        setApplications(apps);
        setObligations(obs);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="p-8 text-slate-500 font-mono text-sm">Aggregating national compliance metrics...</div>;
  }

  // Calculate Stage distribution
  const stageCounts: Record<string, number> = {};
  applications.forEach((a) => {
    stageCounts[a.current_stage] = (stageCounts[a.current_stage] || 0) + 1;
  });
  const chartData = Object.entries(stageCounts).map(([stage, count]) => ({
    stage: stage.replace("_PENDING", "").replace("APPLICATION_", ""),
    count,
  }));

  const totalBreached = obligations.filter((o) => o.status === "BREACHED").length;
  const totalPending = obligations.filter((o) => o.status === "PENDING").length;

  return (
    <div className="p-6 space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 text-white p-5 rounded border border-slate-800 flex justify-between items-center">
        <div>
          <h1 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-400" />
            AICTE Approvals Bureau - National Pendency & Escalation Monitor
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time compliance monitoring across all 5 regional offices (CRO, NRO, NWRO, SRO, WRO)
          </p>
        </div>
        <div className="text-right font-mono">
          <div className="text-xs text-slate-400">Total Applications Tracked</div>
          <div className="text-xl font-bold text-blue-400">n = {applications.length}</div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase">National Stage Pendency</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{totalPending} Active Obligations</div>
          <p className="text-xs text-slate-500 mt-1">Under strict business-day SLA tracking</p>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1.5 text-red-600">
            <ShieldAlert className="w-4 h-4" />
            National SLA Breaches
          </div>
          <div className="text-2xl font-bold text-red-600 mt-1">{totalBreached} Escalated</div>
          <p className="text-xs text-slate-500 mt-1">Triggered OVERDUE ladder to Bureau & Admin</p>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded shadow-xs">
          <div className="text-xs font-semibold text-slate-500 uppercase">Average Approval Throughput</div>
          <div className="text-2xl font-bold text-emerald-700 mt-1">
            {applications.filter((a) => a.status === "APPROVED").length} Approved
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {applications.filter((a) => a.status === "REJECTED").length} Rejected after committee hearing
          </p>
        </div>
      </div>

      {/* Stage Distribution Chart */}
      <div className="bg-white border border-slate-200 p-5 rounded shadow-xs">
        <h2 className="text-sm font-bold text-slate-800 mb-1">Application Stage Distribution & Bottleneck Analysis</h2>
        <p className="text-xs text-slate-500 mb-4">Volume of cases distributed by workflow phase</p>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <XAxis dataKey="stage" tick={{ fontSize: 11, fill: "#475569" }} />
              <YAxis tick={{ fontSize: 11, fill: "#475569" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "4px",
                  color: "#fff",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="count" fill="#2563eb" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Critical Escalations Table */}
      <div className="bg-white border border-slate-200 rounded shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 bg-red-50/50 flex justify-between items-center">
          <div>
            <h2 className="text-sm font-bold text-red-900 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              Critical Escalations Requiring Bureau Intervention
            </h2>
            <p className="text-xs text-red-700">Breached deadlines and overdue regional scrutiny reviews</p>
          </div>
          <span className="text-xs font-mono text-red-700">n = {totalBreached}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-100 text-slate-600 font-semibold uppercase">
                <th className="py-2.5 px-4">Obligation Title</th>
                <th className="py-2.5 px-4">Region ID</th>
                <th className="py-2.5 px-4">Assigned Role</th>
                <th className="py-2.5 px-4">Original SLA Due</th>
                <th className="py-2.5 px-4">Current Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 font-mono">
              {obligations
                .filter((o) => o.status === "BREACHED")
                .slice(0, 10)
                .map((ob) => (
                  <tr key={ob.id} className="hover:bg-red-50/30">
                    <td className="py-3 px-4 font-sans font-medium text-slate-900">{ob.title}</td>
                    <td className="py-3 px-4 text-slate-600">Region #{ob.region_id}</td>
                    <td className="py-3 px-4 text-slate-600">{ob.owner_role}</td>
                    <td className="py-3 px-4 text-red-700 font-bold">
                      {new Date(ob.due_at).toLocaleDateString("en-IN", { timeZone: "UTC" })}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-xs bg-red-100 text-red-800 border border-red-300 font-semibold">
                        BREACHED
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
