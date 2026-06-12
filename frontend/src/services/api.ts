import axios from 'axios'
import type {
  ArtDecision, DailyTrend, DashboardSummary, NLRuleParsed,
  OverrideRequest, OverrideStats, Rule, TopRule, TopTrader,
  Trade, TradeCheckResponse, User
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Users
export const getUsers = () => api.get<User[]>('/users/').then(r => r.data)
export const getUser = (id: number) => api.get<User>(`/users/${id}`).then(r => r.data)

// ArT Engine
export const checkTrade = (payload: Record<string, unknown>) =>
  api.post<TradeCheckResponse>('/art/check', payload).then(r => r.data)
export const listDecisions = (params?: { limit?: number; outcome?: string }) =>
  api.get<ArtDecision[]>('/art/decisions', { params }).then(r => r.data)

// Rules
export const listRules = (active_only = false) =>
  api.get<Rule[]>('/rules/', { params: { active_only } }).then(r => r.data)
export const createRule = (payload: Record<string, unknown>) =>
  api.post<Rule>('/rules/', payload).then(r => r.data)
export const updateRule = (id: number, payload: Record<string, unknown>) =>
  api.patch<Rule>(`/rules/${id}`, payload).then(r => r.data)
export const deactivateRule = (id: number) =>
  api.delete(`/rules/${id}`)
export const parseNLRule = (natural_language: string) =>
  api.post<NLRuleParsed>('/rules/nl-parse', { natural_language }).then(r => r.data)
export const createFromNL = (natural_language: string) =>
  api.post<Rule>('/rules/nl-create', { natural_language }).then(r => r.data)

// Overrides
export const listOverrides = (status?: string) =>
  api.get<OverrideRequest[]>('/overrides/', { params: status ? { status } : {} }).then(r => r.data)
export const getOverride = (id: number) =>
  api.get<OverrideRequest>(`/overrides/${id}`).then(r => r.data)
export const actionOverride = (id: number, payload: { approver_id: number; status: string; approver_notes?: string }) =>
  api.post<OverrideRequest>(`/overrides/${id}/action`, payload).then(r => r.data)
export const escalateOverride = (id: number, escalated_by_id: number) =>
  api.post<OverrideRequest>(`/overrides/${id}/escalate`, null, { params: { escalated_by_id } }).then(r => r.data)

// Stubs (Trade Generator)
export const generateTrade = (scenario?: string, trader_id?: number) =>
  api.post<TradeCheckResponse & { scenario: string }>('/stubs/generate-trade', null, {
    params: { scenario, trader_id },
  }).then(r => r.data)
export const generateBatch = (count: number) =>
  api.post<{ count: number; results: (TradeCheckResponse & { scenario: string })[] }>(
    '/stubs/generate-batch', null, { params: { count } }
  ).then(r => r.data)
export const getScenarios = () =>
  api.get<{ scenarios: { key: string; label: string; weight: number }[] }>('/stubs/scenarios').then(r => r.data)

// Reports
export const getSummary = (days = 30) =>
  api.get<DashboardSummary>('/reports/summary', { params: { days } }).then(r => r.data)
export const getDailyTrend = (days = 14) =>
  api.get<DailyTrend[]>('/reports/daily-trend', { params: { days } }).then(r => r.data)
export const getTopRules = (days = 30) =>
  api.get<TopRule[]>('/reports/top-rules', { params: { days } }).then(r => r.data)
export const getTopTraders = (days = 30) =>
  api.get<TopTrader[]>('/reports/top-traders', { params: { days } }).then(r => r.data)
export const getOverrideStats = (days = 30) =>
  api.get<OverrideStats>('/reports/override-stats', { params: { days } }).then(r => r.data)
export const nlQuery = (query: string) =>
  api.post('/reports/nl-query', { query }).then(r => r.data)

// Audit
export const getAuditLog = (params?: { days?: number; event_type?: string; limit?: number }) =>
  api.get('/audit/', { params }).then(r => r.data)
