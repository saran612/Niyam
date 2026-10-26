import React, { useEffect, useState } from "react";
import { AuditLogItem } from "../types";
import { apiRequest } from "../api";
import { ShieldCheck, ShieldAlert, RefreshCw, Search, ChevronRight, ChevronDown } from "lucide-react";

export const AuditExplorer: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [verification, setVerification] = useState<{
    is_valid: boolean;
    total_logs: number;
    corrupted_log_id?: number | null;
    error_message?: string | null;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedLogId, setExpandedLogId] = useState<number | null>(null);

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const [logsData, verifyData] = await Promise.all([
        apiRequest<AuditLogItem[]>("/audit/logs?limit=100"),
        apiRequest<{ is_valid: boolean; total_logs: number; corrupted_log_id?: number; error_message?: string }>("/audit/verify"),
      ]);
      setLogs(logsData);
      setVerification(verifyData);
    } catch (err: any) {
      setError(err.message || "Failed to load audit trail");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const filteredLogs = logs.filter((log) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      log.action.toLowerCase().includes(q) ||
      log.entity_type.toLowerCase().includes(q) ||
      String(log.entity_id).toLowerCase().includes(q) ||
      log.hash.toLowerCase().includes(q) ||
      JSON.stringify(log.payload).toLowerCase().includes(q)
    );
  });

  if (loading) {
    return (
      <div className="p-8 text-slate-500 font-mono text-xs flex items-center gap-2" id="audit-loading">
        <RefreshCw className="w-4 h-4 animate-spin text-slate-400" />
        Verifying cryptographic SHA-256 hash chain and loading immutable audit trail...
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Integrity Verification Card */}
      <div
        className={`p-4 rounded border ${
          verification?.is_valid
            ? "bg-emerald-50/70 border-emerald-300 text-emerald-950"
            : "bg-red-50 border-red-300 text-red-950"
        } flex flex-wrap gap-4 items-center justify-between`}
      >
        <div className="flex items-center gap-3">
          {verification?.is_valid ? (
            <ShieldCheck className="w-7 h-7 text-emerald-600 shrink-0" />
          ) : (
            <ShieldAlert className="w-7 h-7 text-red-600 shrink-0" />
          )}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider">
              {verification?.is_valid
                ? "Cryptographic Audit Chain Intact & Verified"
                : "TAMPER DETECTED IN AUDIT LOGS"}
            </h2>
            <p className="text-xs font-mono opacity-90 mt-0.5">
              Verified SHA-256 hash chaining across {verification?.total_logs ?? logs.length} in-transaction mutation records.
              {verification?.error_message && ` Anomaly: ${verification.error_message}`}
            </p>
          </div>
        </div>

        <button
          onClick={loadLogs}
          className="bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 px-3 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 cursor-pointer shadow-xs transition-colors"
          id="btn-reverify-audit"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Re-verify Chain
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded" id="audit-error-banner">
          <strong>Error loading logs:</strong> {error}
        </div>
      )}

      {/* Logs Table Card */}
      <div className="bg-white border border-slate-200 rounded shadow-xs overflow-hidden">
        <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50 flex flex-wrap gap-4 items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Immutable Audit Trail</h3>
            <p className="text-2xs text-slate-500 font-sans mt-0.5">
              Every state mutation, workflow transition, and clock advance written in-transaction
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter action, entity, payload..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-slate-500 bg-white font-mono w-60"
                id="audit-filter-input"
              />
            </div>
            <span className="text-2xs font-mono text-slate-500 bg-slate-100 px-2 py-1 rounded border border-slate-200">
              Showing {filteredLogs.length} of {logs.length}
            </span>
          </div>
        </div>

        {filteredLogs.length === 0 ? (
          <div className="p-10 text-center text-slate-400 text-xs font-mono" id="audit-empty-state">
            {logs.length === 0 ? "No audit records found in database." : "No records matching current filter."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono" id="audit-logs-table">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-600 font-semibold text-2xs uppercase">
                  <th className="py-2 px-4 w-8"></th>
                  <th className="py-2 px-4">Action</th>
                  <th className="py-2 px-4">Entity</th>
                  <th className="py-2 px-4">Timestamp (UTC)</th>
                  <th className="py-2 px-4">Current Hash (SHA-256)</th>
                  <th className="py-2 px-4">Previous Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {filteredLogs.map((log) => {
                  const isExpanded = expandedLogId === log.id;
                  const dateObj = new Date(log.timestamp);
                  const formattedDate = dateObj.toLocaleDateString("en-IN", { timeZone: "UTC" });
                  const formattedTime = dateObj.toLocaleTimeString("en-IN", { timeZone: "UTC" });

                  return (
                    <React.Fragment key={log.id}>
                      <tr
                        className={`hover:bg-slate-50/80 cursor-pointer transition-colors ${
                          isExpanded ? "bg-slate-50/90" : ""
                        }`}
                        onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                      >
                        <td className="py-2.5 px-4 text-slate-400 text-center">
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                        </td>
                        <td className="py-2.5 px-4 font-bold text-slate-900">
                          <span className="px-1.5 py-0.5 bg-slate-100 rounded text-2xs border border-slate-200">
                            {log.action}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 text-slate-700">
                          <span className="font-semibold text-slate-900">{log.entity_type}</span>{" "}
                          <span className="text-slate-500">#{log.entity_id}</span>
                        </td>
                        <td className="py-2.5 px-4 text-slate-600 whitespace-nowrap text-2xs">
                          {formattedDate} {formattedTime}
                        </td>
                        <td className="py-2.5 px-4 text-blue-700 font-medium" title={log.hash}>
                          {log.hash.slice(0, 16)}...
                        </td>
                        <td className="py-2.5 px-4 text-slate-400" title={log.prev_hash}>
                          {log.prev_hash.slice(0, 16)}...
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr className="bg-slate-50/90">
                          <td colSpan={6} className="px-10 py-3 border-t border-slate-200/80">
                            <div className="space-y-2 text-2xs">
                              <div className="flex items-center gap-4 text-slate-500">
                                <span>Record ID: <strong className="text-slate-800">#{log.id}</strong></span>
                                <span>Actor ID: <strong className="text-slate-800">{log.actor_id ?? "SYSTEM"}</strong></span>
                                <span className="truncate">Full Hash: <code className="text-blue-700 bg-white px-1.5 py-0.5 rounded border border-slate-200">{log.hash}</code></span>
                              </div>
                              <div>
                                <span className="font-semibold text-slate-700 block mb-1">Payload:</span>
                                <pre className="bg-slate-900 text-slate-100 p-3 rounded font-mono text-2xs overflow-x-auto leading-relaxed">
                                  {JSON.stringify(log.payload, null, 2)}
                                </pre>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
