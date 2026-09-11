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
import ApplicationSummaryPage from './pages/ApplicationSummaryPage.jsx'

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
            regardless of wizard progress. Application summary is reached only via a
            button on the Scheme Match results view, which hands it data as router
            navigation state -- not gated by RequireStep since the page itself handles
            the no-state case gracefully (e.g. a direct visit or reload). */}
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/advisory-chat" element={<AdvisoryChatPage />} />
        <Route path="/application-summary" element={<ApplicationSummaryPage />} />
      </Route>
    </Routes>
  )
}
