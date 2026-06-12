import { useState, useEffect, useCallback } from 'react'
import { Zap, RefreshCw, Play, AlertTriangle, CheckCircle, XCircle, ArrowRight } from 'lucide-react'
import { generateTrade, generateBatch, getScenarios, getUsers } from '../services/api'
import OutcomeBadge from '../components/OutcomeBadge'
import type { TradeCheckResponse, User } from '../types'

type Result = TradeCheckResponse & { scenario: string }

const OUTCOME_ICON = {
  CLEAN_PASS:               <CheckCircle className="text-green-500" size={18} />,
  SOFT_BLOCK:               <AlertTriangle className="text-yellow-500" size={18} />,
  HARD_BLOCK:               <XCircle className="text-red-500" size={18} />,
  HARD_BLOCK_WITH_OVERRIDE: <AlertTriangle className="text-orange-500" size={18} />,
}

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

export default function Stub1Page() {
  const [results, setResults] = useState<Result[]>([])
  const [scenarios, setScenarios] = useState<{ key: string; label: string }[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [selectedScenario, setSelectedScenario] = useState('')
  const [selectedTrader, setSelectedTrader] = useState('')
  const [batchCount, setBatchCount] = useState(5)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<Result | null>(null)

  useEffect(() => {
    getScenarios().then(d => setScenarios(d.scenarios))
    getUsers().then(setUsers)
  }, [])

  const runSingle = useCallback(async () => {
    setLoading(true)
    try {
      const res = await generateTrade(
        selectedScenario || undefined,
        selectedTrader ? Number(selectedTrader) : undefined,
      )
      setResults(prev => [res, ...prev].slice(0, 100))
      setSelected(res)
    } finally {
      setLoading(false)
    }
  }, [selectedScenario, selectedTrader])

  const runBatch = useCallback(async () => {
    setLoading(true)
    try {
      const res = await generateBatch(batchCount)
      const valid = res.results.filter(r => !('error' in r)) as Result[]
      setResults(prev => [...valid, ...prev].slice(0, 100))
      if (valid.length > 0) setSelected(valid[0])
    } finally {
      setLoading(false)
    }
  }, [batchCount])

  const traders = users.filter(u => u.role === 'TRADER')

  const summary = results.reduce((acc, r) => {
    acc[r.decision.outcome] = (acc[r.decision.outcome] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Zap className="text-yellow-500" size={24} />
          Stub 1 — Trade Generator
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Randomly generates trades and fires them at the ArT rules engine. Covers all 4 outcome types across Equities and Fixed Income.
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Scenario</label>
            <select
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white min-w-[200px]"
              value={selectedScenario}
              onChange={e => setSelectedScenario(e.target.value)}
            >
              <option value="">Random (weighted)</option>
              {scenarios.map(s => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Trader</label>
            <select
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white min-w-[180px]"
              value={selectedTrader}
              onChange={e => setSelectedTrader(e.target.value)}
            >
              <option value="">Random trader</option>
              {traders.map(u => (
                <option key={u.id} value={u.id}>{u.full_name} ({u.seniority_level})</option>
              ))}
            </select>
          </div>
          <button
            onClick={runSingle}
            disabled={loading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            <Play size={15} />
            Run Single Trade
          </button>
          <div className="flex items-center gap-2">
            <input
              type="number" min={1} max={50}
              value={batchCount}
              onChange={e => setBatchCount(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-20"
            />
            <button
              onClick={runBatch}
              disabled={loading}
              className="flex items-center gap-2 bg-slate-700 hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
            >
              <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
              Run Batch
            </button>
          </div>
        </div>
      </div>

      {/* Outcome summary chips */}
      {results.length > 0 && (
        <div className="flex gap-3 flex-wrap">
          {(['CLEAN_PASS', 'SOFT_BLOCK', 'HARD_BLOCK_WITH_OVERRIDE', 'HARD_BLOCK'] as const).map(o => (
            <div key={o} className="bg-white border border-gray-200 rounded-lg px-4 py-2 flex items-center gap-2 shadow-sm">
              {OUTCOME_ICON[o]}
              <span className="text-sm font-medium text-gray-700">
                {o.replace(/_/g, ' ')}: <strong>{summary[o] || 0}</strong>
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Main layout: results table + detail panel */}
      <div className="flex gap-4">
        {/* Results table */}
        <div className="flex-1 min-w-0 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <span className="font-semibold text-sm text-gray-700">Generated Trades ({results.length})</span>
          </div>
          {results.length === 0 ? (
            <div className="text-center py-16 text-gray-400 text-sm">
              Click "Run Single Trade" or "Run Batch" to generate trades
            </div>
          ) : (
            <div className="overflow-auto max-h-[520px]">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide sticky top-0">
                  <tr>
                    <th className="text-left px-4 py-2">Ref</th>
                    <th className="text-left px-4 py-2">Ticker</th>
                    <th className="text-left px-4 py-2">Class</th>
                    <th className="text-left px-4 py-2">Direction</th>
                    <th className="text-right px-4 py-2">Notional</th>
                    <th className="text-left px-4 py-2">Outcome</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => (
                    <tr
                      key={r.trade.id}
                      onClick={() => setSelected(r)}
                      className={`border-t border-gray-50 cursor-pointer transition-colors ${
                        selected?.trade.id === r.trade.id ? 'bg-blue-50' : 'hover:bg-gray-50'
                      }`}
                    >
                      <td className="px-4 py-2 font-mono text-xs text-gray-500">{r.trade.trade_ref}</td>
                      <td className="px-4 py-2 font-medium">{r.trade.ticker}</td>
                      <td className="px-4 py-2 text-gray-600">{r.trade.asset_class.replace('_', ' ')}</td>
                      <td className="px-4 py-2 text-gray-600">{r.trade.direction.replace('_', ' ')}</td>
                      <td className="px-4 py-2 text-right font-medium">{fmt(r.trade.notional)}</td>
                      <td className="px-4 py-2"><OutcomeBadge outcome={r.decision.outcome} size="sm" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="w-80 shrink-0 bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-4 overflow-auto max-h-[620px]">
            <div>
              <div className="text-xs text-gray-400 font-mono">{selected.trade.trade_ref}</div>
              <div className="font-bold text-lg mt-1">{selected.trade.ticker}</div>
              <div className="mt-1"><OutcomeBadge outcome={selected.decision.outcome} size="md" /></div>
            </div>

            <div className="space-y-1 text-sm">
              <Row label="Asset Class" value={selected.trade.asset_class.replace('_', ' ')} />
              <Row label="Product" value={selected.trade.product_type.replace(/_/g, ' ')} />
              <Row label="Direction" value={selected.trade.direction.replace('_', ' ')} />
              <Row label="Notional" value={fmt(selected.trade.notional)} />
              <Row label="Account Equity" value={fmt(selected.trade.account_equity)} />
              <Row label="Account Type" value={selected.trade.account_type} />
              {selected.trade.credit_rating && <Row label="Credit Rating" value={selected.trade.credit_rating} />}
            </div>

            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">ArT Decision</div>
              <p className="text-sm text-gray-700 leading-relaxed">{selected.decision.reasoning}</p>
            </div>

            {selected.decision.rules_triggered.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Rules Triggered ({selected.decision.rules_triggered.length})
                </div>
                <div className="space-y-2">
                  {selected.decision.rules_triggered.map((r, i) => (
                    <div key={i} className="bg-red-50 border border-red-100 rounded-lg p-2 text-xs">
                      <div className="font-semibold text-red-800">{r.rule_name}</div>
                      <div className="text-red-600 mt-0.5">{r.rule_code}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selected.decision.processing_time_ms !== null && (
              <div className="text-xs text-gray-400">
                Processed in {selected.decision.processing_time_ms}ms
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span className="font-medium text-right">{value}</span>
    </div>
  )
}
