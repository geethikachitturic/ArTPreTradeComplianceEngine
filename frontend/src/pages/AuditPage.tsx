import { useState, useEffect, useCallback } from 'react'
import { FileText, RefreshCw } from 'lucide-react'
import { getAuditLog } from '../services/api'

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [days, setDays] = useState(7)
  const [eventType, setEventType] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getAuditLog({ days, event_type: eventType || undefined, limit: 200 })
      setLogs(res)
    } finally {
      setLoading(false)
    }
  }, [days, eventType])

  useEffect(() => { load() }, [load])

  const EVENT_COLOURS: Record<string, string> = {
    TRADE_CHECKED:       'bg-blue-100 text-blue-700',
    OVERRIDE_APPROVED:   'bg-green-100 text-green-700',
    OVERRIDE_REJECTED:   'bg-red-100 text-red-700',
    OVERRIDE_ESCALATED:  'bg-orange-100 text-orange-700',
    OVERRIDE_PENDING:    'bg-yellow-100 text-yellow-700',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <FileText className="text-gray-500" size={24} />
            Audit Log
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Immutable record of all ArT decisions, override actions, and system events.
          </p>
        </div>
        <button onClick={load} disabled={loading}
          className="flex items-center gap-2 border border-gray-300 rounded-lg px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center">
        <select className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white"
          value={days} onChange={e => setDays(Number(e.target.value))}>
          <option value={1}>Today</option>
          <option value={7}>Past 7 days</option>
          <option value={30}>Past 30 days</option>
          <option value={90}>Past 90 days</option>
        </select>
        <select className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white"
          value={eventType} onChange={e => setEventType(e.target.value)}>
          <option value="">All Events</option>
          <option value="TRADE_CHECKED">Trade Checked</option>
          <option value="OVERRIDE_APPROVED">Override Approved</option>
          <option value="OVERRIDE_REJECTED">Override Rejected</option>
          <option value="OVERRIDE_ESCALATED">Override Escalated</option>
        </select>
        <span className="text-sm text-gray-400">{logs.length} entries</span>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-gray-400 text-sm">Loading audit log...</div>
        ) : logs.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">No audit entries for this period</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide sticky top-0">
              <tr>
                <th className="text-left px-4 py-3">Timestamp</th>
                <th className="text-left px-4 py-3">Event</th>
                <th className="text-left px-4 py-3">Entity</th>
                <th className="text-left px-4 py-3">User</th>
                <th className="text-left px-4 py-3">Description</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={log.id} className="border-t border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-2.5 text-gray-400 text-xs whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${EVENT_COLOURS[log.event_type] ?? 'bg-gray-100 text-gray-600'}`}>
                      {log.event_type.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-gray-500 text-xs">
                    {log.entity_type} #{log.entity_id}
                  </td>
                  <td className="px-4 py-2.5 text-gray-700 text-xs">{log.username || '—'}</td>
                  <td className="px-4 py-2.5 text-gray-600 text-xs max-w-md truncate">{log.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
