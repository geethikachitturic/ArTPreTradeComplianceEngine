import { useState, useEffect } from 'react'
import { Shield, Send, AlertCircle } from 'lucide-react'
import { checkTrade, getUsers } from '../services/api'
import OutcomeBadge from '../components/OutcomeBadge'
import type { TradeCheckResponse, User } from '../types'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

const OUTCOME_COLOURS = {
  CLEAN_PASS:               'border-green-400 bg-green-50',
  SOFT_BLOCK:               'border-yellow-400 bg-yellow-50',
  HARD_BLOCK:               'border-red-400 bg-red-50',
  HARD_BLOCK_WITH_OVERRIDE: 'border-orange-400 bg-orange-50',
}

export default function TraderPage() {
  const [users, setUsers] = useState<User[]>([])
  const [result, setResult] = useState<TradeCheckResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    trader_id: '',
    asset_class: 'EQUITY',
    product_type: 'STOCK',
    direction: 'BUY',
    ticker: '',
    quantity: '',
    price: '',
    account_id: 'ACC-00001',
    account_type: 'MARGIN',
    account_equity: '',
    existing_long_market_value: '0',
    existing_short_market_value: '0',
    existing_debit_balance: '0',
    intraday_margin_level: '0',
    deficit_count_30d: '0',
    is_90day_freeze_active: false,
    credit_rating: '',
  })

  useEffect(() => {
    getUsers().then(u => {
      setUsers(u)
      if (u.length > 0) setForm(f => ({ ...f, trader_id: String(u[0].id) }))
    })
  }, [])

  const set = (k: string, v: string | boolean) => setForm(f => ({ ...f, [k]: v }))

  const notional = Number(form.quantity) * Number(form.price)

  const PRODUCT_OPTIONS: Record<string, { value: string; label: string }[]> = {
    EQUITY: [
      { value: 'STOCK', label: 'Stock' },
      { value: 'ETF', label: 'ETF' },
      { value: 'EQUITY_OPTION', label: 'Equity Option' },
    ],
    FIXED_INCOME: [
      { value: 'GOVT_BOND', label: 'Government Bond' },
      { value: 'CORP_BOND_IG', label: 'Corporate Bond (Investment Grade)' },
      { value: 'CORP_BOND_HY', label: 'Corporate Bond (High Yield)' },
      { value: 'MUNICIPAL_BOND', label: 'Municipal Bond' },
    ],
  }

  const DIRECTION_OPTIONS = [
    { value: 'BUY', label: 'Buy' },
    { value: 'SELL', label: 'Sell' },
    { value: 'SHORT_SELL', label: 'Short Sell' },
    { value: 'BUY_TO_COVER', label: 'Buy to Cover' },
    { value: 'SHORT_PUT', label: 'Short Put' },
    { value: 'SHORT_CALL', label: 'Short Call' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = {
        trader_id: Number(form.trader_id),
        asset_class: form.asset_class,
        product_type: form.product_type,
        direction: form.direction,
        ticker: form.ticker.toUpperCase(),
        quantity: Number(form.quantity),
        price: Number(form.price),
        account_id: form.account_id,
        account_type: form.account_type,
        account_equity: Number(form.account_equity),
        existing_long_market_value: Number(form.existing_long_market_value),
        existing_short_market_value: Number(form.existing_short_market_value),
        existing_debit_balance: Number(form.existing_debit_balance),
        intraday_margin_level: Number(form.intraday_margin_level),
        deficit_count_30d: Number(form.deficit_count_30d),
        is_90day_freeze_active: form.is_90day_freeze_active,
        credit_rating: form.credit_rating || null,
      }
      const res = await checkTrade(payload)
      setResult(res)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'An error occurred. Check backend connection.')
    } finally {
      setLoading(false)
    }
  }

  const traders = users.filter(u => u.role === 'TRADER')
  const products = PRODUCT_OPTIONS[form.asset_class] || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Shield className="text-blue-500" size={24} />
          Trader — Pre-Trade Check
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Enter trade details and submit to ArT for a real-time compliance decision.
        </p>
      </div>

      <div className="flex gap-6 items-start">
        {/* Trade entry form */}
        <div className="flex-1 bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Trader */}
            <section>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 border-b pb-1">Trader</h3>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Trader">
                  <select className={cls} value={form.trader_id} onChange={e => set('trader_id', e.target.value)} required>
                    <option value="">Select trader</option>
                    {traders.map(u => (
                      <option key={u.id} value={u.id}>{u.full_name} ({u.seniority_level})</option>
                    ))}
                  </select>
                </Field>
                <Field label="Account Type">
                  <select className={cls} value={form.account_type} onChange={e => set('account_type', e.target.value)}>
                    <option value="MARGIN">Margin</option>
                    <option value="CASH">Cash</option>
                    <option value="PORTFOLIO_MARGIN">Portfolio Margin</option>
                  </select>
                </Field>
              </div>
            </section>

            {/* Trade economics */}
            <section>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 border-b pb-1">Trade Economics</h3>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Asset Class">
                  <select className={cls} value={form.asset_class}
                    onChange={e => {
                      const ac = e.target.value
                      set('asset_class', ac)
                      set('product_type', PRODUCT_OPTIONS[ac][0].value)
                    }}>
                    <option value="EQUITY">Equity</option>
                    <option value="FIXED_INCOME">Fixed Income</option>
                  </select>
                </Field>
                <Field label="Product Type">
                  <select className={cls} value={form.product_type} onChange={e => set('product_type', e.target.value)}>
                    {products.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                  </select>
                </Field>
                <Field label="Direction">
                  <select className={cls} value={form.direction} onChange={e => set('direction', e.target.value)}>
                    {DIRECTION_OPTIONS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                  </select>
                </Field>
                <Field label="Ticker / Instrument">
                  <input className={cls} value={form.ticker} onChange={e => set('ticker', e.target.value)}
                    placeholder="e.g. AAPL" required />
                </Field>
                <Field label="Quantity">
                  <input className={cls} type="number" value={form.quantity} onChange={e => set('quantity', e.target.value)}
                    placeholder="0" required />
                </Field>
                <Field label="Price ($)">
                  <input className={cls} type="number" step="0.01" value={form.price} onChange={e => set('price', e.target.value)}
                    placeholder="0.00" required />
                </Field>
              </div>
              {notional > 0 && (
                <div className="mt-2 text-sm text-blue-700 font-medium">
                  Notional: {fmt(notional)}
                </div>
              )}
              {form.asset_class === 'FIXED_INCOME' && (
                <div className="mt-3">
                  <Field label="Credit Rating">
                    <input className={cls} value={form.credit_rating} onChange={e => set('credit_rating', e.target.value)}
                      placeholder="e.g. BBB+" />
                  </Field>
                </div>
              )}
            </section>

            {/* Account state */}
            <section>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 border-b pb-1">Account State</h3>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Account Equity ($)">
                  <input className={cls} type="number" value={form.account_equity} onChange={e => set('account_equity', e.target.value)}
                    placeholder="0" required />
                </Field>
                <Field label="Existing Long MV ($)">
                  <input className={cls} type="number" value={form.existing_long_market_value} onChange={e => set('existing_long_market_value', e.target.value)} />
                </Field>
                <Field label="Existing Short MV ($)">
                  <input className={cls} type="number" value={form.existing_short_market_value} onChange={e => set('existing_short_market_value', e.target.value)} />
                </Field>
                <Field label="Debit Balance ($)">
                  <input className={cls} type="number" value={form.existing_debit_balance} onChange={e => set('existing_debit_balance', e.target.value)} />
                </Field>
                <Field label="Intraday Margin Level ($)">
                  <input className={cls} type="number" value={form.intraday_margin_level} onChange={e => set('intraday_margin_level', e.target.value)} />
                </Field>
                <Field label="Deficit Count (30d)">
                  <input className={cls} type="number" value={form.deficit_count_30d} onChange={e => set('deficit_count_30d', e.target.value)} />
                </Field>
              </div>
              <label className="flex items-center gap-2 mt-3 cursor-pointer">
                <input type="checkbox" className="rounded" checked={form.is_90day_freeze_active}
                  onChange={e => set('is_90day_freeze_active', e.target.checked)} />
                <span className="text-sm text-gray-700">90-day freeze active (FINRA Rule 4210(d)(2)(D))</span>
              </label>
            </section>

            {error && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
                <AlertCircle size={16} />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-semibold transition-colors disabled:opacity-50"
            >
              <Send size={16} />
              {loading ? 'Running ArT Check...' : 'Submit to ArT'}
            </button>
          </form>
        </div>

        {/* Decision panel */}
        <div className="w-96 shrink-0 space-y-4">
          {result ? (
            <>
              <div className={`rounded-xl border-2 p-5 space-y-4 ${OUTCOME_COLOURS[result.decision.outcome]}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-gray-500 font-mono">{result.trade.trade_ref}</div>
                    <div className="font-bold text-xl mt-1">{result.trade.ticker}</div>
                  </div>
                  <OutcomeBadge outcome={result.decision.outcome} size="lg" />
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm">
                  <Stat label="Notional" value={fmt(result.trade.notional)} />
                  <Stat label="Account Type" value={result.trade.account_type} />
                  {result.decision.reg_t_margin_required != null && (
                    <>
                      <Stat label="Reg T Required" value={fmt(result.decision.reg_t_margin_required)} />
                      <Stat label="Reg T Available" value={fmt(result.decision.reg_t_margin_available!)} />
                    </>
                  )}
                  {result.decision.intraday_margin_deficit != null && (
                    <Stat label="IML Deficit" value={fmt(result.decision.intraday_margin_deficit)} />
                  )}
                  <Stat label="Processing" value={`${result.decision.processing_time_ms}ms`} />
                </div>

                <div>
                  <div className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">Reasoning</div>
                  <p className="text-sm leading-relaxed text-gray-800">{result.decision.reasoning}</p>
                </div>

                {result.override_request_id && (
                  <div className="bg-orange-100 border border-orange-300 rounded-lg p-2 text-sm text-orange-800">
                    Override request #{result.override_request_id} raised. Pending supervisor review.
                  </div>
                )}
              </div>

              {result.decision.rules_triggered.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                  <div className="text-sm font-semibold text-gray-700 mb-3">
                    Rules Triggered ({result.decision.rules_triggered.length})
                  </div>
                  <div className="space-y-2">
                    {result.decision.rules_triggered.map((r, i) => (
                      <div key={i} className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs space-y-1">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-semibold text-gray-800">{r.rule_name}</span>
                          <OutcomeBadge outcome={r.block_type} size="sm" />
                        </div>
                        <div className="text-gray-400 font-mono">{r.rule_code} · {r.rule_type}</div>
                        <div className="text-gray-600 leading-relaxed">{r.description}</div>
                        {r.margin_required != null && (
                          <div className="text-gray-500">Required: {fmt(r.margin_required)} · Available: {fmt(r.margin_available!)}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-10 text-center text-gray-400 text-sm">
              Submit a trade to see the ArT decision here
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const cls = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-300'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {children}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-sm font-semibold text-gray-800">{value}</div>
    </div>
  )
}
