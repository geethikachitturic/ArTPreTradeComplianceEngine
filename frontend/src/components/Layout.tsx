import { NavLink, Outlet } from 'react-router-dom'
import clsx from 'clsx'
import { Shield, Zap, CheckSquare, BookOpen, BarChart2, FileText } from 'lucide-react'

const NAV = [
  { to: '/stub1',     label: 'Trade Generator',   icon: Zap,         desc: 'Stub 1' },
  { to: '/trader',    label: 'Trader',             icon: Shield,      desc: 'Manual Entry' },
  { to: '/approvals', label: 'Approvals',          icon: CheckSquare, desc: 'Stub 2' },
  { to: '/rules',     label: 'Rules Manager',      icon: BookOpen,    desc: 'Controls Team' },
  { to: '/dashboard', label: 'MI Dashboard',       icon: BarChart2,   desc: 'Management' },
  { to: '/audit',     label: 'Audit Log',          icon: FileText,    desc: 'Compliance' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <header className="bg-slate-900 text-white px-6 py-3 flex items-center gap-4 shadow-lg">
        <div className="flex items-center gap-2">
          <Shield className="text-blue-400" size={22} />
          <span className="font-bold text-lg tracking-tight">ArT</span>
          <span className="text-slate-400 text-sm font-normal">Pre-Trade Controls Engine</span>
        </div>
        <div className="ml-auto text-xs text-slate-400">FINRA Rule 4210 · Regulation T · 2026 Amendments</div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <nav className="w-52 bg-slate-800 text-slate-300 flex flex-col py-4 gap-1 shrink-0">
          {NAV.map(({ to, label, icon: Icon, desc }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => clsx(
                'flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'hover:bg-slate-700 hover:text-white',
              )}
            >
              <Icon size={16} className="shrink-0" />
              <div>
                <div className="font-medium leading-tight">{label}</div>
                <div className="text-xs opacity-60">{desc}</div>
              </div>
            </NavLink>
          ))}
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-6 bg-gray-50">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
