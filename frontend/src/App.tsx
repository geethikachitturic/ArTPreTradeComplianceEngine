import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Stub1Page from './pages/Stub1Page'
import TraderPage from './pages/TraderPage'
import ApprovalsPage from './pages/ApprovalsPage'
import RulesPage from './pages/RulesPage'
import DashboardPage from './pages/DashboardPage'
import AuditPage from './pages/AuditPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/stub1" replace />} />
          <Route path="stub1"     element={<Stub1Page />} />
          <Route path="trader"    element={<TraderPage />} />
          <Route path="approvals" element={<ApprovalsPage />} />
          <Route path="rules"     element={<RulesPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="audit"     element={<AuditPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
