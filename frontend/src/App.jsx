import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import RequireStep from './components/RequireStep.jsx'
import { useIntake } from './context/IntakeContext.jsx'
import IntakePage from './pages/IntakePage.jsx'
import FeasibilityPage from './pages/FeasibilityPage.jsx'
import CalculatorPage from './pages/CalculatorPage.jsx'
import EssScorePage from './pages/EssScorePage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import AdvisoryChatPage from './pages/AdvisoryChatPage.jsx'
import SchemeMatchPage from './pages/SchemeMatchPage.jsx'

export default function App() {
  const { isIntakeComplete, feasibility, calculator, intake } = useIntake()
  const hasCategory = Boolean(intake.category)

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<IntakePage />} />
        <Route
          path="/feasibility"
          element={
            <RequireStep ok={isIntakeComplete} fallback="/">
              <FeasibilityPage />
            </RequireStep>
          }
        />
        <Route
          path="/calculator"
          element={
            <RequireStep ok={isIntakeComplete && Boolean(feasibility)} fallback="/feasibility">
              <CalculatorPage />
            </RequireStep>
          }
        />
        <Route
          path="/ess-score"
          element={
            <RequireStep ok={isIntakeComplete && Boolean(calculator)} fallback="/calculator">
              <EssScorePage />
            </RequireStep>
          }
        />
        <Route
          path="/scheme-match"
          element={
            <RequireStep ok={hasCategory} fallback="/">
              <SchemeMatchPage />
            </RequireStep>
          }
        />
        {/* Officer dashboard and advisory chat are separate views, reachable anytime
            regardless of wizard progress. */}
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/advisory-chat" element={<AdvisoryChatPage />} />
      </Route>
    </Routes>
  )
}
