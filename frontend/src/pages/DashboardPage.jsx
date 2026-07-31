import React, { useEffect, useState } from 'react';
import {
  ShieldCheck, ShieldX, Activity, RefreshCw, Search, Layers, Clock, Terminal, Server, Database, Radio, Cpu, BarChart2, ShieldAlert
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { getMetrics, getAuditLogs, getRules, reloadRules, resetWafLogs } from '../services/api';
import wsManager from '../services/websocket';

const COLOR_ALLOWED = '#10b981';
const COLOR_BLOCKED = '#ef4444';

export const DashboardPage = () => {
  const [metrics, setMetrics] = useState({
    total_requests: 0,
    allowed_requests: 0,
    blocked_requests: 0,
    requests_per_minute: 0,
    rule_violations: {},
    most_triggered_rule: 'None',
  });

  const [auditLogs, setAuditLogs] = useState([]);
  const [rules, setRules] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [reloading, setReloading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [shadowMode, setShadowMode] = useState(false);
  const [showArchModal, setShowArchModal] = useState(false);

  const handleResetLogs = async () => {
    if (!window.confirm("Are you sure you want to clear all WAF logs and reset metrics?")) {
      return;
    }
    setResetting(true);
    try {
      await resetWafLogs();
      setAuditLogs([]);
      setMetrics({
        total_requests: 0,
        allowed_requests: 0,
        blocked_requests: 0,
        requests_per_minute: 0,
        rule_violations: {},
        most_triggered_rule: 'None',
      });
    } catch (err) {
      console.error('Failed to reset WAF logs:', err);
    } finally {
      setResetting(false);
    }
  };

  const fetchData = async () => {
    try {
      const [mRes, aRes, rRes] = await Promise.all([getMetrics(), getAuditLogs(50), getRules()]);
      setMetrics(mRes);
      setAuditLogs(aRes);
      setRules(rRes.rules || []);
      if (rRes.shadow_mode !== undefined) {
        setShadowMode(rRes.shadow_mode);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    }
  };

  useEffect(() => {
    fetchData();

    const unsubscribe = wsManager.subscribe((event) => {
      if (event.payload) {
        setAuditLogs((prev) => [event.payload, ...prev.slice(0, 49)]);
        if (event.payload.would_block) {
          setShadowMode(true);
        }
        fetchData();
      }
    });

    return () => unsubscribe();
  }, []);

  const handleReloadRules = async () => {
    setReloading(true);
    try {
      await reloadRules();
      await fetchData();
    } catch (err) {
      console.error('Failed to reload rules:', err);
    } finally {
      setReloading(false);
    }
  };

  const toolTraffic = auditLogs.reduce((acc, log) => {
    acc[log.tool] = (acc[log.tool] || 0) + 1;
    return acc;
  }, {});

  const ruleHits = {
    RateLimitRule: metrics.rule_violations?.RateLimitRule || 0,
    ParameterValidationRule: metrics.rule_violations?.ParameterValidationRule || 0,
    DataScopeRule: metrics.rule_violations?.DataScopeRule || 0,
    SequenceRule: metrics.rule_violations?.SequenceRule || 0,
  };

  const filteredLogs = auditLogs.filter(
    (log) =>
      (log.tool && log.tool.toLowerCase().includes(searchTerm.toLowerCase())) ||
      log.request_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.rule_triggered && log.rule_triggered.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (log.reason && log.reason.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (log.user_prompt && log.user_prompt.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const aiDecisions = { ALLOW: 0, BLOCK: 0, REVIEW: 0 };
  const aiRisks = { LOW: 0, MEDIUM: 0, HIGH: 0 };
  let sqliCount = 0;
  let promptInjCount = 0;

  auditLogs.forEach((log) => {
    const decision = log.final_decision || "ALLOW";
    if (decision in aiDecisions) {
      aiDecisions[decision]++;
    }
    const risk = log.ai_risk_score || "LOW";
    if (risk in aiRisks) {
      aiRisks[risk]++;
    }
    const reason = (log.reason || "").toLowerCase();
    const parameters = JSON.stringify(log.parameters).toLowerCase();
    if (reason.includes("sql") || parameters.includes("drop table") || parameters.includes("union select") || parameters.includes("delete from")) {
      sqliCount++;
    }
    if (reason.includes("prompt injection") || parameters.includes("ignore previous instructions") || parameters.includes("reveal system prompt")) {
      promptInjCount++;
    }
  });

  const latestRequest = auditLogs[0];

  const pieData = [
    { name: 'Allowed', value: metrics.allowed_requests || 0, color: COLOR_ALLOWED },
    { name: 'Blocked', value: metrics.blocked_requests || 0, color: COLOR_BLOCKED },
  ];

  const ruleChartData = Object.entries(ruleHits).map(([key, val]) => ({
    name: key.replace('Rule', ''),
    hits: val,
  }));

  return (
    <div className="app-container py-6 space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-100 tracking-tight flex items-center gap-3">
            Agent WAF Control Center
            <span className="clean-badge px-3 py-1 text-slate-100 text-xs font-mono">
              Live Protection
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time proxy telemetry, security policy evaluation, and event stream logs.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowArchModal(true)}
            className="clean-btn px-4 py-2 text-slate-200 text-xs font-semibold"
          >
            🏛️ View Architecture Diagram
          </button>
          <button
            onClick={handleReloadRules}
            disabled={reloading}
            className="clean-btn px-4 py-2 text-slate-100 text-xs font-semibold flex items-center space-x-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reloading ? 'animate-spin' : ''}`} />
            <span>Reload Rules</span>
          </button>
          <button
            onClick={handleResetLogs}
            disabled={resetting}
            className="clean-btn px-4 py-2 text-slate-100 text-xs font-semibold flex items-center space-x-2 border-red-900/50 hover:bg-red-950/20"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>{resetting ? 'Resetting...' : 'Reset Logs'}</span>
          </button>
        </div>
      </div>

      {/* System Health Status Bar */}
      <div className="clean-card p-4 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <span className="text-slate-400 uppercase font-semibold">System Readiness:</span>
          <div className="flex items-center space-x-2">
            <Server className="w-4 h-4 text-slate-300" />
            <span className="text-slate-300">Backend:</span>
            <span className="text-slate-100 font-bold">🟢 Operational</span>
          </div>
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-slate-300" />
            <span className="text-slate-300">SQLite DB:</span>
            <span className="text-slate-100 font-bold">🟢 Connected</span>
          </div>
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-slate-300 animate-pulse" />
            <span className="text-slate-300">WebSocket:</span>
            <span className="text-slate-100 font-bold">🟢 Streaming</span>
          </div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-slate-300" />
            <span className="text-slate-300">Policy Engine:</span>
            <span className="text-slate-100 font-bold">🟢 Active</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-slate-400 uppercase font-semibold">Shadow Mode:</span>
            <span
              className={`clean-badge px-3 py-1 font-bold text-[10px] text-slate-300`}
            >
              {shadowMode ? 'ON (Log Only)' : 'OFF (Enforce Block)'}
            </span>
          </div>
        </div>
      </div>

      {/* KPI Metrics Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="clean-card p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Requests</span>
            <div className="text-3xl font-black text-slate-100 mt-1">{metrics.total_requests}</div>
          </div>
          <div className="clean-badge p-3 text-slate-300">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        <div className="clean-card p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Allowed Calls</span>
            <div className="text-3xl font-black text-slate-200 mt-1">{metrics.allowed_requests}</div>
          </div>
          <div className="clean-badge p-3 text-slate-300">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>

        <div className="clean-card p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Blocked Events</span>
            <div className="text-3xl font-black text-slate-300 mt-1">{metrics.blocked_requests}</div>
          </div>
          <div className="clean-badge p-3 text-slate-300">
            <ShieldX className="w-5 h-5" />
          </div>
        </div>

        <div className="clean-card p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Velocity (RPM)</span>
            <div className="text-3xl font-black text-slate-100 mt-1">{metrics.requests_per_minute}</div>
          </div>
          <div className="clean-badge p-3 text-slate-300">
            <Clock className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* AI WAF Security Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="clean-card p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">AI Allowed Decisions</span>
            <div className="text-3xl font-black text-slate-100 mt-1">{aiDecisions.ALLOW}</div>
          </div>
          <div className="clean-badge p-3 text-slate-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>

        <div className="clean-card p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">AI Block/Review Decisions</span>
            <div className="text-3xl font-black text-slate-100 mt-1">{aiDecisions.BLOCK + aiDecisions.REVIEW}</div>
          </div>
          <div className="clean-badge p-3 text-slate-400">
            <ShieldX className="w-5 h-5" />
          </div>
        </div>

        <div className="clean-card p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">AI High Risk Alerts</span>
            <div className="text-3xl font-black text-slate-100 mt-1">{aiRisks.HIGH}</div>
          </div>
          <div className="clean-badge p-3 text-slate-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>

        <div className="clean-card p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Injection Detections</span>
            <div className="text-3xl font-black text-slate-100 mt-1">{sqliCount + promptInjCount}</div>
          </div>
          <div className="clean-badge p-3 text-slate-400">
            <Terminal className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Live Request Pipeline & Checklist */}
      {latestRequest && (
        <div className="clean-card p-6 space-y-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            Live Request Flow Interception & Rule Evaluation Panel
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-center font-mono text-xs">
            <div className="clean-card bg-opacity-25 bg-slate-950/20 p-3 text-center border-slate-700/20">
              <span className="text-slate-400 block text-[10px]">1. PLANNER</span>
              <span className="font-bold text-slate-200">{latestRequest.agent_id}</span>
            </div>
            <div className="text-center text-slate-500 hidden md:block">➔</div>
            <div className="clean-card bg-opacity-25 bg-slate-950/20 p-3 text-center border-slate-700/20">
              <span className="text-cyan-400 block text-[10px]">2. WAF PROXY</span>
              <span className="font-bold text-cyan-300">Tool: {latestRequest.tool}</span>
            </div>
            <div className="text-center text-slate-500 hidden md:block">➔</div>
            <div className="clean-card bg-opacity-25 bg-slate-950/20 p-3 text-center border-slate-700/20">
              <span className="block text-[10px] uppercase font-semibold text-slate-400">
                3. DISPOSITION
              </span>
              <span className={`font-bold ${latestRequest.blocked ? 'text-rose-400' : 'text-emerald-400'}`}>
                {latestRequest.blocked ? 'BLOCKED' : 'ALLOWED'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tool Traffic, Rule Hits, Rule Config Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="clean-card p-6 space-y-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-cyan-400" />
            Tool Traffic Breakdown
          </h3>
          <div className="space-y-3 font-mono text-xs">
            {Object.entries(toolTraffic).map(([toolName, count], idx) => (
              <div key={idx} className="clean-card bg-opacity-25 bg-slate-950/20 p-3 flex items-center justify-between border-slate-700/20">
                <span className="text-cyan-400 font-bold">{toolName}</span>
                <span className="clean-badge px-2.5 py-0.5 text-cyan-300 font-bold text-[11px]">
                  {count} calls
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="clean-card p-6 space-y-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-purple-400" />
            Rule Hit Count Breakdown
          </h3>
          <div className="space-y-3 font-mono text-xs">
            {Object.entries(ruleHits).map(([ruleName, count], idx) => (
              <div key={idx} className="clean-card bg-opacity-25 bg-slate-950/20 p-3 flex items-center justify-between border-slate-700/20">
                <span className="text-purple-300 font-semibold">{ruleName.replace('Rule', '')}</span>
                <span className="clean-badge px-2.5 py-0.5 text-purple-300 font-bold text-[11px]">
                  {count} blocks
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="clean-card p-6 space-y-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            Registered Security Rules
          </h3>
          <div className="space-y-2.5 text-xs font-mono">
            <div className="clean-card bg-opacity-25 bg-slate-950/20 p-2.5 flex justify-between border-slate-700/20">
              <span className="text-slate-300">RateLimitRule</span>
              <span className="text-emerald-400">Max 5/min (Enabled)</span>
            </div>
            <div className="clean-card bg-opacity-25 bg-slate-950/20 p-2.5 flex justify-between border-slate-700/20">
              <span className="text-slate-300">ParameterValidationRule</span>
              <span className="text-emerald-400">Max 1000 char (Enabled)</span>
            </div>
            <div className="clean-card bg-opacity-25 bg-slate-950/20 p-2.5 flex justify-between border-slate-700/20">
              <span className="text-slate-300">DataScopeRule</span>
              <span className="text-emerald-400">sample_data/ (Enabled)</span>
            </div>
            <div className="clean-card bg-opacity-25 bg-slate-950/20 p-2.5 flex justify-between border-slate-700/20">
              <span className="text-slate-300">SequenceRule</span>
              <span className="text-emerald-400">search ➔ file (Enabled)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="clean-card p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            Real-Time Audit Log Feed
          </h3>

          <div className="clean-input-box flex items-center px-3 py-1.5 w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 mr-2 flex-shrink-0" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search tools, rules, IDs..."
              className="bg-transparent text-xs text-slate-100 placeholder-slate-500 focus:outline-none w-full"
            />
          </div>
        </div>

        <div className="clean-card bg-opacity-25 bg-slate-950/20 p-2 overflow-x-auto border-slate-700/20 audit-table-wrap">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-700/40 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">User Prompt</th>
                <th className="py-3 px-4">Tool Call (Params)</th>
                <th className="py-3 px-4">AI Risk / Decision</th>
                <th className="py-3 px-4">WAF Trigger</th>
                <th className="py-3 px-4">Reason</th>
                <th className="py-3 px-4 text-right">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 font-mono">
              {filteredLogs.length > 0 ? (
                filteredLogs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/20 transition">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 text-slate-200 font-medium max-w-xs truncate" title={log.user_prompt || '—'}>
                      {log.user_prompt || '—'}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-100">{log.tool}</div>
                      <div className="text-[10px] text-slate-500 max-w-xs truncate" title={JSON.stringify(log.parameters)}>
                        {JSON.stringify(log.parameters)}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 font-sans flex-wrap">
                        <span className={`clean-badge px-2 py-0.5 text-[9px] font-bold ${
                          log.ai_risk_score === 'HIGH' ? 'text-rose-400 border-rose-800/40 bg-rose-950/40' : 'text-slate-400'
                        }`}>
                          {log.ai_risk_score || 'LOW'}
                        </span>
                        {log.blocked ? (
                          <span className="clean-badge px-2 py-0.5 text-rose-400 border border-rose-800/40 bg-rose-950/40 text-[9px] font-bold">
                            BLOCKED
                          </span>
                        ) : log.would_block ? (
                          <span className="clean-badge px-2 py-0.5 text-amber-400 border border-amber-800/40 bg-amber-950/40 text-[9px] font-bold">
                            SHADOW
                          </span>
                        ) : (
                          <span className="clean-badge px-2 py-0.5 text-emerald-400 border border-emerald-800/40 bg-emerald-950/40 text-[9px] font-bold">
                            ALLOWED
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-semibold">{log.rule_triggered || '—'}</td>
                    <td className="py-3 px-4 text-slate-400 max-w-xs truncate" title={log.reason}>
                      {log.reason || 'Allowed'}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">{log.execution_time_ms.toFixed(2)}ms</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-sans text-xs">
                    No matching audit log records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Architecture Modal */}
      {showArchModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="clean-card max-w-3xl w-full p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-700/60 pb-4">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                🏛️ Agent WAF System Architecture Pipeline
              </h3>
              <button
                onClick={() => setShowArchModal(false)}
                className="clean-btn px-3 py-1 text-slate-400 hover:text-white text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <div className="clean-card bg-opacity-25 bg-slate-950/20 p-5 font-mono text-xs text-slate-300 space-y-3 border-slate-700/20">
              <div className="text-center font-bold text-cyan-400">User / Sample AI Agent Chat (/chat)</div>
              <div className="text-center text-slate-500">│</div>
              <div className="text-center text-slate-200">POST /agent/chat ➔ Agent Orchestrator</div>
              <div className="text-center text-slate-500">│</div>
              <div className="text-center text-indigo-400">Agent Planner (decides tool + parameters)</div>
              <div className="text-center text-slate-500">│</div>
              <div className="clean-badge p-3 text-center text-cyan-300 font-bold w-full rounded-xl">
                ══ Agent WAF Proxy Interceptor ══
              </div>
              <div className="text-center text-slate-500">│</div>
              <div className="clean-card bg-opacity-25 bg-slate-950/20 p-3 text-center space-y-1 border-slate-700/20">
                <span className="text-purple-400 font-bold block">Policy Engine Sequential Evaluation:</span>
                <span className="text-slate-400 block text-[11px]">RateLimitRule ➔ ParameterValidationRule ➔ DataScopeRule ➔ SequenceRule</span>
              </div>
              <div className="text-center text-slate-500">│</div>
              <div className="flex justify-around text-[11px]">
                <span className="text-emerald-400">ALLOWED ➔ ToolExecutor ➔ Tool</span>
                <span className="text-rose-400">BLOCKED ➔ WAF Error Response</span>
              </div>
              <div className="text-center text-slate-500">│</div>
              <div className="text-center text-amber-400">SQLite Audit Repo ➔ Metrics Collector ➔ WebSocket Broadcast ➔ Dashboard (/dashboard)</div>
            </div>

            <div className="text-right">
              <button
                onClick={() => setShowArchModal(false)}
                className="clean-btn px-4 py-2 text-slate-200 text-xs font-semibold"
              >
                Close Architecture View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
