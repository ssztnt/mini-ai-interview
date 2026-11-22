import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api/client'
import type { Interview, Objective } from './api/types'

const STORAGE_KEY = 'mini-ai-interview:current'

function readSavedId(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

/**
 * Holds the interview the user is working on and wraps every backend call
 * with loading + error state. The interview ID is kept in sessionStorage so a
 * page refresh resumes where the user left off.
 */
export function useInterview() {
  const [interview, setInterviewState] = useState<Interview | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedId] = useState(readSavedId)
  const [restoring, setRestoring] = useState(savedId !== null)

  const setInterview = useCallback((next: Interview | null) => {
    setInterviewState(next)
    try {
      if (next && next.status !== 'completed') sessionStorage.setItem(STORAGE_KEY, next.id)
      else sessionStorage.removeItem(STORAGE_KEY)
    } catch {
      // Storage can be unavailable (private mode); resuming is a convenience only.
    }
  }, [])

  // Resume an unfinished interview after a refresh.
  useEffect(() => {
    if (!savedId) return
    api
      .getInterview(savedId)
      .then(setInterview, () => setInterview(null))
      .finally(() => setRestoring(false))
  }, [savedId, setInterview])

  const run = useCallback(
    async (action: () => Promise<Interview>) => {
      setBusy(true)
      setError(null)
      try {
        setInterview(await action())
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Something went wrong.')
      } finally {
        setBusy(false)
      }
    },
    [setInterview],
  )

  const id = interview?.id ?? ''

  const actions = {
    create: (topic: string, numQuestions: number) =>
      run(() => api.createInterview(topic, numQuestions)),
    start: (objectives: Objective[]) =>
      run(async () => {
        await api.updatePlan(id, objectives)
        return api.start(id)
      }),
    answer: (text: string) => run(() => api.answer(id, text)),
    complete: () => run(() => api.complete(id)),
    open: (interviewId: string) => run(() => api.getInterview(interviewId)),
    reset: () => {
      setError(null)
      setInterview(null)
    },
  }

  // Once every question is answered, ask for the summary automatically.
  const requested = useRef<string | null>(null)
  useEffect(() => {
    if (interview?.awaiting_summary && requested.current !== interview.id) {
      requested.current = interview.id
      void actions.complete()
    }
  })

  return { interview, busy, error, restoring, ...actions }
}
