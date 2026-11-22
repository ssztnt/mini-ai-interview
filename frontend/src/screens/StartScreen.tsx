import { useState, type FormEvent } from 'react'
import { Button, ErrorNote } from '../components/ui'

const SUGGESTIONS = [
  'AI in the workplace',
  'Productivity tools',
  'Remote work',
  'Scientific research',
  'Learning a new skill',
]

interface Props {
  busy: boolean
  error: string | null
  onCreate: (topic: string, numQuestions: number) => void
}

export function StartScreen({ busy, error, onCreate }: Props) {
  const [topic, setTopic] = useState('')
  const [count, setCount] = useState(4)
  const trimmed = topic.trim()

  function submit(event: FormEvent) {
    event.preventDefault()
    if (trimmed.length >= 2) onCreate(trimmed, count)
  }

  return (
    <form onSubmit={submit} className="space-y-10">
      <div className="space-y-4">
        <h1 className="font-serif text-4xl leading-[1.1] tracking-tight sm:text-5xl">
          What would you like to be interviewed about?
        </h1>
        <p className="max-w-xl text-[17px] leading-relaxed text-muted">
          Pick a topic and the AI drafts a short interview plan for you to review. It then asks one
          question at a time, follows up on what you say, and ends with a summary of your answers.
        </p>
      </div>

      <div className="space-y-3">
        <label htmlFor="topic" className="block text-[15px] font-medium">
          Topic
        </label>
        <input
          id="topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          maxLength={120}
          autoFocus
          placeholder="e.g. how you use AI at work"
          className="w-full rounded-lg border border-rule bg-surface px-4 py-3.5 text-lg placeholder:text-muted/60 focus:border-action focus:outline-none"
        />
        <div className="flex flex-wrap gap-2" aria-label="Suggested topics">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setTopic(s)}
              className={`rounded-full border px-3 py-1 text-[14px] transition-colors ${
                topic === s
                  ? 'border-ink bg-ink text-paper'
                  : 'border-rule text-muted hover:border-muted hover:text-ink'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <fieldset className="space-y-3">
        <legend className="text-[15px] font-medium">Number of questions</legend>
        <div className="inline-flex rounded-lg border border-rule bg-surface p-1">
          {[3, 4, 5].map((n) => (
            <label
              key={n}
              className={`cursor-pointer rounded-md px-5 py-1.5 text-[15px] transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-action ${
                count === n ? 'bg-ink text-paper' : 'text-muted hover:text-ink'
              }`}
            >
              <input
                type="radio"
                name="count"
                value={n}
                checked={count === n}
                onChange={() => setCount(n)}
                className="sr-only"
              />
              {n}
            </label>
          ))}
        </div>
        <p className="text-[14px] text-muted">About a minute per question.</p>
      </fieldset>

      {error && <ErrorNote message={error} />}

      <Button type="submit" busy={busy} disabled={trimmed.length < 2}>
        {busy ? 'Drafting your plan' : 'Draft interview plan'}
      </Button>
    </form>
  )
}
