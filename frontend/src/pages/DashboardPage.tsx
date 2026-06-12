import { useState, useEffect, useCallback } from 'react'
import { BarChart2, Send, Loader, Sparkles } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts'
import { getSummary, getDailyTrend, getTopRules, getTopTraders, getOverrideStats, nlQuery } from '../services/api'
import type { DailyTrend, DashboardSummary, OverrideStats, TopRule, TopTrader } from '../types'

const OUTCOME_COLOURS = {
  CLEAN_PASS:               '#22c55e',
  SOFT_BLOCK:               '#eab308',
  HARD_BLOCK:               '#ef4444',
  HARD_BLOCK_WITH_OVERRIDE: '#f97316',
}

const OUTCOME_LABELS = {
  CLEAN_PASS:               'Clean Pass',
  SOFT_BLOCK:               'Soft Block',
  HARD_BLOCK:               'Hard Block',
  HARD_BLOCK_WITH_OVERRIDE: 'Override Required',
}

function StatCard({ label, value, sub, colour }: { label: string; value: string | number; sub?: string; colour?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="text-xs text-gray-500 font-medium">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${colour || 'text-gray-900'}`}>{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  )
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [trend, setTrend] = useState<DailyTrend[]>([])
  const [topRules, setTopRules] = useState<TopRule[]>([])
  const [topTraders, setTopTraders] = useState<TopTrader[]>([])
  const [overrideStats, setOverrideStats] = useState<OverrideStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  const [nlQueryText, setNlQueryText] = useState('')
  const [nlResult, setNlResult] = useState<any>(null)
  const [nlLoading, setNlLoading] = useState(false)

  const SUGGESTED = [
    'Show me all hard blocks in the past 7 days',
    'Which traders had the most blocks last month?',
    'Show overrides for fixed income trades',
    'What were the most triggered rules this month?',
  ]

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [s, t, tr, tt, os] = await Promise.all([
        getSummary(days),
        getDailyTrend(14),
        getTopRules(days),
        getTopTraders(days),
        getOverrideStats(days),
      ])
      setSummary(s)
      setTrend(t)
      setTopRules(tr)
      setTopTraders(tt)
      setOverrideStats(os)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => { load() }, [load])

  const handleNLQuery = async (q?: string) => {
    const query = q ?? nlQueryText
    if (!query.trim()) return
    setNlLoading(true)
    setNlResult(null)
    if (q) setNlQueryText(q)
    try {
      const res = await nlQuery(query)
      setNlResult(res)
    } finally {
      setNlLoading(false)
    }
  }

  // Build pie data
  const pieData = summary
    ? Object.entries(summary.outcomes).map(([k, v]) => ({
        name: OUTCOME_LABELS[k as keyof typeof OUTCOME_LABELS] ?? k,
        value: v,
        colour: OUTCOME_COLOURS[k as keyof typeof OUTCOME_COLOURS],
      })).filter(d => d.value > 0)
    : []

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <BarChart2 className="text-purple-600" size={24} />
            MI Dashboard
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Management information — outcomes, rule triggers, override stats, and natural language querying.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white"
            value={days}
            onChange={e => setDays(Number(e.target.value))}
          >
            <option value={7}>Past 7 days</option>
            <option value={14}>Past 14 days</option>
            <option value={30}>Past 30 days</option>
            <option value={90}>Past 90 days</option>
          </select>
          <button onClick={load} disabled={loading}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50">
            Refresh
          </button>
        </div>
      </div>

      {/* KPI row */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <StatCard label="Total Trades" value={summary.total_trades.toLocaleString()} />
          <StatCard label="Clean Pass" value={summary.outcomes.CLEAN_PASS} colour="text-green-600"
            sub={`${summary.total_trades > 0 ? Math.round(summary.outcomes.CLEAN_PASS / summary.total_trades * 100) : 0}%`} />
          <StatCard label="Soft Block" value={summary.outcomes.SOFT_BLOCK} colour="text-yellow-600" />
          <StatCard label="Hard Block" value={summary.outcomes.HARD_BLOCK} colour="text-red-600" />
          <StatCard label="Override Required" value={summary.outcomes.HARD_BLOCK_WITH_OVERRIDE} colour="text-orange-600" />
          <StatCard label="Pending Approvals" value={summary.pending_overrides} colour={summary.pending_overrides > 0 ? 'text-orange-600' : 'text-gray-900'} />
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Trend chart */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="font-semibold text-sm text-gray-700 mb-3">Daily Decision Trend (14 days)</div>
          {trend.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No data yet — generate some trades</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={trend} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="CLEAN_PASS" name="Clean Pass" stackId="a" fill={OUTCOME_COLOURS.CLEAN_PASS} />
                <Bar dataKey="SOFT_BLOCK" name="Soft Block" stackId="a" fill={OUTCOME_COLOURS.SOFT_BLOCK} />
                <Bar dataKey="HARD_BLOCK_WITH_OVERRIDE" name="Override" stackId="a" fill={OUTCOME_COLOURS.HARD_BLOCK_WITH_OVERRIDE} />
                <Bar dataKey="HARD_BLOCK" name="Hard Block" stackId="a" fill={OUTCOME_COLOURS.HARD_BLOCK} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Pie chart */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="font-semibold text-sm text-gray-700 mb-3">Outcome Distribution</div>
          {pieData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No data yet</div>
          ) : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width={160} height={160}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" cx="50%" cy="50%" innerRadius={45} outerRadius={70}>
                    {pieData.map((d, i) => <Cell key={i} fill={d.colour} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2">
                {pieData.map((d, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <div className="w-3 h-3 rounded-full shrink-0" style={{ background: d.colour }} />
                    <span className="text-gray-600">{d.name}</span>
                    <span className="font-bold text-gray-800 ml-auto">{d.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Top rules + traders */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="font-semibold text-sm text-gray-700 mb-3">Top Rules Triggered</div>
          {topRules.length === 0 ? (
            <div className="text-gray-400 text-sm py-8 text-center">No blocked trades yet</div>
          ) : (
            <div className="space-y-2">
              {topRules.slice(0, 8).map((r, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="text-xs font-bold text-gray-400 w-4">{i + 1}</div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-800 truncate">{r.rule_name}</div>
                    <div className="text-xs text-gray-400">{r.rule_code} · {r.rule_type}</div>
                  </div>
                  <div className="text-sm font-bold text-gray-700 shrink-0">{r.count}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="font-semibold text-sm text-gray-700 mb-3">Traders — Most Block Decisions</div>
          {topTraders.length === 0 ? (
            <div className="text-gray-400 text-sm py-8 text-center">No blocked trades yet</div>
          ) : (
            <div className="space-y-2">
              {topTraders.slice(0, 8).map((t, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="text-xs font-bold text-gray-400 w-4">{i + 1}</div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-800">{t.trader_name}</div>
                    <div className="text-xs text-gray-400">{t.seniority} · {t.desk}</div>
                  </div>
                  <div className="text-sm font-bold text-red-600 shrink-0">{t.block_count} blocks</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Override stats */}
      {overrideStats && overrideStats.total > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="font-semibold text-sm text-gray-700 mb-3">Override Statistics</div>
          <div className="flex gap-6 text-sm">
            <Stat label="Total Requests" value={overrideStats.total} />
            <Stat label="Approved" value={overrideStats.approved} colour="text-green-600" />
            <Stat label="Rejected" value={overrideStats.rejected} colour="text-red-600" />
            <Stat label="Pending" value={overrideStats.pending} colour="text-orange-600" />
            <Stat label="Escalated" value={overrideStats.escalated} colour="text-purple-600" />
            <Stat label="Approval Rate" value={`${overrideStats.approval_rate}%`} />
            <Stat label="Avg AI Risk Score" value={`${overrideStats.avg_ai_risk_score}/100`} />
          </div>
        </div>
      )}

      {/* NL Query */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="text-purple-500" size={18} />
          <span className="font-semibold text-gray-800">Natural Language Query</span>
          <span className="text-xs text-gray-400 bg-gray-100 rounded px-2 py-0.5">ArT AI</span>
        </div>

        {/* Suggested queries */}
        <div className="flex flex-wrap gap-2">
          {SUGGESTED.map((s, i) => (
            <button key={i}
              onClick={() => handleNLQuery(s)}
              className="text-xs border border-purple-200 text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-full px-3 py-1 transition-colors">
              {s}
            </button>
          ))}
        </div>

        <div className="flex gap-3">
          <input
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-300"
            placeholder="Ask anything about trades, blocks, overrides..."
            value={nlQueryText}
            onChange={e => setNlQueryText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleNLQuery()}
          />
          <button
            onClick={() => handleNLQuery()}
            disabled={nlLoading || !nlQueryText.trim()}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {nlLoading ? <Loader size={15} className="animate-spin" /> : <Send size={15} />}
            Query
          </button>
        </div>

        {nlResult && (
          <div className="space-y-3">
            <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
              <div className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-1">AI Summary</div>
              <p className="text-sm text-gray-800 leading-relaxed">{nlResult.summary}</p>
            </div>

            <div className="text-xs text-gray-400">
              Query: <span className="italic">"{nlResult.query}"</span> ·
              Filters: days_back={nlResult.parsed_filters.days_back}
              {nlResult.parsed_filters.outcome && ` · outcome=${nlResult.parsed_filters.outcome}`}
              {nlResult.parsed_filters.asset_class && ` · asset_class=${nlResult.parsed_filters.asset_class}`}
              · {nlResult.total_results} results
            </div>

            {nlResult.decisions?.length > 0 && (
              <div className="overflow-auto max-h-48 border border-gray-200 rounded-lg">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50 text-gray-500">
                    <tr>
                      <th className="text-left px-3 py-2">Decision Ref</th>
                      <th className="text-left px-3 py-2">Outcome</th>
                      <th className="text-left px-3 py-2">Rules</th>
                      <th className="text-left px-3 py-2">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {nlResult.decisions.map((d: any) => (
                      <tr key={d.decision_ref} className="border-t border-gray-50">
                        <td className="px-3 py-1.5 font-mono">{d.decision_ref}</td>
                        <td className="px-3 py-1.5">{d.outcome.replace(/_/g, ' ')}</td>
                        <td className="px-3 py-1.5">{d.rules_count}</td>
                        <td className="px-3 py-1.5 text-gray-400">{new Date(d.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value, colour = 'text-gray-800' }: { label: string; value: string | number; colour?: string }) {
  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`text-lg font-bold ${colour}`}>{value}</div>
    </div>
  )
}
