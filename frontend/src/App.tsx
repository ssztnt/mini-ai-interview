import { useEffect, useState } from 'react'
import { api } from './api/client'
import type { AppConfig } from './api/types'
import { DemoBanner, Header } from './components/Header'
import { Dots } from './components/ui'
import { AnalyzingScreen } from './screens/AnalyzingScreen'
import { HistoryScreen } from './screens/HistoryScreen'
import { InterviewScreen } from './screens/InterviewScreen'
import { PlanScreen } from './screens/PlanScreen'
import { StartScreen } from './screens/StartScreen'
import { SummaryScreen } from './screens/SummaryScreen'
import { useInterview } from './useInterview'

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  const session = useInterview()
  const { interview, busy, error } = session

  useEffect(() => {
    api.config().then(setConfig, () => setConfig(null))
  }, [])

  // Scroll to top whenever the screen changes.
  const screenKey = showHistory ? 'history' : `${interview?.status}-${interview?.turns.length}`
  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [screenKey])

  const goHome = () => {
    setShowHistory(false)
    if (interview?.status === 'completed') session.reset()
  }
  const goHistory = () => setShowHistory(true)
  const startNew = () => {
    setShowHistory(false)
    session.reset()
  }

  function renderScreen() {
    if (session.restoring) return <Dots className="text-muted" />
    if (showHistory) {
      return (
        <HistoryScreen
          onNew={startNew}
          onOpen={(id) => {
            setShowHistory(false)
            void session.open(id)
          }}
        />
      )
    }
    if (!interview) return <StartScreen busy={busy} error={error} onCreate={session.create} />

    switch (interview.status) {
      case 'planning':
        return (
          <PlanScreen
            interview={interview}
            busy={busy}
            error={error}
            onStart={session.start}
            onCancel={session.reset}
          />
        )
      case 'in_progress':
        return interview.awaiting_summary ? (
          <AnalyzingScreen error={error} onRetry={session.complete} />
        ) : (
          <InterviewScreen
            key={interview.turns.length}
            interview={interview}
            busy={busy}
            error={error}
            onAnswer={session.answer}
          />
        )
      case 'completed':
        return <SummaryScreen interview={interview} onNew={startNew} onHistory={goHistory} />
    }
  }

  return (
    <div className="flex min-h-svh flex-col">
      <Header config={config} onHome={goHome} onHistory={goHistory} />
      {config?.demo && <DemoBanner />}
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 pt-10 pb-24 sm:px-6 sm:pt-14">
        <div className="max-w-[680px]">{renderScreen()}</div>
      </main>
    </div>
  )
}
