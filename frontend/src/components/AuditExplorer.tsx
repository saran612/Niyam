import React, { useEffect, useState } from "react";
import { AuditLogItem } from "../types";
import { apiRequest } from "../api";
import { ShieldCheck, ShieldAlert, RefreshCw } from "lucide-react";

export const AuditExplorer: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [verification, setVerification] = useState<{
    is_valid: boolean;
    total_logs: number;
    corrupted_log_id?: number | null;
    error_message?: string | null;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const [logsData, verifyData] = await Promise.all([
        apiRequest<AuditLogItem[]>("/audit/logs?limit=50"),
        apiRequest<{ is_valid: boolean; total_logs: number; corrupted_log_id?: number; error_message?: string }>("/audit/verify"),
      ]);
      setLogs(logsData);
      setVerification(verifyData);
    } catch (err: any) {
      alert("Failed to load audit trail: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  if (loading) {
    return <div className="p-8 text-slate-500 font-mono text-sm">Validating cryptographic hash chain...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Integrity Status Card */}
      <div
        className={`p-5 rounded border ${
          verification?.is_valid
            ? "bg-emerald-50/60 border-emerald-300 text-emerald-950"
            : "bg-red-50 border-red-300 text-red-950"
        } flex justify-between items-center`}
      >
        <div className="flex items-center gap-3">
          {verification?.is_valid ? (
            <ShieldCheck className="w-8 h-8 text-emerald-600" />
          ) : (
            <ShieldAlert className="w-8 h-8 text-red-600" />
          )}
          <div>
            <h2 className="text-sm font-bold">
              {verification?.is_valid
                ? "Cryptographic Audit Chain Intact & Verified"
                : "TAMPER DETECTED IN AUDIT LOGS"}
            </h2>
            <p className="text-xs opacity-90 mt-0.5 font-mono">
              SHA-256 hash chaining across {verification?.total_logs} in-transaction mutation records.
              {verification?.error_message && ` Anomaly: ${verification.error_message}`}
            </p>
          </div>
        </div>

        <button
          onClick={loadLogs}
          className="bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 px-3 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 cursor-pointer shadow-2xs"
          id="btn-reverify-audit"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Re-verify Chain
        </button>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-slate-200 rounded shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50">
          <h3 className="text-sm font-bold text-slate-800">Immutable Audit Trail</h3>
          <p className="text-xs text-slate-500">Every state mutation, clock advance, and transition recorded in same DB transaction</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-100 text-slate-600 font-semibold uppercase">
                <th className="py-2.5 px-4">Action</th>
                <th className="py-2.5 px-4">Entity</th>
                <th className="py-2.5 px-4">Timestamp (UTC)</th>
                <th className="py-2.5 px-4">Current Hash (SHA-256)</th>
                <th className="py-2.5 px-4">Previous Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-bold text-slate-900">{log.action}</td>
                  <td className="py-3 px-4 text-slate-600">
                    {log.entity_type} #{log.entity_id}
                  </td>
                  <td className="py-3 px-4 text-slate-600">
                    {new Date(log.timestamp).toLocaleTimeString("en-IN", { timeZone: "UTC" })}
                  </td>
                  <td className="py-3 px-4 text-blue-700" title={log.hash}>
                    {log.hash.slice(0, 16)}...
                  </td>
                  <td className="py-3 px-4 text-slate-400" title={log.prev_hash}>
                    {log.prev_hash.slice(0, 16)}...
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
