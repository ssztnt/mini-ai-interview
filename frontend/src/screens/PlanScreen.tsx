import { useState } from 'react'
import type { Interview, Objective } from '../api/types'
import { Button, ErrorNote } from '../components/ui'

const MIN = 3
const MAX = 5

interface Props {
  interview: Interview
  busy: boolean
  error: string | null
  onStart: (objectives: Objective[]) => void
  onCancel: () => void
}

export function PlanScreen({ interview, busy, error, onStart, onCancel }: Props) {
  const [objectives, setObjectives] = useState<Objective[]>(interview.plan)

  const update = (index: number, patch: Partial<Objective>) =>
    setObjectives((list) => list.map((o, i) => (i === index ? { ...o, ...patch } : o)))
  const remove = (index: number) => setObjectives((list) => list.filter((_, i) => i !== index))
  const add = () => setObjectives((list) => [...list, { theme: '', goal: '' }])

  const valid = objectives.every((o) => o.theme.trim() && o.goal.trim())

  return (
    <div className="space-y-10">
      <div className="space-y-4">
        <p className="text-[15px] text-muted">Interview plan for “{interview.topic}”</p>
        <h1 className="font-serif text-3xl leading-tight tracking-tight sm:text-4xl">
          {interview.research_goal}
        </h1>
        <p className="max-w-xl text-[16px] leading-relaxed text-muted">
          You'll get one question for each objective below, in this order. Edit, remove or add
          objectives so the interview covers what matters to you.
        </p>
      </div>

      <ol className="space-y-3">
        {objectives.map((objective, index) => (
          <li
            key={index}
            className="group grid grid-cols-[2rem_1fr_auto] gap-x-3 rounded-lg border border-rule bg-surface p-4 focus-within:border-action"
          >
            <span className="pt-1.5 font-serif text-xl text-muted" aria-hidden>
              {index + 1}
            </span>
            <div className="space-y-1">
              <input
                value={objective.theme}
                onChange={(e) => update(index, { theme: e.target.value })}
                maxLength={80}
                aria-label={`Objective ${index + 1} theme`}
                placeholder="Theme"
                className="w-full rounded bg-transparent py-1 text-[17px] font-semibold focus:outline-none"
              />
              <textarea
                value={objective.goal}
                onChange={(e) => update(index, { goal: e.target.value })}
                maxLength={300}
                rows={2}
                aria-label={`Objective ${index + 1} goal`}
                placeholder="What should this question help us learn?"
                className="field-sizing-content w-full resize-none rounded bg-transparent text-[15px] leading-relaxed text-muted focus:text-ink focus:outline-none"
              />
            </div>
            <button
              type="button"
              onClick={() => remove(index)}
              disabled={objectives.length <= MIN}
              title={
                objectives.length <= MIN ? `A plan needs at least ${MIN} objectives` : 'Remove'
              }
              aria-label={`Remove objective ${index + 1}`}
              className="h-fit rounded-md px-2 py-1 text-[14px] text-muted opacity-60 transition group-hover:opacity-100 hover:bg-rule/50 hover:text-negative disabled:invisible"
            >
              Remove
            </button>
          </li>
        ))}
      </ol>

      {objectives.length < MAX && (
        <button
          type="button"
          onClick={add}
          className="w-full rounded-lg border border-dashed border-rule py-3 text-[15px] text-muted transition-colors hover:border-muted hover:text-ink"
        >
          Add an objective
        </button>
      )}

      {error && <ErrorNote message={error} />}

      <div className="flex flex-wrap items-center gap-3">
        <Button busy={busy} disabled={!valid} onClick={() => onStart(objectives)}>
          {busy
            ? 'Preparing the first question'
            : `Start the ${objectives.length}-question interview`}
        </Button>
        <Button variant="quiet" onClick={onCancel} disabled={busy}>
          Choose another topic
        </Button>
      </div>
    </div>
  )
}
