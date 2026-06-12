export type AssetClass = 'EQUITY' | 'FIXED_INCOME'
export type ProductType = 'STOCK' | 'ETF' | 'EQUITY_OPTION' | 'GOVT_BOND' | 'CORP_BOND_IG' | 'CORP_BOND_HY' | 'MUNICIPAL_BOND'
export type TradeDirection = 'BUY' | 'SELL' | 'SHORT_SELL' | 'BUY_TO_COVER' | 'SHORT_PUT' | 'SHORT_CALL'
export type AccountType = 'CASH' | 'MARGIN' | 'PORTFOLIO_MARGIN'
export type TradeStatus = 'PENDING_CHECK' | 'CLEAN_PASS' | 'SOFT_BLOCK' | 'HARD_BLOCK' | 'HARD_BLOCK_WITH_OVERRIDE' | 'OVERRIDE_APPROVED' | 'OVERRIDE_REJECTED'
export type DecisionOutcome = 'CLEAN_PASS' | 'SOFT_BLOCK' | 'HARD_BLOCK' | 'HARD_BLOCK_WITH_OVERRIDE'
export type RuleType = 'REG_T' | 'FINRA_4210' | 'CUSTOM'
export type BlockType = 'SOFT_BLOCK' | 'HARD_BLOCK' | 'HARD_BLOCK_WITH_OVERRIDE'
export type AssetClassScope = 'EQUITY' | 'FIXED_INCOME' | 'ALL'
export type OverrideStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'ESCALATED'
export type RiskBand = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type UserRole = 'TRADER' | 'SUPERVISOR' | 'HEAD_OF_DESK' | 'MANAGING_DIRECTOR' | 'CONTROLS_TEAM' | 'ADMIN'
export type SeniorityLevel = 'ANALYST' | 'ASSOCIATE' | 'VP' | 'DIRECTOR' | 'MANAGING_DIRECTOR'

export interface User {
  id: number
  username: string
  full_name: string
  role: UserRole
  seniority_level: SeniorityLevel
  desk: string
  is_active: boolean
  created_at: string
}

export interface Trade {
  id: number
  trade_ref: string
  trader_id: number
  asset_class: AssetClass
  product_type: ProductType
  direction: TradeDirection
  ticker: string
  quantity: number
  price: number
  notional: number
  account_id: string
  account_type: AccountType
  account_equity: number
  existing_long_market_value: number
  existing_short_market_value: number
  existing_debit_balance: number
  intraday_margin_level: number
  deficit_count_30d: number
  is_90day_freeze_active: number
  credit_rating: string | null
  status: TradeStatus
  trade_date: string
  created_at: string
}

export interface TriggeredRule {
  rule_id: number | null
  rule_code: string
  rule_name: string
  rule_type: string
  block_type: string
  outcome: string
  description: string
  margin_required?: number
  margin_available?: number
  intraday_margin_deficit?: number
  iml_before?: number
  iml_after?: number
}

export interface ArtDecision {
  id: number
  decision_ref: string
  trade_id: number
  outcome: DecisionOutcome
  rules_triggered: TriggeredRule[]
  reasoning: string
  reg_t_margin_required: number | null
  reg_t_margin_available: number | null
  intraday_margin_deficit: number | null
  processing_time_ms: number | null
  created_at: string
}

export interface TradeCheckResponse {
  trade: Trade
  decision: ArtDecision
  override_request_id: number | null
}

export interface Rule {
  id: number
  rule_code: string
  name: string
  description: string
  natural_language_description: string | null
  rule_type: RuleType
  asset_class_scope: AssetClassScope
  block_type: BlockType
  conditions: Record<string, unknown> | null
  is_active: boolean
  priority: number
  created_by: string
  created_at: string
  updated_at: string
}

export interface NLRuleParsed {
  name: string
  description: string
  natural_language_description: string
  rule_type: RuleType
  asset_class_scope: AssetClassScope
  block_type: BlockType
  conditions: Record<string, unknown>
  confidence: number
  explanation: string
}

export interface OverrideRequest {
  id: number
  override_ref: string
  decision_id: number
  trade_id: number
  requested_by_id: number
  approver_id: number | null
  status: OverrideStatus
  ai_risk_score: number
  ai_risk_band: RiskBand
  ai_risk_rationale: string
  trader_justification: string | null
  approver_notes: string | null
  requested_at: string
  resolved_at: string | null
}

export interface DashboardSummary {
  period_days: number
  total_trades: number
  outcomes: Record<DecisionOutcome, number>
  block_rate: number
  pending_overrides: number
}

export interface DailyTrend {
  date: string
  CLEAN_PASS: number
  SOFT_BLOCK: number
  HARD_BLOCK: number
  HARD_BLOCK_WITH_OVERRIDE: number
}

export interface TopRule {
  rule_code: string
  rule_name: string
  rule_type: string
  count: number
}

export interface TopTrader {
  trader_id: number
  trader_name: string
  desk: string
  seniority: string
  block_count: number
}

export interface OverrideStats {
  total: number
  approved: number
  rejected: number
  pending: number
  escalated: number
  approval_rate: number
  avg_ai_risk_score: number
}
