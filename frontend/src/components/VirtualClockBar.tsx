import React, { useState } from "react";
import { ClockStatus } from "../types";
import { apiRequest } from "../api";
import { Play, RotateCcw } from "lucide-react";

interface Props {
  clock: ClockStatus | null;
  onClockChanged: () => void;
}

export const VirtualClockBar: React.FC<Props> = ({ clock, onClockChanged }) => {
  const [advancing, setAdvancing] = useState(false);
  const [selectedAdvance, setSelectedAdvance] = useState(86400); // 1 day default

  const handleAdvance = async () => {
    try {
      setAdvancing(true);
      await apiRequest("/admin/clock/advance", {
        method: "POST",
        body: JSON.stringify({ seconds: selectedAdvance }),
      });
      onClockChanged();
    } catch (err: any) {
      alert("Failed to advance clock: " + err.message);
    } finally {
      setAdvancing(false);
    }
  };

  const handleReset = async () => {
    try {
      setAdvancing(true);
      await apiRequest("/admin/clock/reset", { method: "POST" });
      onClockChanged();
    } catch (err: any) {
      alert("Failed to reset clock: " + err.message);
    } finally {
      setAdvancing(false);
    }
  };

  if (!clock) return null;

  const daysOffset = Math.round(clock.offset_seconds / 86400);

  return (
    <div className="bg-slate-900 border-b border-slate-800 text-slate-300 px-6 py-2.5 flex flex-wrap items-center justify-between text-xs font-mono">
      <div className="flex items-center gap-4">
        <span className="font-semibold text-slate-100 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          SIMULATED CLOCK
        </span>
        <span className="text-slate-400">
          Current: <strong className="text-white">{new Date(clock.current_time).toLocaleString("en-IN", { timeZone: "UTC" })} UTC</strong>
        </span>
        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
          Offset: {daysOffset >= 0 ? `+${daysOffset}d` : `${daysOffset}d`} ({clock.offset_seconds}s)
        </span>
      </div>

      <div className="flex items-center gap-2 mt-1 sm:mt-0">
        <select
          value={selectedAdvance}
          onChange={(e) => setSelectedAdvance(Number(e.target.value))}
          className="bg-slate-800 border border-slate-700 text-slate-200 px-2 py-1 rounded focus:outline-none focus:ring-1 focus:ring-slate-500"
          id="clock-advance-select"
        >
          <option value={86400}>+1 Business Day (24h)</option>
          <option value={604800}>+7 Calendar Days (T-7 alert)</option>
          <option value={1209600}>+14 Days (T-0 / Breach)</option>
          <option value={2592000}>+30 Days (T-30 / Overdue)</option>
        </select>

        <button
          onClick={handleAdvance}
          disabled={advancing}
          id="btn-advance-clock"
          className="bg-slate-700 hover:bg-slate-600 text-white px-3 py-1 rounded flex items-center gap-1 border border-slate-600 disabled:opacity-50"
        >
          <Play className="w-3.5 h-3.5" />
          Advance
        </button>

        <button
          onClick={handleReset}
          disabled={advancing}
          id="btn-reset-clock"
          className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded flex items-center gap-1 border border-slate-700 disabled:opacity-50"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset
        </button>
      </div>
    </div>
  );
};
