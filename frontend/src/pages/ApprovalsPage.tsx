import { useState, useEffect, useCallback } from 'react'
import { CheckSquare, RefreshCw, CheckCircle, XCircle, ArrowUpCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { listOverrides, actionOverride, escalateOverride, getUsers, listDecisions } from '../services/api'
import OutcomeBadge from '../components/OutcomeBadge'
import type { ArtDecision, OverrideRequest, User } from '../types'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

const RISK_COLOURS = {
  LOW:      'bg-green-100 text-green-800 border-green-300',
  MEDIUM:   'bg-yellow-100 text-yellow-800 border-yellow-300',
  HIGH:     'bg-orange-100 text-orange-800 border-orange-300',
  CRITICAL: 'bg-red-100 text-red-800 border-red-300',
}

export default function ApprovalsPage() {
  const [overrides, setOverrides] = useState<OverrideRequest[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [decisions, setDecisions] = useState<Record<number, ArtDecision>>({})
  const [filter, setFilter] = useState('PENDING')
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<OverrideRequest | null>(null)
  const [approverId, setApproverId] = useState('')
  const [approverNotes, setApproverNotes] = useState('')
  const [acting, setActing] = useState(false)
  const [expandedRationale, setExpandedRationale] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [ovrs, usrs] = await Promise.all([
        listOverrides(filter || undefined),
        getUsers(),
      ])
      setOverrides(ovrs)
      setUsers(usrs)
      // Load decisions for context
      const decMap: Record<number, ArtDecision> = {}
      const decs = await listDecisions({ limit: 200 })
      decs.forEach(d => { decMap[d.id] = d })
      setDecisions(decMap)
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => { load() }, [load])

  const supervisors = users.filter(u => ['SUPERVISOR', 'HEAD_OF_DESK', 'MANAGING_DIRECTOR'].includes(u.role))
  const traders = users.reduce((acc, u) => { acc[u.id] = u; return acc }, {} as Record<number, User>)

  const handleAction = async (status: 'APPROVED' | 'REJECTED') => {
    if (!selected || !approverId) return
    setActing(true)
    try {
      await actionOverride(selected.id, {
        approver_id: Number(approverId),
        status,
        approver_notes: approverNotes || undefined,
      })
      setSelected(null)
      setApproverNotes('')
      await load()
    } finally {
      setActing(false)
    }
  }

  const handleEscalate = async () => {
    if (!selected || !approverId) return
    setActing(true)
    try {
      await escalateOverride(selected.id, Number(approverId))
      setSelected(null)
      await load()
    } finally {
      setActing(false)
    }
  }

  const pending = overrides.filter(o => o.status === 'PENDING').length

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <CheckSquare className="text-orange-500" size={24} />
            Stub 2 — Supervisory Approvals
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Override requests for Hard Block with Override decisions. Approve, reject, or escalate with AI risk scoring.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {pending > 0 && (
            <span className="bg-orange-100 text-orange-800 border border-orange-300 rounded-full px-3 py-1 text-sm font-semibold">
              {pending} pending
            </span>
          )}
          <button onClick={load} disabled={loading}
            className="flex items-center gap-2 border border-gray-300 rounded-lg px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit">
        {['PENDING', 'APPROVED', 'REJECTED', 'ESCALATED', ''].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              filter === s ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
            }`}>
            {s || 'All'}
          </button>
        ))}
      </div>

      <div className="flex gap-4">
        {/* Override list */}
        <div className="flex-1 min-w-0 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {overrides.length === 0 ? (
            <div className="text-center py-16 text-gray-400 text-sm">
              {filter === 'PENDING' ? 'No pending override requests' : 'No override requests for this filter'}
            </div>
          ) : (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                  <tr>
                    <th className="text-left px-4 py-3">Ref</th>
                    <th className="text-left px-4 py-3">Trader</th>
                    <th className="text-left px-4 py-3">Requested</th>
                    <th className="text-left px-4 py-3">AI Risk</th>
                    <th className="text-left px-4 py-3">Status</th>
                    <th className="text-left px-4 py-3">Approver</th>
                  </tr>
                </thead>
                <tbody>
                  {overrides.map(o => {
                    const trader = traders[o.requested_by_id]
                    const approver = o.approver_id ? traders[o.approver_id] : null
                    return (
                      <tr key={o.id}
                        onClick={() => { setSelected(o); setExpandedRationale(false) }}
                        className={`border-t border-gray-50 cursor-pointer transition-colors ${
                          selected?.id === o.id ? 'bg-orange-50' : 'hover:bg-gray-50'
                        }`}>
                        <td className="px-4 py-3 font-mono text-xs text-gray-500">{o.override_ref}</td>
                        <td className="px-4 py-3">
                          <div className="font-medium">{trader?.full_name ?? `User #${o.requested_by_id}`}</div>
                          <div className="text-xs text-gray-400">{trader?.seniority_level} · {trader?.desk}</div>
                        </td>
                        <td className="px-4 py-3 text-gray-500 text-xs">
                          {new Date(o.requested_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className={`text-xs font-bold px-2 py-0.5 rounded border ${RISK_COLOURS[o.ai_risk_band]}`}>
                              {o.ai_risk_band}
                            </span>
                            <span className="text-xs text-gray-500">{o.ai_risk_score}/100</span>
                          </div>
                        </td>
                        <td className="px-4 py-3"><OutcomeBadge outcome={o.status} size="sm" /></td>
                        <td className="px-4 py-3 text-gray-500 text-xs">
                          {approver ? approver.full_name : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Action panel */}
        {selected && (
          <div className="w-96 shrink-0 space-y-4">
            {/* Risk scorecard */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-800">AI Risk Assessment</span>
                <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border font-bold text-sm ${RISK_COLOURS[selected.ai_risk_band]}`}>
                  {selected.ai_risk_score}/100 · {selected.ai_risk_band}
                </div>
              </div>

              {/* Risk bar */}
              <div className="w-full bg-gray-100 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full transition-all ${
                    selected.ai_risk_score <= 30 ? 'bg-green-500' :
                    selected.ai_risk_score <= 60 ? 'bg-yellow-500' :
                    selected.ai_risk_score <= 80 ? 'bg-orange-500' : 'bg-red-600'
                  }`}
                  style={{ width: `${selected.ai_risk_score}%` }}
                />
              </div>

              <div>
                <button
                  onClick={() => setExpandedRationale(e => !e)}
                  className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  AI Rationale {expandedRationale ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </button>
                {expandedRationale && (
                  <p className="mt-2 text-xs text-gray-600 leading-relaxed bg-gray-50 rounded-lg p-3">
                    {selected.ai_risk_rationale}
                  </p>
                )}
              </div>
            </div>

            {/* Override details */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-2 text-sm">
              <div className="font-semibold text-gray-800 mb-2">Override Details</div>
              <InfoRow label="Override Ref" value={selected.override_ref} />
              <InfoRow label="Trade ID" value={`#${selected.trade_id}`} />
              <InfoRow label="Requested" value={new Date(selected.requested_at).toLocaleString()} />
              {selected.resolved_at && (
                <InfoRow label="Resolved" value={new Date(selected.resolved_at).toLocaleString()} />
              )}
              {selected.trader_justification && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Trader Justification</div>
                  <p className="text-sm text-gray-700 bg-gray-50 rounded p-2">{selected.trader_justification}</p>
                </div>
              )}
              {selected.approver_notes && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Approver Notes</div>
                  <p className="text-sm text-gray-700 bg-gray-50 rounded p-2">{selected.approver_notes}</p>
                </div>
              )}
            </div>

            {/* Action form (only if pending) */}
            {selected.status === 'PENDING' && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3">
                <div className="font-semibold text-gray-800">Take Action</div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Acting Supervisor *</label>
                  <select
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
                    value={approverId}
                    onChange={e => setApproverId(e.target.value)}
                  >
                    <option value="">Select supervisor</option>
                    {supervisors.map(u => (
                      <option key={u.id} value={u.id}>{u.full_name} ({u.role.replace('_', ' ')})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
                  <textarea
                    rows={3}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none"
                    placeholder="Decision rationale..."
                    value={approverNotes}
                    onChange={e => setApproverNotes(e.target.value)}
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleAction('APPROVED')}
                    disabled={!approverId || acting}
                    className="flex-1 flex items-center justify-center gap-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-50 transition-colors"
                  >
                    <CheckCircle size={15} /> Approve
                  </button>
                  <button
                    onClick={() => handleAction('REJECTED')}
                    disabled={!approverId || acting}
                    className="flex-1 flex items-center justify-center gap-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-50 transition-colors"
                  >
                    <XCircle size={15} /> Reject
                  </button>
                  <button
                    onClick={handleEscalate}
                    disabled={!approverId || acting}
                    className="flex items-center justify-center gap-1.5 border border-orange-400 text-orange-700 hover:bg-orange-50 rounded-lg px-3 py-2 text-sm font-medium disabled:opacity-50 transition-colors"
                  >
                    <ArrowUpCircle size={15} />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-gray-500 text-xs">{label}</span>
      <span className="font-medium text-xs text-right">{value}</span>
    </div>
  )
}
