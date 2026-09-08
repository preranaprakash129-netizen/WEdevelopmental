import { createContext, useCallback, useContext, useMemo, useState } from 'react'

const STORAGE_KEY = 'sih26091.intake'

const EMPTY_INTAKE = {
  location: '',
  category: '',
  margin_capital: '',
}

function loadInitial() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? { ...EMPTY_INTAKE, ...JSON.parse(raw) } : EMPTY_INTAKE
  } catch {
    return EMPTY_INTAKE
  }
}

const IntakeContext = createContext(null)

export function IntakeProvider({ children }) {
  const [intake, setIntakeState] = useState(loadInitial)
  const [feasibility, setFeasibility] = useState(null)
  const [calculator, setCalculator] = useState(null)

  const setIntake = useCallback((next) => {
    setIntakeState(next)
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    } catch {
      // ignore storage errors (e.g. private browsing)
    }
  }, [])

  const isIntakeComplete = Boolean(intake.location && intake.category && intake.margin_capital)

  const value = useMemo(
    () => ({
      intake,
      setIntake,
      isIntakeComplete,
      feasibility,
      setFeasibility,
      calculator,
      setCalculator,
    }),
    [intake, setIntake, isIntakeComplete, feasibility, calculator],
  )

  return <IntakeContext.Provider value={value}>{children}</IntakeContext.Provider>
}

export function useIntake() {
  const ctx = useContext(IntakeContext)
  if (!ctx) throw new Error('useIntake must be used within IntakeProvider')
  return ctx
}
