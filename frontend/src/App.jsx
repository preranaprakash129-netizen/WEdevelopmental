import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import RequireStep from './components/RequireStep.jsx'
import { useIntake } from './context/IntakeContext.jsx'
import IntakePage from './pages/IntakePage.jsx'
import FeasibilityPage from './pages/FeasibilityPage.jsx'
import CalculatorPage from './pages/CalculatorPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'

export default function App() {
  const { isIntakeComplete, feasibility } = useIntake()

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
        {/* Officer dashboard is a separate view, reachable anytime regardless of wizard progress. */}
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>
    </Routes>
  )
}
