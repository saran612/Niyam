import React, { useEffect, useState } from "react";
import { User, ClockStatus } from "./types";
import { apiRequest } from "./api";
import { VirtualClockBar } from "./components/VirtualClockBar";
import { RegionalDashboard } from "./components/RegionalDashboard";
import { BureauDashboard } from "./components/BureauDashboard";
import { InstitutionDashboard } from "./components/InstitutionDashboard";
import { CaseDetailView } from "./components/CaseDetailView";
import { AuditExplorer } from "./components/AuditExplorer";
import { Shield, UserCircle, LogOut } from "lucide-react";

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [clock, setClock] = useState<ClockStatus | null>(null);
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);
  const [loginEmail, setLoginEmail] = useState("ro.sro@aicte-india.org");
  const [loginPassword, setLoginPassword] = useState("aicte@2026");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchClock = async () => {
    try {
      const c = await apiRequest<ClockStatus>("/admin/clock/status");
      setClock(c);
    } catch {
      // Ignored if offline
    }
  };

  const fetchCurrentUser = async () => {
    try {
      setLoading(true);
      const user = await apiRequest<User>("/auth/me");
      setCurrentUser(user);
    } catch {
      setCurrentUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClock();
    fetchCurrentUser();
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    try {
      const resp = await apiRequest<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      localStorage.setItem("aicte_token", resp.access_token);
      await fetchCurrentUser();
      await fetchClock();
    } catch (err: any) {
      setLoginError(err.message || "Invalid credentials");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("aicte_token");
    setCurrentUser(null);
    setSelectedAppId(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center font-mono text-sm text-slate-500">
        Initializing AICTE Compliance Engine...
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg max-w-md w-full p-8 border border-slate-300 shadow-xl">
          <div className="text-center mb-6">
            <div className="inline-flex p-3 rounded-full bg-blue-50 text-blue-700 mb-2">
              <Shield className="w-8 h-8" />
            </div>
            <h1 className="text-lg font-bold text-slate-900 tracking-tight">AICTE Approval & Obligation Engine</h1>
            <p className="text-xs text-slate-500 mt-1">SIH PS 26262 Deterministic Prototype Platform</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 font-mono focus:ring-1 focus:ring-blue-600 focus:outline-none"
                id="login-email-input"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 font-mono focus:ring-1 focus:ring-blue-600 focus:outline-none"
                id="login-password-input"
                required
              />
            </div>

            {loginError && (
              <div className="p-2.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded" id="login-error-msg">
                {loginError}
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-blue-700 hover:bg-blue-800 text-white py-2 rounded text-xs font-semibold cursor-pointer transition-colors"
              id="btn-login-submit"
            >
              Sign In to Platform
            </button>

            <div className="mt-4 pt-4 border-t border-slate-100 text-xs text-slate-500">
              <div className="font-semibold text-slate-700 mb-1">Quick Demo Accounts (password: aicte@2026):</div>
              <ul className="space-y-1 font-mono text-2xs text-slate-600">
                <li>• Regional Officer: <code className="bg-slate-100 px-1 py-0.5 rounded cursor-pointer" onClick={() => setLoginEmail("ro.sro@aicte-india.org")}>ro.sro@aicte-india.org</code></li>
                <li>• Bureau Officer: <code className="bg-slate-100 px-1 py-0.5 rounded cursor-pointer" onClick={() => setLoginEmail("bureau.officer@aicte-india.org")}>bureau.officer@aicte-india.org</code></li>
                <li>• Institution: <code className="bg-slate-100 px-1 py-0.5 rounded cursor-pointer" onClick={() => setLoginEmail("dean.inst001@aicte-india.org")}>dean.inst001@aicte-india.org</code></li>
                <li>• System Admin: <code className="bg-slate-100 px-1 py-0.5 rounded cursor-pointer" onClick={() => setLoginEmail("admin@aicte-india.org")}>admin@aicte-india.org</code></li>
              </ul>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Simulated Clock Header */}
      <VirtualClockBar clock={clock} onClockChanged={fetchClock} />

      {/* Main App Navigation Bar */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded bg-blue-700 text-white font-bold text-xs">AICTE</div>
            <span className="font-bold text-sm text-slate-900 tracking-tight">Compliance & Obligation Engine</span>
          </div>

          <nav className="flex items-center gap-1 font-medium text-xs">
            <button
              onClick={() => {
                setActiveTab("dashboard");
                setSelectedAppId(null);
              }}
              className={`px-3 py-1.5 rounded cursor-pointer ${
                activeTab === "dashboard" ? "bg-slate-100 text-slate-900 font-semibold" : "text-slate-600 hover:bg-slate-50"
              }`}
              id="tab-dashboard"
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`px-3 py-1.5 rounded cursor-pointer ${
                activeTab === "audit" ? "bg-slate-100 text-slate-900 font-semibold" : "text-slate-600 hover:bg-slate-50"
              }`}
              id="tab-audit"
            >
              Audit Trail
            </button>
          </nav>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2 text-slate-700">
            <UserCircle className="w-4 h-4 text-slate-400" />
            <span>{currentUser.email}</span>
            <span className="px-2 py-0.5 bg-slate-100 text-slate-800 rounded font-semibold border border-slate-200 uppercase text-2xs">
              {currentUser.role}
            </span>
          </div>

          <button
            onClick={handleLogout}
            className="p-1.5 hover:bg-slate-100 rounded text-slate-500 hover:text-slate-800"
            title="Sign out"
            id="btn-logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Content Body */}
      <main className="flex-1">
        {selectedAppId !== null ? (
          <CaseDetailView appId={selectedAppId} onBack={() => setSelectedAppId(null)} />
        ) : activeTab === "audit" ? (
          <AuditExplorer />
        ) : currentUser.role === "regional_officer" ? (
          <RegionalDashboard onSelectApplication={(id) => setSelectedAppId(id)} />
        ) : currentUser.role === "bureau_officer" || currentUser.role === "admin" ? (
          <BureauDashboard />
        ) : (
          <InstitutionDashboard />
        )}
      </main>
    </div>
  );
}

export default App;
