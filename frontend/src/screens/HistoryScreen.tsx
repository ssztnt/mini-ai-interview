import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { InterviewListItem } from '../api/types'
import { Button, Dots, ErrorNote, SentimentDot } from '../components/ui'
import { formatDate } from '../lib/format'

interface Props {
  onOpen: (id: string) => void
  onNew: () => void
}

export function HistoryScreen({ onOpen, onNew }: Props) {
  const [items, setItems] = useState<InterviewListItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchItems = () => api.listInterviews().then(setItems, (e: Error) => setError(e.message))
  const retry = () => {
    setError(null)
    void fetchItems()
  }
  useEffect(() => {
    void fetchItems()
  }, [])

  return (
    <div className="space-y-8">
      <h1 className="font-serif text-4xl tracking-tight">Past interviews</h1>

      {error && <ErrorNote message={error} onRetry={retry} />}
      {!items && !error && <Dots className="text-muted" />}

      {items?.length === 0 && (
        <div className="space-y-4">
          <p className="text-[16px] text-muted">
            Finished interviews appear here, along with their summaries.
          </p>
          <Button onClick={onNew}>Start your first interview</Button>
        </div>
      )}

      {items && items.length > 0 && (
        <ul className="divide-y divide-rule border-y border-rule">
          {items.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onOpen(item.id)}
                className="grid w-full gap-1 px-1 py-5 text-left transition-colors hover:bg-surface sm:grid-cols-[1fr_auto] sm:gap-6"
              >
                <span className="space-y-1">
                  <span className="block text-[17px] font-medium">{item.topic}</span>
                  {item.overview && (
                    <span className="line-clamp-2 block text-[15px] leading-relaxed text-muted">
                      {item.overview}
                    </span>
                  )}
                </span>
                <span className="flex gap-4 text-[14px] text-muted sm:flex-col sm:items-end sm:gap-1">
                  <span>{formatDate(item.completed_at)}</span>
                  {item.sentiment && <SentimentDot label={item.sentiment} />}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
