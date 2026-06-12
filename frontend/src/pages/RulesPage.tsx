import { useState, useEffect, useCallback } from 'react'
import { BookOpen, Plus, Sparkles, ToggleLeft, ToggleRight, Loader, CheckCircle, AlertCircle } from 'lucide-react'
import { listRules, parseNLRule, createFromNL, updateRule } from '../services/api'
import OutcomeBadge from '../components/OutcomeBadge'
import type { NLRuleParsed, Rule } from '../types'

const RULE_TYPE_COLOURS: Record<string, string> = {
  REG_T:      'bg-blue-100 text-blue-700 border-blue-200',
  FINRA_4210: 'bg-purple-100 text-purple-700 border-purple-200',
  CUSTOM:     'bg-emerald-100 text-emerald-700 border-emerald-200',
}

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([])
  const [loading, setLoading] = useState(false)
  const [nlInput, setNlInput] = useState('')
  const [nlParsed, setNlParsed] = useState<NLRuleParsed | null>(null)
  const [nlParsing, setNlParsing] = useState(false)
  const [nlSaving, setNlSaving] = useState(false)
  const [nlError, setNlError] = useState('')
  const [nlSuccess, setNlSuccess] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [showActiveOnly, setShowActiveOnly] = useState(false)
  const [selected, setSelected] = useState<Rule | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await listRules(showActiveOnly)
      setRules(r)
    } finally {
      setLoading(false)
    }
  }, [showActiveOnly])

  useEffect(() => { load() }, [load])

  const handleParse = async () => {
    if (!nlInput.trim()) return
    setNlParsing(true)
    setNlParsed(null)
    setNlError('')
    try {
      const res = await parseNLRule(nlInput)
      setNlParsed(res)
    } catch {
      setNlError('Failed to parse rule. Check backend connection.')
    } finally {
      setNlParsing(false)
    }
  }

  const handleSaveNL = async () => {
    if (!nlParsed) return
    setNlSaving(true)
    setNlSuccess(false)
    try {
      await createFromNL(nlInput)
      setNlInput('')
      setNlParsed(null)
      setNlSuccess(true)
      await load()
      setTimeout(() => setNlSuccess(false), 3000)
    } finally {
      setNlSaving(false)
    }
  }

  const toggleActive = async (rule: Rule) => {
    await updateRule(rule.id, { is_active: !rule.is_active })
    await load()
  }

  const filtered = rules.filter(r => {
    if (filterType && r.rule_type !== filterType) return false
    return true
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <BookOpen className="text-emerald-600" size={24} />
          Rules Manager
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          View and manage pre-trade control rules. Use the AI builder to add new rules in plain English.
        </p>
      </div>

      {/* NL Rules Builder */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="text-yellow-500" size={18} />
          <span className="font-semibold text-gray-800">AI Natural Language Rules Builder</span>
          <span className="text-xs text-gray-400 bg-gray-100 rounded px-2 py-0.5">Powered by ArT AI</span>
        </div>

        <div className="flex gap-3">
          <textarea
            rows={2}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-yellow-300"
            placeholder='Describe a rule in plain English, e.g. "Block any equity trade where the notional exceeds $5M and the trader is below VP level"'
            value={nlInput}
            onChange={e => setNlInput(e.target.value)}
          />
          <button
            onClick={handleParse}
            disabled={nlParsing || !nlInput.trim()}
            className="flex items-center gap-2 bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 self-start transition-colors"
          >
            {nlParsing ? <Loader size={15} className="animate-spin" /> : <Sparkles size={15} />}
            Parse
          </button>
        </div>

        {nlError && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
            <AlertCircle size={14} /> {nlError}
          </div>
        )}

        {nlSuccess && (
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-sm text-green-700">
            <CheckCircle size={14} /> Rule created successfully.
          </div>
        )}

        {nlParsed && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-800">Parsed Rule — Review before saving</span>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-gray-500">AI Confidence:</span>
                <span className={`font-bold ${nlParsed.confidence >= 0.7 ? 'text-green-700' : 'text-yellow-700'}`}>
                  {Math.round(nlParsed.confidence * 100)}%
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-gray-500">Name:</span> <strong>{nlParsed.name}</strong></div>
              <div><span className="text-gray-500">Rule Type:</span> <strong>{nlParsed.rule_type}</strong></div>
              <div><span className="text-gray-500">Asset Class:</span> <strong>{nlParsed.asset_class_scope}</strong></div>
              <div><span className="text-gray-500">Block Type:</span> <OutcomeBadge outcome={nlParsed.block_type} size="sm" /></div>
            </div>

            {(nlParsed.conditions?.rules as any[])?.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1">Conditions detected:</div>
                <div className="flex flex-wrap gap-2">
                  {(nlParsed.conditions.rules as any[]).map((c: any, i: number) => (
                    <span key={i} className="bg-white border border-gray-200 rounded-full px-3 py-0.5 text-xs font-medium text-gray-700">
                      {c.label}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-white border border-yellow-200 rounded-lg p-3 text-xs text-gray-600 leading-relaxed">
              <strong className="text-yellow-700">AI Explanation: </strong>{nlParsed.explanation}
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleSaveNL}
                disabled={nlSaving}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
              >
                {nlSaving ? <Loader size={14} className="animate-spin" /> : <Plus size={14} />}
                Confirm & Create Rule
              </button>
              <button
                onClick={() => setNlParsed(null)}
                className="border border-gray-300 rounded-lg px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                Discard
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Filter controls */}
      <div className="flex items-center gap-4">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {['', 'REG_T', 'FINRA_4210', 'CUSTOM'].map(t => (
            <button key={t} onClick={() => setFilterType(t)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                filterType === t ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
              }`}>
              {t || 'All Types'}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input type="checkbox" checked={showActiveOnly} onChange={e => setShowActiveOnly(e.target.checked)} className="rounded" />
          Active only
        </label>
        <span className="text-sm text-gray-400 ml-auto">{filtered.length} rules</span>
      </div>

      {/* Rules table + detail */}
      <div className="flex gap-4">
        <div className="flex-1 min-w-0 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="py-12 text-center text-gray-400 text-sm">Loading rules...</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="text-left px-4 py-3">Code</th>
                  <th className="text-left px-4 py-3">Name</th>
                  <th className="text-left px-4 py-3">Type</th>
                  <th className="text-left px-4 py-3">Scope</th>
                  <th className="text-left px-4 py-3">Block</th>
                  <th className="text-left px-4 py-3">Priority</th>
                  <th className="text-left px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(r => (
                  <tr key={r.id}
                    onClick={() => setSelected(r)}
                    className={`border-t border-gray-50 cursor-pointer transition-colors ${
                      selected?.id === r.id ? 'bg-emerald-50' : 'hover:bg-gray-50'
                    } ${!r.is_active ? 'opacity-50' : ''}`}>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{r.rule_code}</td>
                    <td className="px-4 py-3 font-medium max-w-[240px]">
                      <div className="truncate">{r.name}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded border ${RULE_TYPE_COLOURS[r.rule_type]}`}>
                        {r.rule_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-xs">{r.asset_class_scope.replace('_', ' ')}</td>
                    <td className="px-4 py-3"><OutcomeBadge outcome={r.block_type} size="sm" /></td>
                    <td className="px-4 py-3 text-gray-500">{r.priority}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={e => { e.stopPropagation(); toggleActive(r) }}
                        className="flex items-center gap-1 text-xs"
                      >
                        {r.is_active
                          ? <ToggleRight className="text-green-600" size={18} />
                          : <ToggleLeft className="text-gray-400" size={18} />}
                        {r.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="w-80 shrink-0 bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3 overflow-auto max-h-[580px]">
            <div>
              <div className="font-mono text-xs text-gray-400">{selected.rule_code}</div>
              <div className="font-bold text-base mt-1">{selected.name}</div>
              <div className="mt-2 flex flex-wrap gap-1">
                <span className={`text-xs font-medium px-2 py-0.5 rounded border ${RULE_TYPE_COLOURS[selected.rule_type]}`}>
                  {selected.rule_type}
                </span>
                <OutcomeBadge outcome={selected.block_type} size="sm" />
              </div>
            </div>

            <div className="text-sm text-gray-600 leading-relaxed">{selected.description}</div>

            {selected.natural_language_description && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-xs text-gray-700 leading-relaxed">
                <span className="font-semibold text-yellow-700">Plain English: </span>
                {selected.natural_language_description}
              </div>
            )}

            {selected.conditions && Object.keys(selected.conditions).length > 0 && (
              <div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Conditions</div>
                <pre className="text-xs bg-gray-50 border border-gray-200 rounded-lg p-3 overflow-auto text-gray-700">
                  {JSON.stringify(selected.conditions, null, 2)}
                </pre>
              </div>
            )}

            <div className="text-xs text-gray-400 space-y-1">
              <div>Created by: {selected.created_by}</div>
              <div>Created: {new Date(selected.created_at).toLocaleDateString()}</div>
              <div>Priority: {selected.priority}</div>
            </div>

            {selected.rule_type === 'CUSTOM' && (
              <button
                onClick={() => toggleActive(selected)}
                className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
                  selected.is_active
                    ? 'bg-red-50 border border-red-200 text-red-700 hover:bg-red-100'
                    : 'bg-green-50 border border-green-200 text-green-700 hover:bg-green-100'
                }`}
              >
                {selected.is_active ? 'Deactivate Rule' : 'Activate Rule'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
