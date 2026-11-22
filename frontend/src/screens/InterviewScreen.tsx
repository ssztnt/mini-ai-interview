import { useState, type FormEvent, type KeyboardEvent } from 'react'
import type { Interview } from '../api/types'
import { Button, Dots, ErrorNote } from '../components/ui'

interface Props {
  interview: Interview
  busy: boolean
  error: string | null
  onAnswer: (answer: string) => void
}

export function InterviewScreen({ interview, busy, error, onAnswer }: Props) {
  // The parent re-mounts this screen per question (key=step), which resets the draft.
  const [draft, setDraft] = useState('')

  const current = interview.turns.at(-1)
  const previous = interview.turns.slice(0, -1)
  const step = interview.turns.length
  const total = interview.plan.length

  function submit(event?: FormEvent) {
    event?.preventDefault()
    if (draft.trim() && !busy) onAnswer(draft.trim())
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) submit()
  }

  if (!current) return null

  return (
    <div className="space-y-10">
      <Progress interview={interview} />

      {previous.length > 0 && (
        <details className="group text-[15px] text-muted">
          <summary className="cursor-pointer rounded select-none hover:text-ink">
            Earlier in this interview ({previous.length})
          </summary>
          <div className="mt-4 space-y-5 border-l border-rule pl-4">
            {previous.map((turn, i) => (
              <div key={i} className="space-y-1">
                <p className="font-serif text-[17px] text-ink">{turn.question}</p>
                <p className="leading-relaxed">{turn.answer}</p>
              </div>
            ))}
          </div>
        </details>
      )}

      <div key={step} className="space-y-3" aria-live="polite">
        {current.lead_in && (
          <p className="text-[17px] leading-relaxed text-muted">{current.lead_in}</p>
        )}
        <h1 className="font-serif text-3xl leading-snug tracking-tight sm:text-[2.1rem]">
          {current.question}
        </h1>
      </div>

      <form onSubmit={submit} className="space-y-4">
        <label htmlFor="answer" className="sr-only">
          Your answer
        </label>
        <textarea
          id="answer"
          autoFocus
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          maxLength={4000}
          rows={5}
          disabled={busy}
          placeholder="Write as much or as little as you like…"
          className="field-sizing-content min-h-36 w-full resize-none rounded-lg border border-rule bg-surface px-4 py-3.5 text-[17px] leading-relaxed placeholder:text-muted/60 focus:border-action focus:outline-none disabled:opacity-60"
        />

        {error && <ErrorNote message={error} />}

        <div className="flex flex-wrap items-center justify-between gap-3">
          {busy ? (
            <p className="flex items-center gap-2 text-[15px] text-muted">
              <Dots />
              {step === total ? 'Wrapping up' : 'Reading your answer'}
            </p>
          ) : (
            <p className="text-[14px] text-muted">
              <kbd className="font-sans">Ctrl</kbd> + <kbd className="font-sans">Enter</kbd> to send
            </p>
          )}
          <Button type="submit" disabled={!draft.trim() || busy}>
            {step === total ? 'Send final answer' : 'Send answer'}
          </Button>
        </div>
      </form>
    </div>
  )
}

function Progress({ interview }: { interview: Interview }) {
  const step = interview.turns.length
  const total = interview.plan.length
  return (
    <div className="space-y-3">
      <p className="text-[14px] text-muted">
        Question {step} of {total}:{' '}
        <span className="text-ink">{interview.plan[step - 1]?.theme}</span>
      </p>
      <ol className="flex gap-1.5" aria-label="Interview progress">
        {interview.plan.map((objective, i) => (
          <li
            key={i}
            title={objective.theme}
            className={`h-1 flex-1 rounded-full transition-colors duration-500 ${
              i < step - 1 ? 'bg-ink' : i === step - 1 ? 'bg-action' : 'bg-rule'
            }`}
          >
            <span className="sr-only">
              {objective.theme}: {i < step - 1 ? 'done' : i === step - 1 ? 'current' : 'upcoming'}
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}
