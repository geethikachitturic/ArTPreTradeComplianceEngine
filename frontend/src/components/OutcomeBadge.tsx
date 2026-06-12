import clsx from 'clsx'
import type { DecisionOutcome, TradeStatus } from '../types'

const CONFIG: Record<string, { label: string; className: string }> = {
  CLEAN_PASS:               { label: 'Clean Pass',               className: 'bg-green-100 text-green-800 border-green-300' },
  SOFT_BLOCK:               { label: 'Soft Block',               className: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
  HARD_BLOCK:               { label: 'Hard Block',               className: 'bg-red-100 text-red-800 border-red-300' },
  HARD_BLOCK_WITH_OVERRIDE: { label: 'Hard Block + Override',    className: 'bg-orange-100 text-orange-800 border-orange-300' },
  OVERRIDE_APPROVED:        { label: 'Override Approved',        className: 'bg-blue-100 text-blue-800 border-blue-300' },
  OVERRIDE_REJECTED:        { label: 'Override Rejected',        className: 'bg-gray-100 text-gray-700 border-gray-300' },
  PENDING:                  { label: 'Pending',                  className: 'bg-purple-100 text-purple-800 border-purple-300' },
  APPROVED:                 { label: 'Approved',                 className: 'bg-green-100 text-green-800 border-green-300' },
  REJECTED:                 { label: 'Rejected',                 className: 'bg-red-100 text-red-800 border-red-300' },
  ESCALATED:                { label: 'Escalated',                className: 'bg-orange-100 text-orange-800 border-orange-300' },
}

interface Props {
  outcome: string
  size?: 'sm' | 'md' | 'lg'
}

export default function OutcomeBadge({ outcome, size = 'md' }: Props) {
  const config = CONFIG[outcome] ?? { label: outcome, className: 'bg-gray-100 text-gray-700 border-gray-300' }
  return (
    <span className={clsx(
      'inline-flex items-center font-semibold rounded-full border',
      size === 'sm' && 'px-2 py-0.5 text-xs',
      size === 'md' && 'px-3 py-1 text-sm',
      size === 'lg' && 'px-4 py-1.5 text-base',
      config.className,
    )}>
      {config.label}
    </span>
  )
}
